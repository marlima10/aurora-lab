import copy,unittest
from unittest.mock import patch
from mapping import convert,enrich_calories
from test_garmin import SAMPLE,STATE
import test_garmin
import server

class Calories(unittest.TestCase):
 def test_missing_invalid_and_real_zero(self):
  for value in (None,True,-1,float('nan'),float('inf'),'500',300000):
   self.assertNotIn('calories',convert(SAMPLE|{'calories':value})['workout']['garminActivity'])
  for value in (0,530.5):
   self.assertEqual(convert(SAMPLE|{'calories':value})['workout']['garminActivity']['calories'],value)
 def test_fill_only_missing_preserves_all_edits_and_deleted(self):
  record=convert(SAMPLE|{'calories':500});work=copy.deepcopy(record['workout']);work['garminActivity'].pop('calories');work['name']='Edited';work['note']='Private';state=copy.deepcopy(STATE);state['workouts'].append(work);original=copy.deepcopy(state)
  result,count=enrich_calories(state,[record]);self.assertEqual(count,1);expected=copy.deepcopy(state);expected['workouts'][-1]['garminActivity']['calories']=500
  self.assertEqual(result,expected);self.assertEqual(state,original)
  self.assertEqual(enrich_calories(result,[record])[1],0)
  self.assertEqual(enrich_calories(STATE,[record])[0],STATE)
  work['garminActivity']['calories']=0;self.assertEqual(enrich_calories(state,[record])[1],0)
 def test_wrong_source_id_never_enriched(self):
  r=convert(SAMPLE|{'calories':500});w=copy.deepcopy(r['workout']);w['garminActivity']['id']='999';state=copy.deepcopy(STATE);state['workouts']=[w]
  self.assertEqual(enrich_calories(state,[r]),(state,0))

class Backfill(unittest.TestCase):
 setUp=test_garmin.Bridge.setUp
 tearDown=test_garmin.Bridge.tearDown
 user=test_garmin.Bridge.user
 def test_backfill_revision_conflict_and_idempotence(self):
  u=self.user();r=convert(SAMPLE|{'calories':500});state=copy.deepcopy(STATE);state['workouts'].append(convert(SAMPLE)['workout']);sent=[]
  def api(path,headers,body=None):
   if body is None:return 200,{'state':copy.deepcopy(state),'rev':state['_rev']}
   sent.append(body)
   if len(sent)==1:state['routines'].append({'id':'concurrent'});state['_rev']=5;return 409,{}
   self.assertEqual(body['baseRev'],5);self.assertEqual(body['state']['routines'],state['routines']);state.update(body['state']);return 200,{}
  with patch.object(server,'request_json',side_effect=api):
   self.assertEqual(server.backfill_calories(u,[r],{}),{'updated':1})
   self.assertEqual(server.backfill_calories(u,[r],{}),{'updated':0})
  self.assertEqual(u.ledger(),[]);self.assertTrue((u.path/'before-calories.json').exists())

class BackfillJob(unittest.TestCase):
 def setUp(self):
  import tempfile
  from pathlib import Path
  self.tmp=tempfile.TemporaryDirectory();self.old=server.ROOT;server.ROOT=Path(self.tmp.name);self.u=server.User('calories-test')
  self.u.save('personal-api.json',{'api_key':'synthetic'});self.u.save('auto-auth.json',{'token':'synthetic'});self.u.save('auto-sync.json',{'uid':'calories-test','enabled':True})
 def tearDown(self):server.ROOT=self.old;self.tmp.cleanup()
 def execute(self,apply=False,wrong=False,truncated=False):
  import backfill,datetime
  state=copy.deepcopy(STATE);state['workouts']=[convert(SAMPLE)['workout']];puts=[]
  def api(path,headers,body=None):
   if path=='/api/me':return 200,{'user':{'id':'wrong' if wrong else self.u.uid}}
   if body is not None:puts.append(body);state.update(body['state']);return 200,{}
   return 200,{'state':copy.deepcopy(state),'rev':4}
  def load(u,first,last):u.preview=[convert(SAMPLE|{'calories':500})];u.truncated=truncated;u.invalid=0
  with patch.object(server,'user_for',return_value=self.u),patch.object(server,'load',side_effect=load),patch.object(server,'request_json',side_effect=api):
   result=backfill.run(datetime.date(2026,1,1),datetime.date(2026,10,21),apply)
  return result,puts
 def test_preview_does_not_write_workouts(self):
  result,puts=self.execute();self.assertEqual(puts,[]);self.assertEqual(result['eligible'],1);self.assertFalse(result['applied'])
 def test_apply_only_enriches_and_checks_expected_state(self):
  result,puts=self.execute(True);self.assertEqual(len(puts),1);self.assertEqual(result['updated'],1);self.assertTrue(result['expected_profile_verified']);self.assertEqual(self.u.ledger(),[])
 def test_wrong_identity_refused(self):
  with self.assertRaises(ValueError):self.execute(True,wrong=True)
 def test_partial_source_refused(self):
  with self.assertRaises(ValueError):self.execute(True,truncated=True)
