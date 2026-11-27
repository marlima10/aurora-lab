"""Read-only agenda projection. Native apps remain the owners of their records."""
import datetime as dt
import json
import urllib.parse
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('America/Sao_Paulo')
MEALS = {'breakfast':'Café da manhã','lunch':'Almoço','dinner':'Jantar','side':'Acompanhamento','snack':'Lanche','drink':'Bebida','dessert':'Sobremesa'}


def date_range(value):
    if not isinstance(value, dict):raise ValueError('Informe o período.')
    start, end = (dt.date.fromisoformat(value[k]) for k in ('start','end'))
    if start.isoformat()!=value['start'] or end.isoformat()!=value['end'] or not 0 <= (end-start).days <= 41:
        raise ValueError('Escolha até 42 dias.')
    return start, end


def item(source, key, day, title, *, time='', status='', url='', kind=''):
    return {'id':source+':'+str(key), 'source':source, 'day':day, 'time':time,
            'title':str(title or 'Sem título')[:160], 'status':status, 'url':url, 'kind':kind}


def planned_ids(state, day, today):
    """Mirror openGym 1.4.5 queue/pin/weekday semantics without inventing dates."""
    routines = {r['id']:r for r in state.get('routines',[]) if isinstance(r,dict) and isinstance(r.get('id'),str)}
    plan = state.get('dayPlan') or {}; override = plan.get(day)
    if override == 'rest':return []
    raw = state.get('queue'); queue = None
    if isinstance(raw,dict) and isinstance(raw.get('ids'),list):
        ids = list(dict.fromkeys(x for x in raw['ids'] if isinstance(x,str) and x in routines))
        since = raw.get('since',0)
        since = since if type(since) in (int,float) else 0
        starts = raw.get('startsOn') or (dt.datetime.fromtimestamp(since/1000,ZONE).date().isoformat() if since>0 else None)
        if ids and starts and not (raw.get('strict') is True and since<=0):queue = raw | {'ids':ids,'since':since,'startsOn':starts}
    def done(identifier):
        name = str(routines[identifier].get('name') or '')
        for w in state.get('workouts',[]):
            if not isinstance(w,dict):continue
            ids = w.get('routineIds') if isinstance(w.get('routineIds'),list) else [w.get('routineId')]
            if identifier not in ids:continue
            start = w.get('start') or 0; title = str(w.get('name') or '')
            if queue['since']>0 and type(start) in (int,float) and start>=queue['since']:return True
            named = name and (title==name or title.startswith(name+' + ') or title.endswith(' + '+name) or ' + '+name+' + ' in title)
            if queue.get('strict') is not True and queue['startsOn']<=str(w.get('d',''))<=today and named:return True
        return False
    pin = ('done' if done(override) else 'open') if queue and override in queue['ids'] else None
    if not pin and override in routines:return [override]
    weekday = str((dt.date.fromisoformat(day).weekday()+1)%7)
    week = (state.get('week') or {}).get(weekday,[])
    week = week if isinstance(week,list) else [week]
    own = [x for x in week if isinstance(x,str) and x in routines]
    remaining = [x for x in queue['ids'] if not done(x)] if queue else []
    on = max(today,queue['startsOn']) if queue else ''
    pins = [(d,x) for d,x in plan.items() if d>=today and x in remaining]
    next_id = next((x for d,x in pins if d==on),None) or next((x for x in remaining if not any(v==x for _,v in pins)),None)
    selected = override if pin=='open' else next_id if day==on else None
    if selected or (queue and day==on and remaining):own = [x for x in own if x not in queue['ids']]
    return list(dict.fromkeys(([selected] if selected else [])+own))


