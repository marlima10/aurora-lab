import copy
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
import types
from unittest.mock import patch
import urllib.request
import urllib.error
os.environ.setdefault('PUBLIC_ORIGIN','https://test.ts.net:8081')
import server
from mapping import convert,merge_records

SAMPLE={'activityId':12345,'activityType':{'typeKey':'running'},'activityName':'Corrida <teste>',
 'startTimeLocal':'2026-10-17 23:30:00','startTimeGMT':'2026-10-18 02:30:00','duration':1800,'distance':5000}
STATE={'workouts':[{'id':'existing','d':'2026-10-17','entries':[]}],
 'routines':[{'id':'plan'}],'customEx':[],'bodyweight':[{'w':75}],'unit':'lb','_wid':'before','_rev':4}
class Mapping(unittest.TestCase):
 def test_units_local_date_and_no_fabricated_load(self):
  r=convert(SAMPLE);self.assertEqual(r['date'],'2026-10-17');self.assertEqual(r['distance_km'],5)
  self.assertEqual(r['workout']['entries'][0]['sets'],[{'min':30,'speed':10,'done':True}])
  self.assertEqual(r['workout']['start'],1792290600000);self.assertEqual(r['workout']['vol'],0)
 def test_preserves_profile_and_does_not_mutate_input(self):
  original=copy.deepcopy(STATE);result,added,_=merge_records(STATE,[convert(SAMPLE)])
  self.assertEqual(STATE,original);self.assertEqual(added,['12345'])
  for key in ('routines','bodyweight','unit'):self.assertEqual(result[key],STATE[key])
  self.assertEqual(result['workouts'][0],STATE['workouts'][0])
 def test_duplicate_and_deleted_import_stay_skipped(self):
  r=convert(SAMPLE);one,_,_=merge_records(STATE,[r,r]);two,added,skipped=merge_records(one,[r])
  self.assertEqual(one,two);self.assertEqual(added,[]);self.assertEqual(skipped,['12345'])
  gone=copy.deepcopy(one);gone['workouts']=[]
  result,added,_=merge_records(gone,[r],['12345']);self.assertEqual(result['workouts'],[])
 def test_invalid_data_refused_and_null_custom_supported(self):
  for change in ({'distance':-1},{'duration':float('nan')},{'duration':0},{'activityId':'../x'},{'startTimeLocal':'invalid'}):
   with self.assertRaises(ValueError):convert(SAMPLE|change)
  result,_,_=merge_records(STATE|{'customEx':None},[convert(SAMPLE)]);self.assertEqual(len(result['customEx']),1)
  with self.assertRaises(ValueError):merge_records(None,[convert(SAMPLE)])
 def test_strength_is_duration_summary(self):
  r=convert(SAMPLE|{'activityType':{'typeKey':'strength_training'},'distance':0})
  row=r['workout']['entries'][0]['sets'][0];self.assertEqual(row['speed'],0)
  self.assertNotIn('r',row);self.assertNotIn('w',row);self.assertEqual(r['exercise']['bp'],'cardio')
