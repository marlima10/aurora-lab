"""Private dashboard data. Fixed upstreams, per-user storage, no browser credentials."""
from contextlib import contextmanager
import datetime as dt
import settings
import agenda
import re
import holidays
from gallery import Gallery,MAX_BYTES
import hmac
import json
import math
import os
import secrets
import sqlite3
import threading
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def fetch(url,headers=None):
    req=urllib.request.Request(url,headers={'User-Agent':'AuroraLAB/40'}|(headers or {}))
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=12) as r:
        raw=r.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError('Resposta muito grande.')
        return raw

class Data:
    def __init__(self,path):
        self.path=path;self.cache={};self.lock=threading.Lock();self.gallery=Gallery(Path(path).parent/"backgrounds")
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,owner TEXT NOT NULL,kind TEXT NOT NULL,title TEXT NOT NULL,day TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0)')
            if 'time' not in {row[1] for row in db.execute('PRAGMA table_info(entries)')}:db.execute("ALTER TABLE entries ADD COLUMN time TEXT NOT NULL DEFAULT ''")
            db.execute('CREATE TABLE IF NOT EXISTS goals(owner TEXT PRIMARY KEY,sessions INTEGER NOT NULL,minutes INTEGER NOT NULL,calories INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS display_settings(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS holiday_events(id TEXT PRIMARY KEY,day TEXT NOT NULL,title TEXT NOT NULL,scope TEXT NOT NULL,source TEXT NOT NULL)')
            db.executemany('INSERT INTO holiday_events VALUES(:id,:day,:title,:scope,:source) ON CONFLICT(id) DO UPDATE SET day=excluded.day,title=excluded.title,scope=excluded.scope,source=excluded.source',holidays.catalogue())
            row=db.execute('SELECT value FROM display_settings WHERE id=1').fetchone()
            upgraded=settings.migrate(json.loads(row[0])) if row else settings.defaults()
            db.execute('INSERT INTO display_settings VALUES(1,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value',(json.dumps(upgraded),))
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=5)
        try:
            with db:yield db
        finally:db.close()
    def settings(self):
        with self.db() as db:row=db.execute('SELECT value FROM display_settings WHERE id=1').fetchone()
        return settings.validate(json.loads(row[0])) if row else settings.defaults()
    def save_settings(self,value):
        value=settings.validate(value)
        if value['backgroundMode']!='default':
            available={image['id'] for image in self.gallery.scan()['images']}
            if not value['backgroundImages'] or any(identifier not in available for identifier in value['backgroundImages']):raise ValueError('Selecione imagens disponíveis na galeria.')
        with self.db() as db:db.execute('INSERT INTO display_settings VALUES(1,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value',(json.dumps(value),))
        return value
    def state(self,owner):
        with self.db() as db:
            rows=db.execute('SELECT id,kind,title,day,done,time FROM entries WHERE owner=? ORDER BY day,id',(owner,)).fetchall()
            goals=db.execute('SELECT sessions,minutes,calories FROM goals WHERE owner=?',(owner,)).fetchone()
        prefs=self.settings()
        with self.db() as db:
            holiday_rows=db.execute('SELECT id,day,title,scope,source FROM holiday_events ORDER BY day,id').fetchall()
        return {'settings':prefs,'holidays':[dict(zip(('id','day','title','scope','source'),r)) for r in holiday_rows if r[3] in holidays.REGIONS[prefs['holidayRegion']]],'holidayRange':{'first':holidays.FIRST_YEAR,'last':holidays.LAST_YEAR},'entries':[dict(zip(('id','kind','title','day','done','time'),r)) for r in rows], 'goals':dict(zip(('sessions','minutes','calories'),goals)) if goals else None}
    def save(self,owner,value):
        action=value.get('action')
        with self.db() as db:
            if action=='goals':
                goals=[value.get(k) for k in ('sessions','minutes','calories')]
                if any(type(v)!=int or not 1<=v<=100000 for v in goals):raise ValueError('Metas inválidas.')
                db.execute('INSERT INTO goals VALUES(?,?,?,?) ON CONFLICT(owner) DO UPDATE SET sessions=excluded.sessions,minutes=excluded.minutes,calories=excluded.calories',(owner,*goals))
            elif action in ('add','edit'):
                kind,title,day=value.get('kind'),value.get('title'),value.get('day','')
                if kind not in ('reminder','event') or not isinstance(title,str) or not 1<=len(title.strip())<=160:raise ValueError('Preencha um título de até 160 caracteres.')
                clock=value.get('time','')
                if not isinstance(day,str) or (day and dt.date.fromisoformat(day).isoformat()!=day) or (kind=='event' and not day):raise ValueError('Data inválida.')
                if not isinstance(clock,str) or (clock and not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]',clock)) or (clock and not day):raise ValueError('Informe a data junto do horário.')
                if action=='edit':
                    identifier=value.get('id')
                    if not isinstance(identifier,str) or not db.execute('SELECT 1 FROM entries WHERE owner=? AND id=?',(owner,identifier)).fetchone():raise ValueError('Item não encontrado.')
                    db.execute('UPDATE entries SET kind=?,title=?,day=?,time=? WHERE owner=? AND id=?',(kind,title.strip(),day,clock,owner,identifier))
                elif db.execute('SELECT count(*) FROM entries WHERE owner=?',(owner,)).fetchone()[0]>=500:raise ValueError('Limite de 500 itens. Exclua itens antigos.')
                if action=='add':db.execute('INSERT INTO entries(id,owner,kind,title,day,done,time) VALUES(?,?,?,?,?,0,?)',(secrets.token_urlsafe(16),owner,kind,title.strip(),day,clock))
            elif action in ('delete','toggle'):
                if not isinstance(value.get('id'),str):raise ValueError('Item inválido.')
                sql='DELETE FROM entries WHERE owner=? AND id=?' if action=='delete' else 'UPDATE entries SET done=1-done WHERE owner=? AND id=?'
                db.execute(sql,(owner,value['id']))
            else:raise ValueError('Operação inválida.')
        return self.state(owner)
    def cached(self,key,ttl,loader):
        # Lock also coalesces cold requests from simultaneously opened devices.
        with self.lock:
            old=self.cache.get(key)
            if old and time.monotonic()-old[0]<ttl:return old[1]
            result=loader()
            if len(self.cache)>256:self.cache.clear()
            self.cache[key]=(time.monotonic(),result);return result

