"""Private Garmin bridge authenticated by the existing openGym session."""
import datetime as dt
import hashlib
import json
import logging
import os
from pathlib import Path
import queue
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from mapping import convert, merge_records, enrich_calories
from personal_api import PersonalAPI, PersonalAPIError, valid_secret
from auto_sync import AutoSync, SyncError
os.umask(0o077)
logging.disable(logging.CRITICAL)
ROOT=Path(os.environ.get('DATA_DIR','/data'))
ORIGIN=os.environ['PUBLIC_ORIGIN'].rstrip('/')
API=os.environ.get('OPENGYM_API','http://opengym-api:3000')
STATIC=Path(__file__).parent/'static'
GUARD=threading.Lock();USERS={}
class Problem(Exception):
    def __init__(self,code,message): self.code=code;self.message=message

def request_json(path,headers,body=None,method=None):
    h=dict(headers)
    if body is not None: h.update({'Content-Type':'application/json','Origin':ORIGIN})
    req=urllib.request.Request(API+path,data=json.dumps(body).encode() if body is not None else None,
        headers=h,method=method or ('PUT' if body is not None else 'GET'))
    try:
        with urllib.request.urlopen(req,timeout=30) as response: return response.status,json.load(response)
    except urllib.error.HTTPError as e:
        if e.code==409: return 409,{}
        raise Problem(401 if e.code in (401,403) else 502,'Entre novamente no openGym.' if e.code in (401,403) else 'O openGym não respondeu. Nenhum novo envio será tentado automaticamente.')

def session(headers):
    forwarded={k:headers[k] for k in ('Cookie','Authorization') if headers.get(k)}
    if not forwarded: raise Problem(401,'Entre no openGym neste navegador e volte a esta página.')
    _,result=request_json('/api/me',forwarded)
    user=result.get('user') or {}
    if not user.get('id'): raise Problem(401,'Entre no openGym primeiro.')
    return str(user['id']),forwarded

class User:
    def __init__(self,uid):
        self.uid=uid
        self.path=ROOT/hashlib.sha256(uid.encode()).hexdigest()
        self.path.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.lock=threading.Lock();self.status='idle';self.error='';self.busy=False
        self.mfa=queue.Queue(maxsize=1);self.preview=[];self.expires=0;self.truncated=False;self.invalid=0
    def ledger(self):
        p=self.path/'imported.json'
        return json.loads(p.read_text()) if p.exists() else []
    def save(self,name,data):
        tmp=self.path/(name+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False));tmp.replace(self.path/name)
    def view(self):
        with self.lock:
            if self.expires<time.time(): self.preview=[]
            done=set(self.ledger())
            return {'status':self.status,'busy':self.busy,'error':self.error,
                'connected':(self.path/'personal-api.json').exists() or (self.path/'tokens'/'garmin_tokens.json').exists(),
                'provider':'personal' if (self.path/'personal-api.json').exists() else 'community' if (self.path/'tokens'/'garmin_tokens.json').exists() else None,
                'activities':[{k:v for k,v in r.items() if k not in ('workout','exercise')}|{'imported':r['activity_id'] in done} for r in self.preview],
                'truncated':self.truncated,'invalid':self.invalid,'auto':AUTO.view(self)}

def user_for(uid):
    with GUARD:
        if uid not in USERS: USERS[uid]=User(uid)
        return USERS[uid]

def error_message(e):
    if isinstance(e,PersonalAPIError): return str(e)
    if isinstance(e,(Problem,SyncError,ValueError)): return e.message if isinstance(e,(Problem,SyncError)) else str(e)
    name=type(e).__name__
    if 'TooManyRequests' in name: return 'A Garmin limitou as solicitações. Aguarde antes de tentar novamente.'
    if 'Authentication' in name: return 'A Garmin recusou o acesso. Confira o login e o código de verificação.'
    return 'Não foi possível concluir a operação. A conexão Garmin pode estar indisponível; seus treinos existentes foram preservados.'

def background(u,fn):
    with u.lock:
        if u.busy: raise Problem(409,'Aguarde a operação atual.')
        u.busy=True;u.status='working';u.error=''
    def work():
        try: fn()
        except Exception as e:
            with u.lock: u.status='error';u.error=error_message(e)
        finally:
            with u.lock:
                u.busy=False
                if u.status=='working': u.status='ready'
    threading.Thread(target=work,daemon=True).start()

