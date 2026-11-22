"""Remove retired print app data from mixed archives; verify every retained member."""
import argparse,base64,copy,hashlib,io,json,os,re,sqlite3,stat,tarfile,tempfile,zipfile
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path,PurePosixPath

ARCHIVE_ENDINGS=('.tar.gz','.tgz','.tar','.zip')
RETIRED_FILES={'octoprint-api.key','octoprint.env','octoprint_aurora.py','octoprint_check.py','compose.printer.yaml','octoprint.svg'}

def dropped(name):
    parts=PurePosixPath(name.replace('\\','/').lstrip('/')).parts
    lower=tuple(p.lower() for p in parts)
    if any(p in ('octoprint','.octoprint') for p in lower):return True
    if lower and lower[-1] in RETIRED_FILES:return True
    base=lower[-1] if lower else ''
    if 'octoprint' in base and base.endswith(('.key','.pem','.env','.yaml','.yml','.json','.ini','.cfg','.conf','.service','.save','.bak','.py','.sh','.ps1')):return True
    if any(p in ('ustreamer','mjpg-streamer','mjpg_streamer','octoprint_venv','octoprint-venv') for p in lower):return True
    if base.startswith(('ustreamer.','mjpg-streamer.','mjpg_streamer.','webcamd.')):return True
    if ('systemd' in lower or 'init.d' in lower) and any(k in base for k in ('camera','webcam','ustream','mjpg')):return True
    if 'printserver' in base and 'camera' in base and base.endswith(('.key','.conf','.json','.service','.save')):return True
    return any(lower[i:i+3]==('docker','server','camera') for i in range(len(lower)-2)) or any(lower[i:i+2]==('data','camera') for i in range(len(lower)-1))

def strip_services(text):
    out=[];skip=False
    for line in text.splitlines(True):
        if re.match(r'^  (octoprint|camera):\s*$',line):skip=True;continue
        if skip and re.match(r'^(?:  \S|\S)',line):skip=False
        if not skip and not any(s in line for s in ('./data/octoprint:','octoprint-api.key:','OCTOPRINT_API_ORIGIN:','127.0.0.1:5000:5000')):out.append(line)
    return ''.join(out)

def clean_registry(value):
    if isinstance(value,dict):return {k:clean_registry(v) for k,v in value.items() if k.lower()!='octoprint'}
    if isinstance(value,list):return [clean_registry(v) for v in value]
    return value

def clean_serving(value):
    if not isinstance(value,dict):return value
    result=copy.deepcopy(value)
    if isinstance(result.get('TCP'),dict):result['TCP'].pop('5000',None)
    for key in ('Web','AllowFunnel'):
        if isinstance(result.get(key),dict):result[key]={k:v for k,v in result[key].items() if not k.endswith(':5000')}
    return result

def sqlite_without_grants(raw):
    with tempfile.TemporaryDirectory(prefix='aurora-retired-db-') as tmp:
        path=Path(tmp)/'auth.sqlite3';path.write_bytes(raw);path.chmod(0o600)
        with closing(sqlite3.connect(path)) as db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'users','grants'}.issubset(tables):return raw
            if not db.execute("SELECT COUNT(*) FROM grants WHERE app='octoprint'").fetchone()[0]:return raw
            db.execute("DELETE FROM grants WHERE app='octoprint'");db.commit();db.execute('VACUUM')
            if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('Sanitized auth database failed integrity check')
        return path.read_bytes()