def fitness(cfg,identity):
    if not identity:return {'available':False,'reason':'Seu acesso ao openGym não está configurado.'}
    headers={'X-Aurora-Identity':identity,'X-Aurora-Proxy-Secret':cfg['opengymSecret']}
    state=json.loads(fetch('http://opengym-api:3000/api/data',headers)).get('state',{})
    today=dt.date.today();start=today-dt.timedelta(days=35);rows=[]
    for w in state.get('workouts',[]):
        if not isinstance(w,dict) or not start.isoformat()<=str(w.get('d',''))<=today.isoformat():continue
        a,b=w.get('start'),w.get('end');cal=(w.get('garminActivity') or {}).get('calories')
        valid=lambda v:type(v) in (int,float) and math.isfinite(v) and v>=0
        minutes=round((b-a)/60000,1) if valid(a) and valid(b) and b>=a else None
        rows.append({'date':w['d'],'name':str(w.get('name','Treino'))[:150],'minutes':minutes,'calories':cal if valid(cal) else None})
    return {'available':True,'source':'openGym / Garmin','workouts':rows}

def weather(data,lat,lon):
    if type(lat) not in (int,float) or type(lon) not in (int,float) or not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Localização inválida.')
    lat,lon=round(lat,2),round(lon,2)
    query=urllib.parse.urlencode({'latitude':lat,'longitude':lon,'current':'temperature_2m,weather_code','daily':'weather_code,temperature_2m_max,temperature_2m_min','timezone':'auto','forecast_days':3})
    return data.cached(('weather',lat,lon),900,lambda:json.loads(fetch('https://api.open-meteo.com/v1/forecast?'+query)))

def saved_weather(data):
    loc=data.settings()['weatherLocation']
    if loc is None:raise ValueError('Configure a cidade do clima.')
    result=weather(data,loc['lat'],loc['lon'])
    return result|{'location':loc['name']}

def locations(data,query):
    if not isinstance(query,str) or not 2<=len(query.strip())<=100 or any(ord(c)<32 for c in query):raise ValueError('Informe a cidade.')
    query=query.strip()
    def load():
        params=urllib.parse.urlencode({'name':query,'count':5,'language':'pt','format':'json'})
        source=json.loads(fetch('https://geocoding-api.open-meteo.com/v1/search?'+params))
        result=[]
        for row in source.get('results',[])[:5]:
            loc={'name':', '.join(str(row[k]) for k in ('name','admin1','country') if row.get(k))[:160],'lat':row.get('latitude'),'lon':row.get('longitude')}
            settings.validate(settings.defaults()|{'weatherLocation':loc})
            result.append(loc)
        return {'locations':result}
    return data.cached(('locations',query.casefold()),3600,load)

