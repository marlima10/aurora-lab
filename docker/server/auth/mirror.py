"""Authenticated facade; native identity always comes from the central session."""
import json
import urllib.request
import urllib.error

def query(session,cfg,action,value=None):
    if 'portal' not in session['grants']:raise ValueError('Portal não autorizado.')
    payload={'owner':session['email'],'identity':session['grants'].get('opengym'),'action':action}
    if action=='weather':payload.update(value or {})
    elif value is not None:payload['value']=value
    key=cfg.get('_mirror_secret','')
    if len(key)<32:return 503,{'error':'Painel ainda não configurado.'}
    req=urllib.request.Request('http://mirror-api:8000/query',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    try:
        with urllib.request.urlopen(req,timeout=20) as r:return r.status,json.loads(r.read(2_000_000))
    except urllib.error.HTTPError as e:
        return e.code,{'error':'Confira os dados e tente novamente.' if e.code==400 else 'Painel indisponível no momento.'}
    except Exception:return 503,{'error':'Painel indisponível no momento.'}