def login(u,email,password):
    from garminconnect import Garmin
    while not u.mfa.empty():
        try: u.mfa.get_nowait()
        except queue.Empty: break
    def prompt():
        with u.lock: u.status='mfa'
        try: code=u.mfa.get(timeout=180)
        except queue.Empty: raise ValueError('O prazo do código expirou. Tente conectar novamente.')
        with u.lock: u.status='working'
        return code
    client=Garmin(email=email,password=password,prompt_mfa=prompt)
    try:
        tokenpath=u.path/'tokens';tokenpath.mkdir(mode=0o700,exist_ok=True)
        client.login()
        client.client.dump(str(tokenpath))
        with u.lock: u.preview=[];u.expires=0
    finally:
        client.password=None
        password=None

def connect_personal(u,api_key):
    try:
        client=PersonalAPI(api_key)
        # Validate both authentication and read access before replacing any credential.
        client.activities(0,1)
    except PersonalAPIError as error:
        with u.lock:
            u.save('personal-api-status.json',{'time':dt.datetime.now(dt.timezone.utc).isoformat(),
                'ok':False,'http_status':error.http_status,'phase':error.phase})
        raise
    with u.lock:
        u.save('personal-api.json',{'api_key':api_key})
        (u.path/'personal-api.json').chmod(0o600)
        u.save('personal-api-status.json',{'time':dt.datetime.now(dt.timezone.utc).isoformat(),'ok':True})
        u.preview=[];u.expires=0


def load(u,first,last):
    with u.lock: u.preview=[];u.expires=0;u.invalid=0;u.truncated=False
    personal=u.path/'personal-api.json'
    if personal.exists():
        client=PersonalAPI(json.loads(personal.read_text())['api_key'])
        page_size=25
        get_page=lambda offset: client.activities(offset,page_size,first,last)
    else:
        from garminconnect import Garmin
        client=Garmin();client.login(str(u.path/'tokens'))
        page_size=100
        get_page=lambda offset: client.get_activities(offset,page_size)
    rows=[];invalid=0;truncated=False
    for offset in range(0,1000,page_size):
        page=get_page(offset)
        if not isinstance(page,list): raise ValueError('Resposta de atividades não reconhecida.')
        days=[]
        for raw in page:
            day=str(raw.get('startTimeLocal',''))[:10];days.append(day)
            if first<=day<=last:
                try: rows.append(convert(raw))
                except (ValueError,TypeError): invalid+=1
        if len(page)<page_size or (days and min(days)<first): break
    else: truncated=True
    unique={r['activity_id']:r for r in rows}
    with u.lock:
        u.preview=list(unique.values());u.expires=time.time()+1800;u.truncated=truncated;u.invalid=invalid

def import_selected(u,ids,headers):
    with u.lock:
        if u.busy: raise Problem(409,'Aguarde a operação atual.')
        if u.expires<time.time(): raise Problem(400,'Carregue as atividades novamente.')
        if not isinstance(ids,list) or not ids or len(ids)>1000 or any(not isinstance(i,str) for i in ids):
            raise Problem(400,'Selecione as atividades para importar.')
        selected=set(ids);records=[r for r in u.preview if r['activity_id'] in selected]
        if len(records)!=len(selected): raise Problem(400,'Seleção inválida.')
        u.busy=True
    try:
        return write_records(u,records,headers)
    finally:
        with u.lock: u.busy=False

def write_records(u,records,headers):
    ledger=u.ledger()
    for attempt in range(3):
        _,current=request_json('/api/data',headers)
        state=current.get('state')
        merged,added,skipped=merge_records(state,records,ledger)
        if not added:
            if skipped:u.save('imported.json',sorted(set(ledger)|set(skipped)))
            return {'added':0,'skipped':len(skipped)}
        u.save('before-import.json',current)
        code,_=request_json('/api/data',headers,{'state':merged,'baseRev':current['rev'],'baseWid':state.get('_wid','')})
        if code==409: continue
        u.save('imported.json',sorted(set(ledger)|set(added)|set(skipped)))
        return {'added':len(added),'skipped':len(skipped)}
    raise Problem(409,'O perfil mudou durante a importação. Recarregue e tente novamente.')

def backfill_calories(u,records,headers):
    for attempt in range(3):
        _,current=request_json('/api/data',headers)
        merged,count=enrich_calories(current['state'],records)
        if not count: return {'updated':0}
        u.save('before-calories.json',current)
        code,_=request_json('/api/data',headers,{'state':merged,'baseRev':current['rev'],'baseWid':current['state'].get('_wid','')})
        if code==409: continue
        return {'updated':count}
    raise Problem(409,'O perfil mudou. Recarregue antes de atualizar as calorias.')