def news(data):
    def load():
        root=ET.fromstring(fetch('https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419'))
        rows=[]
        for item in root.findall('./channel/item')[:8]:
            url=item.findtext('link','');p=urllib.parse.urlsplit(url)
            if p.scheme=='https' and p.hostname=='news.google.com':
                rows.append({'title':item.findtext('title','')[:300],'url':url,'source':item.findtext('source',''),'published':item.findtext('pubDate','')})
        return {'source':'Google Notícias','items':rows,'updatedAt':dt.datetime.now(dt.timezone.utc).isoformat()}
    return data.cached('news',600,load)

def run():
    cfg=json.loads(Path('/run/secrets/mirror.json').read_text());data=Data('/data/mirror.sqlite3')
    slots=threading.BoundedSemaphore(8)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,value):
            raw=json.dumps(value,ensure_ascii=False).encode();self.send_response(status)
            for k,v in {'Content-Type':'application/json','Content-Length':str(len(raw)),'Cache-Control':'no-store'}.items():self.send_header(k,v)
            self.end_headers();self.wfile.write(raw)
        def image(self,raw):
            self.send_response(200)
            for key,value in {'Content-Type':'image/jpeg','Content-Length':str(len(raw)),'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}.items():self.send_header(key,value)
            self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if self.path=='/health':return self.send(200,{'status':'ok'})
            if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+cfg['token']):return self.send(403,{})
            parts=self.path.split('/')
            try:
                if len(parts) not in (3,4) or parts[1]!='backgrounds' or (len(parts)==4 and parts[3]!='thumb'):return self.send(404,{})
                return self.image(data.gallery.image(parts[2],len(parts)==4))
            except (ValueError,FileNotFoundError):return self.send(404,{})
        def do_POST(self):
            if not slots.acquire(False):return self.send(503,{'error':'Aguarde um instante.'})
            try:
                self.connection.settimeout(20)
                if not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+cfg['token']):return self.send(403,{'error':'Não autorizado.'})
                size=int(self.headers.get('Content-Length','0'))
                if self.path=='/backgrounds/upload':
                    if self.headers.get('X-Aurora-Admin')!='1':return self.send(403,{})
                    if self.headers.get('Transfer-Encoding') or not 0<size<=MAX_BYTES:return self.send(413,{'error':'Envie uma imagem de até 12 MB.'})
                    if self.headers.get('Content-Type') not in ('image/jpeg','image/png','image/webp'):return self.send(400,{'error':'Use JPG, PNG ou WebP.'})
                    try:return self.send(200,data.gallery.upload(self.rfile.read(size),urllib.parse.unquote(self.headers.get('X-Image-Name','imagem'))[:160]))
                    except ValueError as error:return self.send(400,{'error':str(error)})
                if self.path!='/query' or self.headers.get('Transfer-Encoding') or not 0<size<=8192:raise ValueError('Conteúdo inválido.')
                v=json.loads(self.rfile.read(size));owner=v.get('owner');action=v.get('action')
                if not isinstance(owner,str) or not 1<=len(owner)<=254:raise ValueError('Perfil inválido.')
                if action in ('settings-get','settings-save'):
                    if v.get('admin') is not True:return self.send(403,{'error':'Somente o administrador pode configurar a tela.'})
                    result={'settings':data.settings() if action=='settings-get' else data.save_settings(v.get('value')),'defaults':settings.defaults()}
                elif action=='state':
                    result=data.state(owner)
                    try:result['fitness']=fitness(cfg,v.get('identity'))
                    except Exception:result['fitness']={'available':False,'reason':'openGym indisponível no momento.'}
                elif action=='agenda':result=agenda.collect(data,cfg,v,fetch)
                elif action=='news':result=news(data)
                elif action=='backgrounds':
                    if v.get('admin') is not True:return self.send(403,{})
                    result=data.gallery.scan()
                elif action=='locations':
                    if v.get('admin') is not True:return self.send(403,{'error':'Somente o administrador pode configurar a cidade.'})
                    result=locations(data,(v.get('value') or {}).get('query'))
                elif action=='weather':result=saved_weather(data)
                else:result=data.save(owner,v.get('value',{}))
                self.send(200,result)
            except (ValueError,TypeError,KeyError):self.send(400,{'error':'Confira os campos e tente novamente.'})
            except Exception:self.send(503,{'error':'A fonte de dados está indisponível. Tente novamente.'})
            finally:slots.release()
    ThreadingHTTPServer(('0.0.0.0',8000),Handler).serve_forever()
if __name__=='__main__':run()
