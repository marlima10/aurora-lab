import json,hashlib,uuid,datetime,traceback
from pathlib import Path
from decimal import Decimal
from zoneinfo import ZoneInfo
from django.db import connection,transaction
from django.contrib.auth import get_user_model
from wger.core.models import Language,RepetitionUnit,WeightUnit
from wger.exercises.models import Exercise,ExerciseCategory,Translation
from wger.manager.models import Routine,Day,Slot,SlotEntry,SetsConfig,RepetitionsConfig,WeightConfig,WorkoutSession,WorkoutLog
from wger.measurements.models import Category,Measurement
from import_values import map_set
assert connection.settings_dict['NAME']=='wger_test','Import only into the isolated evaluation DB.'
raw=Path('/import/source-opengym.json').read_bytes();sha=hashlib.sha256(raw).hexdigest();state=json.loads(raw)['state'];catalogue=json.loads(Path('/import/catalogue.json').read_text())
uid=lambda kind,value:uuid.uuid5(uuid.NAMESPACE_URL,'auroralab-wger:'+kind+':'+str(value))
instant=lambda value:datetime.datetime.fromtimestamp(value/1000,datetime.timezone.utc)
def import_all():
 with transaction.atomic():
  with connection.cursor() as c:
   c.execute('CREATE TABLE IF NOT EXISTS aurora_import_snapshot(id text PRIMARY KEY,sha256 text NOT NULL,source jsonb NOT NULL,report jsonb NOT NULL)')
   c.execute("SELECT sha256 FROM aurora_import_snapshot WHERE id='opengym'");existing=c.fetchone()
   if existing:
    if existing[0]!=sha:raise ValueError('Another snapshot already exists; refusing to overwrite evaluation data.')
    return {'alreadyImported':True,'sha256':sha}
  user=get_user_model().objects.get(username='rafael')
  language=Language.objects.filter(short_name__in=['pt','pt-br']).first()
  if not language:raise ValueError('Portuguese exercise language is missing')
  unit=WeightUnit.objects.get(name='lb' if state.get('unit')=='lbs' else 'kg')
  category,_=ExerciseCategory.objects.get_or_create(name='Importado do openGym')
  workouts=[w for w in state['workouts'] if w['id'] not in state.get('deleted',{}).get('workouts',{})]
  routines=[r for r in state.get('routines',[]) if r['id'] not in state.get('deleted',{}).get('routines',{})]
  custom={str(e['id']):e for e in state.get('customEx',[])}
  exercise_ids={str(e['id']) for w in workouts for e in w.get('entries',[])}|{str(e['id']) for r in routines for e in r.get('ex',[])}
  exercises={}
  for key in exercise_ids:
   cat=catalogue.get(key,{})
   name=custom.get(key,{}).get('n') or cat.get('displayName') or cat.get('name')
   if not name:raise ValueError('Original exercise name is missing')
   exercise=Exercise.objects.create(uuid=uid('exercise',key),category=category)
   Translation.objects.create(uuid=uid('translation',key),exercise=exercise,language=language,name=name,description_source='Exercício copiado de um histórico privado do openGym. Consulte os detalhes originais no snapshot de importação.')
   exercises[key]=exercise
  today=datetime.date.today();end=today+datetime.timedelta(days=119)
  plans={};days={}
  for r in routines:
   plan=Routine.objects.create(user=user,name=r['name'][:25],description='Cópia de avaliação do openGym. Nome original: '+r['name']+'. Datas de vigência técnicas do teste; agenda original preservada no snapshot.',start=today,end=end,is_public=False)
   day=Day.objects.create(routine=plan,name='Rotina importada',order=1)
   plans[r['id']]=plan;days[r['id']]=day
   for i,e in enumerate(r.get('ex',[])):
    reps,repname,weight,weightname=map_set(e)
    slot=Slot.objects.create(day=day,order=i+1)
    entry=SlotEntry.objects.create(slot=slot,exercise=exercises[str(e['id'])],order=1,repetition_unit=RepetitionUnit.objects.get(name=repname),weight_unit=WeightUnit.objects.get(name=weightname) if weightname else unit)
    SetsConfig.objects.create(slot_entry=entry,iteration=1,value=e.get('sets',1))
    if reps is not None:RepetitionsConfig.objects.create(slot_entry=entry,iteration=1,value=reps)
    if weight is not None:WeightConfig.objects.create(slot_entry=entry,iteration=1,value=weight)
  archive=Routine.objects.create(user=user,name='Histórico openGym/Garmin',description='Agrupador técnico da cópia histórica. As datas reais constam nas sessões e no relatório; não é uma recomendação de treino.',start=today,end=end,is_public=False)
  archive_day=Day.objects.create(routine=archive,name='Histórico importado',order=1)
  report={'treinos':0,'seriesExecutadas':0,'seriesNaoConcluidasPreservadas':0,'rotinas':len(routines),'agrupadoresTecnicos':1,'registrosDePeso':0,'exercicios':len(exercises)}
  for w in workouts:
   start=instant(w['start']);finish=instant(w['end'])
   if finish<start:raise ValueError('Invalid original timestamps')
   plan=plans.get(w.get('routineId'),archive);day=days.get(w.get('routineId'),archive_day)
   notes='Cópia openGym/Garmin. '+json.dumps({'nome':w.get('name'),'dataOriginal':w.get('d'),'notas':w.get('note'),'garmin':w.get('garminActivity'),'exercicios':w.get('entries',[])},ensure_ascii=False)
   session=WorkoutSession.objects.create(id=uid('session',w['id']),user=user,routine=plan,day=day,datetime_start=start,datetime_end=finish,notes=notes)
   for i,e in enumerate(w.get('entries',[])):
    for n,s in enumerate(e.get('sets',[])):
     if s.get('done') is not True:report['seriesNaoConcluidasPreservadas']+=1;continue
     reps,repname,weight,weightname=map_set(s)
     if reps is None and weight is None:raise ValueError('Completed set has no representable value')
     when=start  # Set update timestamps are not a replacement for the workout date.
     log=WorkoutLog(id=uid('set',str(w['id'])+':'+str(i)+':'+str(n)),user=user,session=session,routine=plan,date=when,exercise=exercises[str(e['id'])],repetitions=reps,repetitions_unit=RepetitionUnit.objects.get(name=repname),weight=weight,weight_unit=WeightUnit.objects.get(name=weightname) if weightname else unit)
     log.save();report['seriesExecutadas']+=1
   report['treinos']+=1
  body=Category.get_or_create_body_weight(user,unit='lb' if state.get('unit')=='lbs' else 'kg')
  for i,w in enumerate(state.get('bodyweight',[])):
   date=datetime.datetime.combine(datetime.date.fromisoformat(w['d']),datetime.time(),tzinfo=ZoneInfo('America/Sao_Paulo'))
   Measurement.objects.create(id=uid('weight',i),category=body,date=date,value=Decimal(str(w['w'])),extra_data={'unit':body.unit,'originalDate':w['d'],'originalTimestamp':w.get('t')})
   report['registrosDePeso']+=1
  with connection.cursor() as c:c.execute('INSERT INTO aurora_import_snapshot VALUES(%s,%s,%s::jsonb,%s::jsonb)',['opengym',sha,json.dumps(state),json.dumps(report)])
  return dict(report,sha256=sha)
try:print(json.dumps(import_all()))
except Exception:
 diagnostic=Path('/tmp/wger-import-error.log')
 diagnostic.write_text(traceback.format_exc())
 diagnostic.chmod(0o600)
 raise RuntimeError('Importação abortada; detalhes somente no diagnóstico privado.') from None
