"""Explicit one-off calorie enrichment. Stop the hourly bridge while running this job."""
import argparse,datetime as dt,hashlib,json
import server
from mapping import enrich_calories

def run(first,last,apply=False):
    if first>last or (last-first).days>366: raise ValueError('Escolha um período de até um ano.')
    paths=[p for p in server.ROOT.glob('*/personal-api.json') if (p.parent/'auto-auth.json').exists()]
    if len(paths)!=1: raise ValueError('A manutencao exige exatamente um perfil Garmin com autorizacao automatica.')
    folder=paths[0].parent
    config=json.loads((folder/'auto-sync.json').read_text());uid=config.get('uid')
    if not isinstance(uid,str) or hashlib.sha256(uid.encode()).hexdigest()!=folder.name: raise ValueError('Perfil inconsistente.')
    u=server.user_for(uid);token=server.AUTO.read(u,'auto-auth.json').get('token')
    if not server.valid_secret(token): raise ValueError('Reative a atualizacao no seu perfil.')
    headers={'Authorization':'Bearer '+token}
    _,me=server.request_json('/api/me',headers)
    if str((me.get('user') or {}).get('id',''))!=uid: raise ValueError('Autorizacao de outro perfil.')
    if me.get('token'):
        if not server.valid_secret(me['token']): raise ValueError('Renovacao invalida.')
        u.save('auto-auth.json',{'token':me['token']});headers={'Authorization':'Bearer '+me['token']}
    server.load(u,first.isoformat(),last.isoformat())
    if u.truncated or u.invalid: raise ValueError('Consulta incompleta ou invalida. Nenhum treino foi alterado.')
    _,before=server.request_json('/api/data',headers)
    _,eligible=enrich_calories(before['state'],u.preview)
    result=server.backfill_calories(u,u.preview,headers) if apply else {'updated':0}
    _,after=server.request_json('/api/data',headers)
    expected,_=enrich_calories(before['state'],u.preview) if apply else (before['state'],0)
    # No concurrent profile writes are hidden by the validation: fail visibly if any other field changed.
    def public(value):
        if isinstance(value,dict): return {k:public(v) for k,v in value.items() if not k.startswith('_')}
        if isinstance(value,list): return [public(v) for v in value]
        return value
    preserved=public(expected)==public(after['state'])
    record={'time':dt.datetime.now(dt.timezone.utc).isoformat(),'period':[first.isoformat(),last.isoformat()],
        'source_activities':len(u.preview),'eligible':eligible,'updated':result['updated'],'applied':apply,
        'expected_profile_verified':preserved,'workouts_before':len(before['state']['workouts']),'workouts_after':len(after['state']['workouts']),
        'workouts_with_calories':sum(1 for w in after['state']['workouts'] if isinstance(w.get('garminActivity',{}).get('calories'),(int,float)))}
    u.save('calories-backfill-status.json',record)
    if not preserved: raise ValueError('O perfil mudou durante a verificacao. Confira o snapshot before-calories.json e nao restaure sobre edicoes recentes.')
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--first',required=True,type=dt.date.fromisoformat);p.add_argument('--last',required=True,type=dt.date.fromisoformat);p.add_argument('--apply',action='store_true');a=p.parse_args()
    try: print(json.dumps(run(a.first,a.last,a.apply)))
    except Exception as error: print(json.dumps({'error':server.error_message(error)}));raise SystemExit(1)