AUTO=AutoSync(ROOT,user_for,request_json,write_records,error_message)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def log_error(self,*args): pass
    def send(self,status,body,ctype='application/json; charset=utf-8'):
        data=body if isinstance(body,bytes) else json.dumps(body,ensure_ascii=False).encode()
        self.send_response(status)
        for k,v in {'Content-Type':ctype,'Content-Length':str(len(data)),'Cache-Control':'no-store',
            'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}.items(): self.send_header(k,v)
        self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/health': return self.send(200,{'ok':True})
        assets={'/garmin/':('index.html','text/html; charset=utf-8'),'/garmin/app.js':('app.js','application/javascript'),'/garmin/style.css':('style.css','text/css')}
        if path in assets:
            filename,ctype=assets[path];return self.send(200,(STATIC/filename).read_bytes(),ctype)
        try:
            uid,_=session(self.headers)
            if path!='/garmin/status': raise Problem(404,'Página não encontrada.')
            self.send(200,user_for(uid).view())
        except Exception as e: self.send(e.code if isinstance(e,(Problem,SyncError)) else 502,{'error':error_message(e)})
    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=65536: raise Problem(413,'Solicitação inválida.')
            raw=self.rfile.read(length)
            if self.headers.get('Origin')!=ORIGIN: raise Problem(403,'Origem da solicitação recusada.')
            uid,headers=session(self.headers);u=user_for(uid)
            body=json.loads(raw)
            if not isinstance(body,dict): raise Problem(400,'Solicitação inválida.')
            path=urlsplit(self.path).path
            if path=='/garmin/personal':
                api_key=body.get('apiKey')
                if not valid_secret(api_key): raise Problem(400,'Informe sua chave pessoal Garmin, sem espacos ou quebras de linha.')
                background(u,lambda:connect_personal(u,api_key));return self.send(202,{'ok':True})
            if path=='/garmin/login':
                email=body.get('email');password=body.get('password')
                if not isinstance(email,str) or '@' not in email or len(email)>254 or not isinstance(password,str) or not 1<=len(password)<=1024:
                    raise Problem(400,'Informe seu e-mail e senha Garmin.')
                background(u,lambda:login(u,email,password));return self.send(202,{'ok':True})
            if path=='/garmin/mfa':
                code=body.get('code','')
                if not isinstance(code,str) or not code.isdigit() or not 4<=len(code)<=10: raise Problem(400,'Código inválido.')
                with u.lock:
                    if u.status!='mfa': raise Problem(409,'Não há código pendente.')
                    try: u.mfa.put_nowait(code)
                    except queue.Full: raise Problem(409,'Código já enviado.')
                    u.status='working'
                return self.send(202,{'ok':True})
            if path=='/garmin/load':
                first=dt.date.fromisoformat(body.get('first',''));last=dt.date.fromisoformat(body.get('last',''))
                if first>last or (last-first).days>366: raise Problem(400,'Escolha um período de até um ano.')
                background(u,lambda:load(u,first.isoformat(),last.isoformat()));return self.send(202,{'ok':True})
            if path=='/garmin/auto':
                enabled=body.get('enabled')
                if not isinstance(enabled,bool):raise Problem(400,'Escolha ativar ou pausar.')
                view=AUTO.enable(u,headers) if enabled else AUTO.disable(u)
                if enabled:threading.Thread(target=AUTO.run,args=(u,),daemon=True).start()
                return self.send(200,{'ok':True,'auto':view})
            if path=='/garmin/sync':
                AUTO.schedule_now(u)
                threading.Thread(target=AUTO.run,args=(u,),daemon=True).start()
                return self.send(202,{'ok':True})
            if path=='/garmin/import': return self.send(200,import_selected(u,body.get('ids'),headers))
            if path=='/garmin/disconnect':
                with u.lock:
                    if u.busy: raise Problem(409,'Aguarde a operação atual.')
                    token=u.path/'tokens'/'garmin_tokens.json'
                    u.save('auto-sync.json',AUTO.config(u)|{'enabled':False,'next_run':None});(u.path/'auto-auth.json').unlink(missing_ok=True)
                    token.unlink(missing_ok=True);(u.path/'personal-api.json').unlink(missing_ok=True);u.preview=[];u.expires=0;u.status='idle';u.error=''
                return self.send(200,{'ok':True})
            raise Problem(404,'Página não encontrada.')
        except Exception as e:
            self.send(e.code if isinstance(e,(Problem,SyncError)) else 400 if isinstance(e,(ValueError,TypeError)) else 502,{'error':error_message(e)})

if __name__=='__main__':
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    AUTO.start()
    ThreadingHTTPServer(('0.0.0.0',8080),Handler).serve_forever()