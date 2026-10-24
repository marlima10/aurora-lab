"""Restore a backup into a disposable directory; never starts production services."""
from contextlib import closing
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tarfile
import tempfile

MAX_BYTES = 20 * 2**30

def check_archive(source, expected_sha256, probe=None):
    source=Path(source)
    with source.open('rb') as handle: digest=hashlib.file_digest(handle,'sha256').hexdigest()
    if digest != expected_sha256: raise ValueError('SHA-256 divergente')
    count=databases=jsons=profiles=total=0
    # Private temporary data is removed even on a failed validation/probe.
    with tempfile.TemporaryDirectory(prefix='aurora-restore-') as directory:
        root=Path(directory);root.chmod(0o700)
        with tarfile.open(source,'r:gz') as archive:
            members=archive.getmembers();seen=set()
            for member in members:
                name=member.name
                path=PurePosixPath(name)
                if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name or not (member.isfile() or member.isdir()): raise ValueError('Caminho ou tipo inseguro no backup')
                normalized=PurePosixPath(*path.parts[1:]) if path.parts and path.parts[0]=='sqlite-snapshots' else path
                key=str(normalized)
                if key in seen: raise ValueError('Caminho duplicado no backup')
                seen.add(key);total+=member.size
                if total > MAX_BYTES or member.size < 0: raise ValueError('Backup excede o limite de restauracao')
            if shutil.disk_usage(root).free < total + 128*2**20: raise ValueError('Espaco insuficiente para restaurar')
            for member in members:
                if not member.isfile(): continue
                path=PurePosixPath(member.name)
                normalized=PurePosixPath(*path.parts[1:]) if path.parts[0]=='sqlite-snapshots' else path
                dest=root.joinpath(*normalized.parts);dest.parent.mkdir(parents=True,exist_ok=True)
                with archive.extractfile(member) as src, dest.open('wb') as out:
                    os.chmod(dest,0o600);h=hashlib.sha256()
                    while chunk:=src.read(1024*1024): out.write(chunk);h.update(chunk)
                with dest.open('rb') as handle:
                    if hashlib.file_digest(handle,'sha256').hexdigest()!=h.hexdigest(): raise ValueError('Arquivo restaurado divergente')
                count+=1
                with dest.open('rb') as handle: signature=handle.read(16)
                if signature==b'SQLite format 3\x00':
                    with closing(sqlite3.connect(dest.as_uri()+'?mode=ro',uri=True)) as db:
                        if db.execute('pragma integrity_check').fetchall()!=[('ok',)]: raise ValueError('SQLite restaurado invalido')
                    databases+=1
                if dest.suffix=='.json':
                    json.loads(dest.read_bytes());jsons+=1
                    if normalized.parts[0]=='opengym': profiles+=1
            if not (root/'fitness/fitness.sqlite3').is_file() or databases < 1 or profiles < 1: raise ValueError('Dados essenciais ausentes no backup')
            apps = {}
            for app in ('manyfold','mealie','actual','auth'):
                if (root/'config'/('compose.'+app+'.yaml')).exists():
                    candidates=list((root/app).rglob('*'))
                    db_count=0
                    for file in candidates:
                        if file.is_file():
                            with file.open('rb') as handle:
                                if handle.read(16)==b'SQLite format 3\x00': db_count+=1
                    if db_count==0: raise ValueError('Banco adicional ausente na restauracao')
                    apps[app]={'sqlite_verified':db_count}
            probe_result=probe(root) if probe else None
        return {'time':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'ok','archive':source.name,'sha256':digest,'files_verified':count,'bytes_restored':total,'sqlite_verified':databases,'json_verified':jsons,'opengym_json_verified':profiles,'isolated':True,'production_modified':False,'apps_verified':apps,'application_probe':probe_result,'scope':'Restauracao descartavel dos arquivos, SQLite e JSON; nao testa hardware, VPN ou todos os servicos.'}

def save_report(path, report):
    path=Path(path);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(report,ensure_ascii=False),encoding='utf-8');tmp.chmod(0o644);tmp.replace(path)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('sha256');parser.add_argument('--report',required=True);args=parser.parse_args()
    os.umask(0o077)
    try: report=check_archive(args.archive,args.sha256)
    except Exception as exc: report={'time':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'error','message':type(exc).__name__,'isolated':True,'production_modified':False}
    save_report(args.report,report)
    print(json.dumps(report,ensure_ascii=False))
    raise SystemExit(0 if report['status']=='ok' else 1)
