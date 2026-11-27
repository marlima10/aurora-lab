"""Authenticated facade; native identity always comes from the central session."""
import json
import urllib.request
import urllib.error

def query(session,cfg,action,value=None):
    if 'portal' not in session['grants']:raise ValueError('Portal não autorizado.')
    payload={'owner':session['email'],'identity':session['grants'].get('opengym'),'mealieIdentity':session['grants'].get('mealie'),'action':action,'admin':session.get('admin') is True}
    if value is not None and action!='weather':payload['value']=value
    key=cfg.get('_mirror_secret','')
    if len(key)<32:return 503,{'error':'Painel ainda não configurado.'}
    req=urllib.request.Request('http://mirror-api:8000/query',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    try:
        with urllib.request.urlopen(req,timeout=35 if action=='agenda' else 20) as r:return r.status,json.loads(r.read(2_000_000))
    except urllib.error.HTTPError as e:
        return e.code,{'error':'Confira os dados e tente novamente.' if e.code==400 else 'Painel indisponível no momento.'}
    except Exception:return 503,{'error':'Painel indisponível no momento.'}

MAX_IMAGE_BYTES=12*1024*1024

def upload(session,cfg,raw,content_type,name):
    if 'portal' not in session['grants'] or not session.get('admin'):return 403,{'error':'Somente o administrador pode enviar imagens.'}
    if len(cfg.get('_mirror_secret',''))<32:return 503,{'error':'Galeria não configurada.'}
    req=urllib.request.Request('http://mirror-api:8000/backgrounds/upload',data=raw,headers={'Content-Type':content_type,'Authorization':'Bearer '+cfg['_mirror_secret'],'X-Aurora-Admin':'1','X-Image-Name':name})
    try:
        with urllib.request.urlopen(req,timeout=30) as response:return response.status,json.loads(response.read(2_000_000))
    except urllib.error.HTTPError as error:
        if error.code in (400,413):return error.code,json.loads(error.read(8192))
        return 503,{'error':'Galeria indisponível.'}
    except Exception:return 503,{'error':'Não foi possível enviar a imagem.'}

def image(session,cfg,identifier,thumb=False):
    import re
    if 'portal' not in session['grants'] or not re.fullmatch(r'[a-f0-9]{64}',identifier):return 404,b''
    if len(cfg.get('_mirror_secret',''))<32:return 503,b''
    req=urllib.request.Request('http://mirror-api:8000/backgrounds/'+identifier+('/thumb' if thumb else ''),headers={'Authorization':'Bearer '+cfg['_mirror_secret']})
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            raw=response.read(MAX_IMAGE_BYTES+1)
            return (200,raw) if len(raw)<=MAX_IMAGE_BYTES else (503,b'')
    except urllib.error.HTTPError as error:return error.code,b''
    except Exception:return 503,b''
