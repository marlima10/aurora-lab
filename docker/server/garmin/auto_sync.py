"""Hourly recent-activities sync using a native, renewable openGym paired session."""
import datetime as dt
import hashlib
import json
import threading
import time
from pathlib import Path
from personal_api import PersonalAPI, PersonalAPIError, valid_secret
from mapping import convert

INTERVAL = 3600
ACTIVITY_LIMIT = 5

class SyncError(Exception):
    def __init__(self,code,message):self.code=code;self.message=message

class AutoSync:
    def __init__(self,root,get_user,fetch,write,error_text,client_factory=PersonalAPI,clock=time.time):
        self.root=Path(root);self.get_user=get_user;self.fetch=fetch;self.write=write
        self.error_text=error_text;self.client_factory=client_factory;self.clock=clock

    def read(self,u,name):
        try:
            value=json.loads((u.path/name).read_text())
            return value if isinstance(value,dict) else {}
        except (OSError,ValueError):return {}

    def config(self,u):return self.read(u,'auto-sync.json')

    def view(self,u):
        c=self.config(u)
        return {k:c.get(k) for k in ('last_run','last_status','last_error','last_added','last_skipped','latest_date','next_run')}|{'enabled':c.get('enabled') is True,'interval_seconds':INTERVAL,'activity_limit':ACTIVITY_LIMIT}

    def enable(self,u,headers):
        with u.lock:
            if u.busy:raise SyncError(409,'Aguarde a operacao atual.')
            if not (u.path/'personal-api.json').exists():raise SyncError(400,'Configure a chave oficial Garmin primeiro.')
            u.busy=True
        try:
            _,created=self.fetch('/api/pair/create',headers,{},method='POST')
            code=created.get('code')
            if not isinstance(code,str) or not code:raise SyncError(502,'O openGym nao criou a autorizacao automatica.')
            _,paired=self.fetch('/api/pair/redeem',{}, {'code':code},method='POST')
            if str((paired.get('user') or {}).get('id',''))!=u.uid or not valid_secret(paired.get('token')):
                raise SyncError(502,'A autorizacao nao pertence a este perfil. Nenhum treino foi alterado.')
            with u.lock:
                u.save('auto-auth.json',{'token':paired['token']})
                (u.path/'auto-auth.json').chmod(0o600)
                u.save('auto-sync.json',self.config(u)|{'uid':u.uid,'enabled':True,'interval_seconds':INTERVAL,'next_run':self.clock(),'last_error':''})
        finally:
            with u.lock:u.busy=False
        return self.view(u)

    def disable(self,u):
        with u.lock:
            if u.busy:raise SyncError(409,'Aguarde a operacao atual.')
            u.save('auto-sync.json',self.config(u)|{'enabled':False,'next_run':None})
            (u.path/'auto-auth.json').unlink(missing_ok=True)
        return self.view(u)

    def schedule_now(self,u):
        with u.lock:
            c=self.config(u)
            if not c.get('enabled'):raise SyncError(409,'Ative a atualizacao automatica primeiro.')
            if u.busy:raise SyncError(409,'Aguarde a operacao atual.')
            u.save('auto-sync.json',c|{'next_run':self.clock()})

    def run(self,u):
        with u.lock:
            c=self.config(u)
            if u.busy or c.get('enabled') is not True or (c.get('next_run') or 0)>self.clock():return None
            if c.get('uid')!=u.uid:raise SyncError(403,'Configuracao de perfil invalida.')
            u.busy=True
        started=self.clock();result=None
        try:
            token=self.read(u,'auto-auth.json').get('token')
            if not valid_secret(token):raise SyncError(401,'Reative a atualizacao para autorizar o openGym.')
            headers={'Authorization':'Bearer '+token}
            _,me=self.fetch('/api/me',headers)
            if str((me.get('user') or {}).get('id',''))!=u.uid:raise SyncError(401,'Reative a atualizacao no perfil correto.')
            renewed=me.get('token')
            if renewed:
                if not valid_secret(renewed):raise SyncError(502,'Resposta de renovacao openGym invalida.')
                u.save('auto-auth.json',{'token':renewed});headers={'Authorization':'Bearer '+renewed}
            key=self.read(u,'personal-api.json').get('api_key')
            rows=self.client_factory(key).activities(0,ACTIVITY_LIMIT)
            if not isinstance(rows,list) or len(rows)>ACTIVITY_LIMIT:raise SyncError(502,'A Garmin devolveu uma pagina inesperada.')
            records=sorted((convert(row) for row in rows),key=lambda r:(r['workout']['start'],r['activity_id']))
            result=self.write(u,records,headers) if records else {'added':0,'skipped':0}
            c.update(last_status='ok',last_error='',last_added=result['added'],last_skipped=result['skipped'],latest_date=records[-1]['date'] if records else None,activity_limit=ACTIVITY_LIMIT)
        except Exception as error:
            c.update(last_status='error',last_error=self.error_text(error),last_added=0,last_skipped=0)
            if getattr(error,'code',None)==401 or (isinstance(error,PersonalAPIError) and error.http_status in (401,403)):
                c['enabled']=False
                (u.path/'auto-auth.json').unlink(missing_ok=True)
        finally:
            c.update(last_run=dt.datetime.fromtimestamp(started,dt.timezone.utc).isoformat(),next_run=self.clock()+INTERVAL if c.get('enabled') else None)
            with u.lock:
                try:u.save('auto-sync.json',c)
                finally:u.busy=False
        return result

    def tick(self):
        for path in self.root.glob('*/auto-sync.json'):
            try:
                c=json.loads(path.read_text());uid=c.get('uid')
                if not isinstance(uid,str) or hashlib.sha256(uid.encode()).hexdigest()!=path.parent.name:continue
                if c.get('enabled') is True and (c.get('next_run') or 0)<=self.clock():self.run(self.get_user(uid))
            except (OSError,ValueError,TypeError):continue

    def start(self):
        def loop():
            while True:
                try:self.tick()
                except Exception:pass
                time.sleep(15)
        threading.Thread(target=loop,daemon=True).start()