def workouts(state, start, end, today):
    rows=[]; routines={r['id']:r for r in state.get('routines',[]) if isinstance(r,dict) and isinstance(r.get('id'),str)}
    for index,w in enumerate(state.get('workouts',[])):
        if not isinstance(w,dict) or not start.isoformat()<=str(w.get('d',''))<=end.isoformat():continue
        stamp=w.get('start'); clock=''
        if type(stamp) in (int,float) and 0<stamp<4_102_444_800_000:
            clock=dt.datetime.fromtimestamp(stamp/1000,ZONE).strftime('%H:%M')
        rows.append(item('training',str(w.get('id') or index),w['d'],w.get('name','Treino'),time=clock,status='Realizado',url='/opengym'))
    # Past schedules are not historical facts. Only completed records appear in the past.
    for offset in range((end-start).days+1):
        day=(start+dt.timedelta(days=offset)).isoformat()
        if day<today:continue
        for identifier in planned_ids(state,day,today):
            rows.append(item('training',day+':'+identifier,day,routines[identifier].get('name','Treino'),status='Planejado',url='/opengym'))
    return rows


def meals(fetch, secret, identity, start, end):
    headers={'X-Aurora-Identity':identity,'X-Aurora-Proxy-Secret':secret,'X-Mealie-Reverse-Proxy-Secret':secret}
    rows=[]
    for page in range(1,12):
        query=urllib.parse.urlencode({'start_date':start.isoformat(),'end_date':end.isoformat(),'perPage':100,'page':page,'orderBy':'date','orderDirection':'asc'})
        payload=json.loads(fetch('http://mealie:9000/api/households/mealplans?'+query,headers))
        if not isinstance(payload,dict) or not isinstance(payload.get('items'),list):raise ValueError('Resposta inválida.')
        for entry in payload['items']:
            day=str(entry.get('date',''))
            if not start.isoformat()<=day<=end.isoformat():continue
            recipe=entry.get('recipe') or {}; title=entry.get('title') or recipe.get('name') or entry.get('text') or 'Refeição'
            rows.append(item('meals',entry['id'],day,title,status=MEALS.get(entry.get('entryType'),'Refeição'),url='/mealie'))
        total=payload.get('total_pages',payload.get('totalPages',1))
        if page>=int(total):return rows
    raise ValueError('Muitas refeições no período. Escolha uma semana.')


def collect(data, cfg, value, fetch):
    start,end=date_range(value.get('value')); state=data.state(value['owner']); rows=[]; sources=[]
    for entry in state['entries']:
        if start.isoformat()<=entry['day']<=end.isoformat():
            source='reminders' if entry['kind']=='reminder' else 'personal'
            rows.append(item(source,entry['id'],entry['day'],entry['title'],time=entry.get('time',''),status='Concluído' if entry['done'] else '',kind=entry['kind']))
    for holiday in state['holidays']:
        if start.isoformat()<=holiday['day']<=end.isoformat():rows.append(item('holidays',holiday['id'],holiday['day'],holiday['title'],status='Feriado',url=holiday['source']))
    today=dt.datetime.now(ZONE).date().isoformat()
    for source,identity,secret_key in [('training',value.get('identity'),'opengymSecret'),('meals',value.get('mealieIdentity'),'mealieSecret')]:
        if not identity or not cfg.get(secret_key):
            sources.append({'source':source,'status':'unauthorized','message':'Acesso não configurado.'});continue
        def load():
            if source=='meals':return meals(fetch,cfg[secret_key],identity,start,end)
            native=json.loads(fetch('http://opengym-api:3000/api/data',{'X-Aurora-Identity':identity,'X-Aurora-Proxy-Secret':cfg[secret_key]}))
            if not isinstance(native.get('state'),dict):raise ValueError('Resposta inválida.')
            return workouts(native['state'],start,end,today)
        try:
            records=data.cached(('agenda',source,identity,start.isoformat(),end.isoformat(),today),60,load)
            rows.extend(records);sources.append({'source':source,'status':'ok','count':len(records)})
        except Exception:sources.append({'source':source,'status':'unavailable','message':'Fonte indisponível; tente atualizar.'})
    rows.sort(key=lambda row:(row['day'],row['time'] or '00:00',row['source'],row['id']))
    return {'start':start.isoformat(),'end':end.isoformat(),'timezone':str(ZONE),'items':rows,'sources':sources,'updatedAt':dt.datetime.now(dt.timezone.utc).isoformat()}