def transform(name,raw,depth):
    lower=name.lower().replace('\\','/');base=PurePosixPath(lower).name
    if base=='tailscaled.state':
        value=json.loads(raw);clean=copy.deepcopy(value)
        for key,encoded in value.items():
            if not key.startswith('_serve/') or not isinstance(encoded,str):continue
            decoded=json.loads(base64.b64decode(encoded));filtered=clean_serving(decoded)
            if filtered!=decoded:clean[key]=base64.b64encode(json.dumps(filtered,separators=(',',':')).encode()).decode()
        if clean!=value:return (json.dumps(clean,indent=2)+'\n').encode()
    if lower.endswith(ARCHIVE_ENDINGS) and (raw.startswith((b'\x1f\x8b',b'PK')) or raw[257:262]==b'ustar'):
        if depth>=4:raise ValueError('Nested archive depth exceeded')
        with tempfile.TemporaryDirectory(prefix='aurora-retired-nested-') as tmp:
            original=Path(tmp)/base;original.write_bytes(raw);output=Path(tmp)/('clean-'+base)
            changes=rewrite_archive(original,output,depth+1)
            if changes['removed'] or changes['modified']:return output.read_bytes()
    if raw.startswith(b'SQLite format 3\0') and ('auth' in PurePosixPath(lower).parts or base in ('auth.sqlite3','auth.db')):
        return sqlite_without_grants(raw)
    if base.endswith('.json') and (any(k in PurePosixPath(lower).parts for k in ('secrets','sso','printserver')) or any(k in base for k in ('credential','secret','acesso','mapping','sso'))):
        try:
            value=json.loads(raw);clean=clean_registry(value)
            if value!=clean:return (json.dumps(clean,ensure_ascii=False,indent=2)+'\n').encode()
        except (ValueError,UnicodeError):pass
    if base.startswith('compose.') and base.endswith(('.yaml','.yml')):
        text=raw.decode('utf-8');clean=strip_services(text)
        if clean!=text:return clean.encode()
    if base in ('.env','.env.example'):
        text=raw.decode('utf-8');lines=[]
        for line in text.splitlines(True):
            if line.startswith(('CAMERA_DEVICE=','PRINTER_DEVICE=','OCTOPRINT_')):continue
            if line.startswith('COMPOSE_PROFILES='):line=re.sub(r'\bcamera\b,?', '',line)
            if line.startswith('COMPOSE_FILE='):line=line.replace(':compose.printer.yaml','').replace('compose.printer.yaml:', '')
            lines.append(line)
        clean=''.join(lines)
        if clean!=text:return clean.encode()
    return raw

def digest(raw):return hashlib.sha256(raw).hexdigest()

