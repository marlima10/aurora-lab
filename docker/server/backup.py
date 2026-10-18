import datetime as dt
import hashlib
import json
import os
import pathlib
import sqlite3
import tarfile
import tempfile
import time

os.umask(0o077)

def status(value):
    path=pathlib.Path('/status/fitness-backup.json')
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value)); temp.chmod(0o644); temp.replace(path)

def backup():
    stamp=dt.datetime.now(dt.timezone.utc)
    name='auroralab-data-'+stamp.strftime('%Y%m%d-%H%M%S')+'.tar.gz'
    target=pathlib.Path('/backups')/name
    databases=[]
    json_files=[]
    with tempfile.TemporaryDirectory() as tmp:
        stage=pathlib.Path(tmp)
        for source in pathlib.Path('/source').rglob('*'):
            if not source.is_file() or source.suffix not in ('.db','.sqlite','.sqlite3'): continue
            with source.open('rb') as handle:
                if handle.read(16)!=b'SQLite format 3\x00': continue
            relative=source.relative_to('/source')
            dest=stage/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            src=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True,timeout=30)
            dst=sqlite3.connect(str(dest)); src.backup(dst)
            if dst.execute('pragma integrity_check').fetchall()!=[('ok',)]: raise RuntimeError('Banco invalido')
            src.close(); dst.close(); databases.append(str(relative))
        for source in pathlib.Path('/source/opengym').rglob('*.json'):
            if not source.is_file() or source.is_symlink(): continue
            value=source.read_bytes();json.loads(value)
            relative=source.relative_to('/source');dest=stage/relative
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(value);json_files.append(str(relative))
        required={'fitness/fitness.sqlite3'}
        history='octoprint/octoprint/data/printhistory/history.db'
        if (pathlib.Path('/source')/history).exists(): required.add(history)
        if not required.issubset(databases): raise RuntimeError('Banco esperado ausente')
        partial=target.with_suffix(target.suffix+'.partial')
        with tarfile.open(partial,'w:gz') as archive:
            for db in databases:archive.add(stage/db,arcname='sqlite-snapshots/'+db,recursive=False)
            for item in json_files:archive.add(stage/item,arcname=item,recursive=False)
            for source in pathlib.Path('/source').rglob('*'):
                if not source.is_file() or source.is_symlink(): continue
                relative=str(source.relative_to('/source'))
                if relative in json_files: continue
                if any(relative==db or relative in (db+'-wal',db+'-shm',db+'-journal') for db in databases): continue
                archive.add(source,arcname=relative,recursive=False)
        with tarfile.open(partial,'r:gz') as archive:
            for item in json_files:json.loads(archive.extractfile(item).read())
            for db in databases:
                member=archive.extractfile('sqlite-snapshots/'+db)
                restored=stage/('verify-'+pathlib.Path(db).name)
                with restored.open('wb') as out: out.write(member.read())
                check=sqlite3.connect(restored.as_uri()+'?mode=ro',uri=True)
                if check.execute('pragma integrity_check').fetchall()!=[('ok',)]: raise RuntimeError('Banco arquivado invalido')
                check.close()
        partial.replace(target)
        digest=hashlib.file_digest(target.open('rb'),'sha256').hexdigest()
        target.with_suffix(target.suffix+'.sha256').write_text(digest+'  '+name+'\n')
        status({'time':stamp.isoformat(),'status':'ok','verified':True,'file':name,'sha256':digest,'scope':'Fitness, OctoPrint, Prints, Samba, Tailscale, CasaOS, Home Assistant, openGym, Garmin e codigo/configuracoes; copia local no mesmo SSD'})
    print('Backup verificado:',name,flush=True)

while True:
    try: backup()
    except Exception as exc:
        status({'time':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'error','verified':False,'message':type(exc).__name__})
        print('Falha no backup:',type(exc).__name__,flush=True)
    time.sleep(int(os.environ.get('BACKUP_INTERVAL','86400')))
