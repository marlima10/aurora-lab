"""Convert Garmin activity summaries without inventing strength data."""
import copy
import datetime as dt
import hashlib
import math
import re

def finite(value):
    try: n=float(value or 0)
    except (ValueError,TypeError): raise ValueError('Métrica inválida.')
    if not math.isfinite(n): raise ValueError('Métrica inválida.')
    return n

def convert(a):
    aid=str(a.get('activityId',''))
    if not aid.isdigit(): raise ValueError('Identificador inválido.')
    sport=str((a.get('activityType') or {}).get('typeKey','other'))
    if not re.fullmatch(r'[a-zA-Z0-9_]{1,80}',sport): raise ValueError('Modalidade inválida.')
    try:
        day=dt.date.fromisoformat(str(a['startTimeLocal'])[:10]).isoformat()
        start=dt.datetime.fromisoformat(str(a['startTimeGMT']).replace('Z','+00:00'))
    except (ValueError,KeyError): raise ValueError('Data inválida.')
    if start.tzinfo is None: start=start.replace(tzinfo=dt.timezone.utc)
    duration=finite(a.get('duration'));distance=finite(a.get('distance'))
    if duration<=0 or duration>604800 or distance<0 or distance>2000000: raise ValueError('Métricas fora dos limites.')
    title=str(a.get('activityName') or sport.replace('_',' ')).strip()[:160]
    eid='garmin-ex-'+sport.lower();wid='garmin-'+hashlib.sha256(aid.encode()).hexdigest()[:32]
    note='Resumo Garmin: https://connect.garmin.com/modern/activity/'+aid
    note+=' · Sem inferir séries, repetições, carga ou músculos.'
    if distance: note+=' · Distância: '+format(distance/1000,'.3f')+' km'
    row={'min':round(duration/60,4),'speed':round(distance/1000/(duration/3600),4),'done':True}
    workout={'id':wid,'d':day,'start':round(start.timestamp()*1000),
        'end':round((start.timestamp()+duration)*1000),'routineId':None,
        'name':title+' · Garmin','entries':[{'id':eid,'mode':'cardio','sets':[row],'topW':None,'note':note}],
        'prs':[],'vol':0,'note':note,'garminActivity':{'id':aid,'sport':sport}}
    calories=calories_value(a.get('calories'))
    if calories is not None: workout['garminActivity']['calories']=calories
    exercise={'id':eid,'n':sport.replace('_',' ')+' (garmin resumo)','custom':True,
        'eq':'custom','tg':'garmin','desc':'Resumo de duração e distância; sem séries ou carga.','bp':'cardio'}
    return {'activity_id':aid,'name':title,'date':day,'minutes':round(duration/60,1),
        'distance_km':round(distance/1000,3),'workout':workout,'exercise':exercise}

def merge_records(state,records,ledger=()):
    if not isinstance(state,dict) or not isinstance(state.get('workouts'),list) or not isinstance(state.get('routines'),list):
        raise ValueError('Abra o openGym e salve seu perfil antes de importar.')
    if state.get('customEx') is not None and not isinstance(state.get('customEx'),list):
        raise ValueError('Formato de exercícios não reconhecido.')
    out=copy.deepcopy(state)
    if out.get('customEx') is None: out['customEx']=[]
    existing={w.get('id') for w in out['workouts'] if isinstance(w,dict)}
    ex={e.get('id') for e in out['customEx'] if isinstance(e,dict)}
    seen=set(map(str,ledger));added=[];skipped=[]
    for rec in records:
        wid=rec['workout']['id'];aid=rec['activity_id']
        if wid in existing or aid in seen: skipped.append(aid);continue
        out['workouts'].append(copy.deepcopy(rec['workout']));existing.add(wid);seen.add(aid);added.append(aid)
        if rec['exercise']['id'] not in ex:
            out['customEx'].append(copy.deepcopy(rec['exercise']));ex.add(rec['exercise']['id'])
    return out,added,skipped

def calories_value(value):
    # Absence is different from a measured zero; never estimate missing energy.
    if value is None or isinstance(value,bool) or not isinstance(value,(int,float)): return None
    return value if math.isfinite(value) and 0 <= value <= 200000 else None


def enrich_calories(state,records):
    """Fill missing Garmin calories on existing matching workouts only."""
    out=copy.deepcopy(state);changed=0
    source={r['workout']['id']:r for r in records}
    for workout in out.get('workouts',[]):
        record=source.get(workout.get('id'));meta=workout.get('garminActivity')
        if not record or not isinstance(meta,dict) or str(meta.get('id'))!=record['activity_id']: continue
        if calories_value(meta.get('calories')) is not None: continue
        value=calories_value(record['workout']['garminActivity'].get('calories'))
        if value is None: continue
        meta['calories']=value;changed+=1
    return out,changed