def file_digest(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()

def may_transform(name):
    lower=name.lower().replace('\\','/');parts=PurePosixPath(lower).parts;base=parts[-1] if parts else ''
    return (lower.endswith(ARCHIVE_ENDINGS) or 'auth' in parts or base in ('auth.sqlite3','auth.db','.env','.env.example','tailscaled.state')
        or (base.startswith('compose.') and base.endswith(('.yaml','.yml')))
        or (base.endswith('.json') and (any(k in parts for k in ('secrets','sso','printserver')) or any(k in base for k in ('credential','secret','acesso','mapping','sso')))))

def needs_sanitize(source):
    if source.name.endswith('.zip'):
        with zipfile.ZipFile(source) as archive:
            for member in archive.infolist():
                if dropped(member.filename):return True
                if may_transform(member.filename) and not member.is_dir():
                    raw=archive.read(member)
                    if transform(member.filename,raw,0)!=raw:return True
    else:
        with tarfile.open(source,'r:*') as archive:
            for member in archive:
                if dropped(member.name) or ((member.issym() or member.islnk()) and dropped(member.linkname)):return True
                if member.isfile() and may_transform(member.name):
                    raw=archive.extractfile(member).read()
                    if transform(member.name,raw,0)!=raw:return True
    return False

def rewrite_archive(source,output,depth=0):
    expected=[];removed=modified=0
    if source.name.endswith('.zip'):
        with zipfile.ZipFile(source) as old,zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as new:
            for item in old.infolist():
                if dropped(item.filename):removed+=1;continue
                raw=old.read(item);clean=transform(item.filename,raw,depth) if not item.is_dir() else raw
                modified+=int(clean!=raw);new.writestr(item,clean);expected.append((item.filename,digest(clean)))
        with zipfile.ZipFile(output) as check:
            actual=[(m.filename,digest(check.read(m))) for m in check.infolist()]
    else:
        mode='w:gz' if source.name.endswith(('.gz','.tgz')) else 'w'
        options={'compresslevel':1} if mode=='w:gz' else {}
        with tarfile.open(source,'r:*') as old,tarfile.open(output,mode,**options) as new:
            for item in old:
                if dropped(item.name):removed+=1;continue
                if item.isfile():
                    raw=old.extractfile(item).read();clean=transform(item.name,raw,depth);modified+=int(clean!=raw)
                    adjusted=copy.copy(item);adjusted.size=len(clean);new.addfile(adjusted,io.BytesIO(clean));expected.append((item.name,digest(clean)))
                else:
                    if item.issym() or item.islnk():
                        if dropped(item.linkname):removed+=1;continue
                    new.addfile(item);expected.append((item.name,None))
        with tarfile.open(output,'r:*') as check:
            actual=[(m.name,digest(check.extractfile(m).read()) if m.isfile() else None) for m in check]
    if actual!=expected:raise ValueError('Retained archive member verification failed')
    return {'removed':removed,'modified':modified,'retained':len(expected)}

def sanitize(source):
    if source.is_symlink():raise ValueError('Refusing archive symlink')
    oldstat=source.stat();oldsha=file_digest(source)
    output=source.with_name(source.name+'.print39.partial')
    try:
        result=rewrite_archive(source,output)
        result.update(path=str(source),old_sha256=oldsha)
        if not result['removed'] and not result['modified']:
            output.unlink();result.update(status='unchanged',sha256=oldsha);return result
        newsha=file_digest(output)
        os.chmod(output,stat.S_IMODE(oldstat.st_mode))
        if hasattr(os,'chown'):os.chown(output,oldstat.st_uid,oldstat.st_gid)
        os.replace(output,source)
        sidecar=source.with_suffix(source.suffix+'.sha256')
        if sidecar.exists():sidecar.write_text(newsha+'  '+source.name+'\n')
        result.update(status='sanitized',sha256=newsha)
        return result
    finally:
        if output.exists():output.unlink()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--report',required=True);parser.add_argument('--audit',action='store_true');args=parser.parse_args()
    root=Path(args.root).resolve();report=Path(args.report).resolve()
    if str(root).lower().replace('\\','/') not in ('d:/auroraserver','/srv/auroralab'):raise ValueError('Unexpected backup root')
    previous=json.loads(report.read_text()) if report.exists() else {'results':[]}
    done={r['path']:r for r in previous['results'] if r.get('status') in ('unchanged','sanitized')}
    files=sorted(p for p in root.rglob('*') if p.is_file() and not p.is_symlink() and p.name.endswith(ARCHIVE_ENDINGS) and not any(part in ('.git','node_modules','sources','aurora-lab') for part in p.relative_to(root).parts))
    pending=[]
    for source in files:
        resolved=source.resolve();assert resolved.is_relative_to(root)
        if not args.audit and str(source) in done and file_digest(source)==done[str(source)].get('sha256'):continue
        pending.append(source)
    def process(source):
        if args.audit and not needs_sanitize(source):return {'path':str(source),'status':'unchanged','sha256':file_digest(source),'audited':True,'removed':0,'modified':0}
        result=sanitize(source)
        if args.audit:result['audited']=True
        return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        work={pool.submit(process,p):p for p in pending}
        for future in as_completed(work):
            source=work[future]
            try:result=future.result()
            except Exception as exc:result={'path':str(source),'status':'error','error':type(exc).__name__}
            previous['results'].append(result);report.parent.mkdir(parents=True,exist_ok=True);temporary=report.with_suffix('.tmp');temporary.write_text(json.dumps(previous,indent=2));os.replace(temporary,report)
            print(json.dumps({'path':str(source.relative_to(root)),'status':result['status'],'removed':result.get('removed',0),'modified':result.get('modified',0)}),flush=True)
    latest={r['path']:r for r in previous['results']}
    errors=[r for r in latest.values() if r.get('status')=='error']
    print(json.dumps({'completed':len(latest),'errors':len(errors)}),flush=True)
    raise SystemExit(1 if errors else 0)

if __name__=='__main__':main()