class Bridge(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=server.ROOT;server.ROOT=Path(self.tmp.name)
 def tearDown(self):server.ROOT=self.old;self.tmp.cleanup()
 def user(self):
  u=server.User('test-user');u.preview=[convert(SAMPLE)];u.expires=time.time()+600;return u
 def test_conflict_refetch_preserves_concurrent_change(self):
  u=self.user();current=copy.deepcopy(STATE);sent=[]
  def api(path,headers,body=None):
   self.assertEqual(headers,{'Cookie':'synthetic'})
   if body is None:return 200,{'state':copy.deepcopy(current),'rev':current['_rev']}
   sent.append(body)
   if len(sent)==1:current['routines'].append({'id':'new-plan'});current['_rev']=5;current['_wid']='concurrent';return 409,{}
   self.assertEqual(body['baseRev'],5);self.assertEqual(body['baseWid'],'concurrent')
   self.assertEqual(len(body['state']['routines']),2);return 200,{}
  with patch.object(server,'request_json',side_effect=api):result=server.import_selected(u,['12345'],{'Cookie':'synthetic'})
  self.assertEqual(result,{'added':1,'skipped':0});self.assertEqual(u.ledger(),['12345'])
  self.assertTrue((u.path/'before-import.json').exists())
 def test_failure_leaves_ledger_unchanged(self):
  u=self.user()
  def api(path,headers,body=None):
   if body is None:return 200,{'state':STATE,'rev':4}
   raise server.Problem(502,'Unavailable')
  with patch.object(server,'request_json',side_effect=api):
   with self.assertRaises(server.Problem):server.import_selected(u,['12345'],{})
  self.assertEqual(u.ledger(),[]);self.assertFalse(u.busy)
 def test_profiles_are_separate_and_selection_scoped(self):
  one=self.user();two=server.User('other');one.save('imported.json',['12345'])
  self.assertNotEqual(one.path,two.path);self.assertEqual(two.ledger(),[])
  with self.assertRaises(server.Problem):server.import_selected(one,['not-in-preview'],{})
 def test_cannot_authenticate_without_opengym_session(self):
  with self.assertRaises(server.Problem):server.session({})
  with patch.object(server,'request_json',return_value=(200,{'user':{'id':'one'}})):
   uid,h=server.session({'Cookie':'synthetic','X-User':'other'})
  self.assertEqual(uid,'one');self.assertEqual(h,{'Cookie':'synthetic'})
 def test_sso_identity_is_forwarded_only_when_explicitly_enabled(self):
  headers={'X-Aurora-Identity':'existing-profile','X-Aurora-Proxy-Secret':'fixture-private-proxy-secret-000000000'}
  with patch.dict(os.environ,{'AURORA_SSO_ENABLED':'0'}):
   with self.assertRaises(server.Problem):server.session(headers)
  with patch.dict(os.environ,{'AURORA_SSO_ENABLED':'1'}):
   with patch.object(server,'request_json',return_value=(200,{'user':{'id':'existing-profile'}})) as call:
    uid,forwarded=server.session(headers)
   self.assertEqual(uid,'existing-profile');self.assertEqual(forwarded,headers);call.assert_called_once_with('/api/me',headers)
 def test_login_mfa_token_save_without_password_persistence(self):
  u=self.user();clients=[]
  class Fake:
   def __init__(self,**kw):self.password=kw['password'];self.prompt=kw['prompt_mfa'];self.client=self;clients.append(self)
   def login(self):self.code=self.prompt()
   def dump(self,path):(Path(path)/'garmin_tokens.json').write_text('{"synthetic":true}')
  with patch.dict('sys.modules',{'garminconnect':types.SimpleNamespace(Garmin=Fake)}):
   server.background(u,lambda:server.login(u,'test@example.invalid','synthetic-password'))
   deadline=time.time()+2
   while u.status!='mfa' and time.time()<deadline:time.sleep(.01)
   self.assertEqual(u.status,'mfa');u.mfa.put('123456')
   while u.busy and time.time()<deadline:time.sleep(.01)
  self.assertFalse(u.busy);self.assertIsNone(clients[0].password)
  self.assertEqual(clients[0].code,'123456')
  self.assertEqual(json.loads((u.path/'tokens'/'garmin_tokens.json').read_text()),{'synthetic':True})
 def test_preview_filters_dates_and_ignores_invalid_activity(self):
  u=self.user()
  class Fake:
   def login(self,path):pass
   def get_activities(self,start,limit):return [SAMPLE,SAMPLE|{'activityId':2,'duration':-1},SAMPLE|{'activityId':3,'startTimeLocal':'2025-01-01 12:00:00'}]
  with patch.dict('sys.modules',{'garminconnect':types.SimpleNamespace(Garmin=Fake)}):
   server.load(u,'2026-10-17','2026-10-18')
  self.assertEqual(len(u.preview),1);self.assertEqual(u.invalid,1)
 def test_http_csrf_and_unauthenticated_access(self):
  http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
  base='http://127.0.0.1:'+str(http.server_port)
  try:
   for path,data,origin,code in [('/garmin/status',None,None,401),('/garmin/login',b'{}','https://evil.test',403),('/garmin/auto',b'{"enabled":true}',server.ORIGIN,401),('/garmin/auto',b'{"enabled":true}','https://evil.test',403)]:
    req=urllib.request.Request(base+path,data=data,headers={'Origin':origin} if origin else {})
    with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(req)
    self.assertEqual(caught.exception.code,code)
   with urllib.request.urlopen(base+'/garmin/') as res:
    self.assertEqual(res.status,200);self.assertIn("frame-ancestors 'none'",res.headers['Content-Security-Policy'])
  finally:http.shutdown();http.server_close();thread.join()
if __name__=='__main__':unittest.main()