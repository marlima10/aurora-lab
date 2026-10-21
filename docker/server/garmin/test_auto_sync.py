import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ.setdefault('PUBLIC_ORIGIN','https://test.ts.net:8081')
import server
from auto_sync import AutoSync,SyncError,INTERVAL
from test_garmin import SAMPLE,STATE

class AutoSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.old=server.ROOT;server.ROOT=self.root;self.u=server.User('owner')
        self.u.save('personal-api.json',{'api_key':'synthetic-key'})
        self.now=10000;self.state=copy.deepcopy(STATE);self.calls=[];self.write_count=0
        self.latest=[SAMPLE];self.renew=False;self.denied=False
        class Client:
            def __init__(inner,key):self.assertEqual(key,'synthetic-key')
            def activities(inner,start,limit):
                self.assertEqual((start,limit),(0,1));return self.latest
        self.auto=AutoSync(self.root,lambda uid:self.u,self.api,server.write_records,server.error_message,client_factory=Client,clock=lambda:self.now)
    def tearDown(self):server.ROOT=self.old;self.temp.cleanup()
    def api(self,path,headers,body=None,method=None):
        self.calls.append((path,headers,body,method))
        if path=='/api/pair/create':
            self.assertEqual(headers,{'Cookie':'synthetic-browser'});self.assertEqual(method,'POST')
            return 200,{'code':'ONETIME'}
        if path=='/api/pair/redeem':
            self.assertEqual(headers,{});self.assertEqual(body,{'code':'ONETIME'})
            return 200,{'user':{'id':'owner'},'token':'synthetic-bearer'}
        if path=='/api/me':
            if self.denied:raise server.Problem(401,'Sessao encerrada')
            return 200,{'user':{'id':'owner'},**({'token':'renewed-bearer'} if self.renew else {})}
        if path=='/api/data':
            self.assertIn('Authorization',headers);self.assertNotIn('Cookie',headers)
            if body is None:return 200,{'state':copy.deepcopy(self.state),'rev':self.state['_rev']}
            self.write_count+=1;self.state=copy.deepcopy(body['state']);self.state['_rev']+=1
            return 200,{'ok':True}
        raise AssertionError(path)
    def enable(self):return self.auto.enable(self.u,{'Cookie':'synthetic-browser'})
    def execute_sync(self):
        with patch.object(server,'request_json',side_effect=self.api):return self.auto.run(self.u)
    def test_initial_latest_import_and_hourly_no_duplicate(self):
        self.enable();self.assertEqual(self.execute_sync(),{'added':1,'skipped':0});self.assertEqual(self.write_count,1)
        self.assertEqual(self.auto.config(self.u)['next_run'],self.now+INTERVAL)
        self.assertIsNone(self.execute_sync());self.now+=INTERVAL
        self.assertEqual(self.execute_sync(),{'added':0,'skipped':1});self.assertEqual(self.write_count,1)
        self.assertEqual(self.state['routines'],STATE['routines']);self.assertEqual(self.state['bodyweight'],STATE['bodyweight'])
        self.assertEqual(self.state['workouts'][0],STATE['workouts'][0]);self.assertEqual(self.u.ledger(),['12345'])
    def test_schedule_survives_restart_and_waits_one_hour(self):
        self.enable();self.execute_sync();self.now+=INTERVAL-1
        restarted=AutoSync(self.root,lambda uid:server.User(uid),self.api,server.write_records,server.error_message,client_factory=self.auto.client_factory,clock=lambda:self.now)
        with patch.object(server,'request_json',side_effect=self.api):
            restarted.tick();self.assertEqual(self.write_count,1)
            self.now+=1;restarted.tick();self.assertEqual(self.write_count,1)
        self.assertEqual(restarted.config(self.u)['last_skipped'],1)
    def test_token_renewal_without_browser_and_no_secret_in_view(self):
        self.enable();self.renew=True;self.execute_sync()
        self.assertEqual(self.auto.read(self.u,'auto-auth.json')['token'],'renewed-bearer')
        writes=[h for p,h,b,m in self.calls if p=='/api/data']
        self.assertTrue(all(h=={'Authorization':'Bearer renewed-bearer'} for h in writes))
        public=json.dumps(self.auto.view(self.u));self.assertNotIn('bearer',public);self.assertNotIn('synthetic',public)
        if os.name=='posix':self.assertEqual((self.u.path/'auto-auth.json').stat().st_mode&0o777,0o600)
    def test_disable_and_disconnect_credential_stops_jobs(self):
        self.enable();self.auto.disable(self.u);self.assertIsNone(self.execute_sync());self.assertEqual(self.write_count,0)
        self.assertFalse((self.u.path/'auto-auth.json').exists());self.assertFalse(self.auto.view(self.u)['enabled'])
    def test_revoked_session_pauses_without_writing(self):
        self.enable();self.denied=True;self.execute_sync();self.assertEqual(self.write_count,0)
        self.assertFalse(self.auto.view(self.u)['enabled']);self.assertEqual(self.auto.view(self.u)['last_status'],'error')
        self.assertFalse((self.u.path/'auto-auth.json').exists());self.assertFalse(self.u.busy)
    def test_wrong_profile_token_is_never_saved(self):
        original=self.auto.fetch
        def wrong(path,headers,body=None,method=None):
            code,data=original(path,headers,body,method)
            if path=='/api/pair/redeem':data['user']['id']='other'
            return code,data
        self.auto.fetch=wrong
        with self.assertRaises(SyncError):self.enable()
        self.assertFalse((self.u.path/'auto-auth.json').exists());self.assertEqual(self.write_count,0)
    def test_bad_page_and_network_error_preserve_profile_and_retry_later(self):
        self.enable();self.latest=[SAMPLE,SAMPLE];before=copy.deepcopy(self.state);self.execute_sync()
        self.assertEqual(self.state,before);self.assertEqual(self.write_count,0)
        self.assertEqual(self.auto.config(self.u)['next_run'],self.now+INTERVAL)
        self.assertEqual(self.auto.config(self.u)['last_status'],'error');self.assertEqual(self.u.ledger(),[])
    def test_lost_write_response_is_confirmed_next_hour_without_duplicate(self):
        self.enable()
        def lost_response(path,headers,body=None,method=None):
            result=self.api(path,headers,body,method)
            if path=='/api/data' and body is not None:raise server.Problem(502,'Resposta perdida')
            return result
        with patch.object(server,'request_json',side_effect=lost_response):self.auto.run(self.u)
        self.assertEqual(self.write_count,1);self.assertEqual(self.u.ledger(),[])
        self.assertEqual(self.auto.view(self.u)['last_status'],'error')
        self.now+=INTERVAL
        self.assertEqual(self.execute_sync(),{'added':0,'skipped':1})
        self.assertEqual(self.write_count,1);self.assertEqual(self.u.ledger(),['12345'])
    def test_unavailable_opengym_never_changes_state(self):
        self.enable();before=copy.deepcopy(self.state)
        with patch.object(server,'request_json',side_effect=server.Problem(502,'Indisponivel')):self.auto.run(self.u)
        self.assertEqual(self.state,before);self.assertEqual(self.u.ledger(),[])
        self.assertEqual(self.auto.view(self.u)['last_status'],'error')
        self.assertEqual(self.auto.config(self.u)['next_run'],self.now+INTERVAL)

    def test_manual_operation_is_not_interrupted(self):
        self.enable();self.u.busy=True;self.assertIsNone(self.execute_sync());self.assertEqual(self.write_count,0)
        self.u.busy=False
    def test_deleted_previous_import_is_not_recreated(self):
        self.u.save('imported.json',['12345']);self.enable();self.execute_sync()
        self.assertEqual(self.write_count,0);self.assertEqual(self.state,STATE)
    def test_profile_config_cannot_select_another_user(self):
        self.enable();self.u.save('auto-sync.json',self.auto.config(self.u)|{'uid':'other'})
        self.auto.tick();self.assertEqual(self.write_count,0)

if __name__=='__main__':unittest.main()
