import datetime as dt
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
import agenda
import api


class AgendaTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'mirror.db';self.data=api.Data(str(self.path))
        self.range={'start':'2026-11-23','end':'2026-11-29'}
    def tearDown(self):self.tmp.cleanup()
    def test_timed_reminders_edit_and_owner_isolation(self):
        a=self.data.save('a',{'action':'add','kind':'reminder','title':'Consulta','day':'2026-11-25','time':'14:30'})['entries'][0]
        self.assertEqual(a['time'],'14:30');self.assertEqual(self.data.state('b')['entries'],[])
        with self.assertRaises(ValueError):self.data.save('b',{'action':'edit','id':a['id'],'kind':'event','title':'Roubado','day':'2026-11-25'})
        self.data.save('a',{'action':'edit','id':a['id'],'kind':'reminder','title':'Consulta alterada','day':'2026-11-26','time':'15:00'})
        saved=api.Data(str(self.path)).state('a')['entries'][0];self.assertEqual(saved['id'],a['id']);self.assertEqual(saved['time'],'15:00')
    def test_legacy_database_migration_preserves_rows_and_is_idempotent(self):
        path=Path(self.tmp.name)/'legacy.db'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE entries(id TEXT PRIMARY KEY,owner TEXT NOT NULL,kind TEXT NOT NULL,title TEXT NOT NULL,day TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0)')
            db.execute("INSERT INTO entries VALUES('original','a','reminder','Preservado','',1)")
        db.close()
        for _ in range(2):
            value=api.Data(str(path)).state('a')['entries'][0]
            self.assertEqual(value,dict(id='original',kind='reminder',title='Preservado',day='',done=1,time=''))
    def test_invalid_dates_hours_and_range(self):
        for day,clock in [('', '12:00'),('2026-11-25','24:00'),('2026-11-25','12:60'),('2026-02-30','12:00'),('2026-1-1','12:00'),(None,'')]:
            with self.assertRaises((ValueError,TypeError)):self.data.save('a',{'action':'add','kind':'reminder','title':'x','day':day,'time':clock})
        for value in [{'start':'2026-11-23','end':'2027-01-04'},{'start':'2026-11-25','end':'2026-11-23'},{'start':'2026-1-1','end':'2026-01-02'}]:
            with self.assertRaises(ValueError):agenda.date_range(value)
        self.assertEqual((agenda.date_range({'start':'2026-11-01','end':'2026-12-12'})[1]-dt.date(2026,11,1)).days,41)
    def test_native_schedule_week_override_rest_and_queue_pins(self):
        state={'routines':[{'id':'a','name':'A'},{'id':'b','name':'B'},{'id':'c','name':'C'}],'week':{'2':['a','gone','b']},'dayPlan':{},'workouts':[]}
        today='2026-11-24';self.assertEqual(agenda.planned_ids(state,today,today),['a','b'])
        state['dayPlan'][today]='rest';self.assertEqual(agenda.planned_ids(state,today,today),[])
        state['dayPlan'][today]='c';self.assertEqual(agenda.planned_ids(state,today,today),['c'])
        state['dayPlan']={'2026-11-25':'a'};state['queue']={'ids':['a','c'],'since':1,'startsOn':'2026-11-24'}
        self.assertEqual(agenda.planned_ids(state,today,today),['c','b'])
        self.assertEqual(agenda.planned_ids(state,'2026-11-25',today),['a'])
        self.assertEqual(agenda.planned_ids(state,'2026-11-26',today),[])
        state['workouts']=[{'routineId':'a','start':1000,'d':today,'name':'A'}]
        self.assertEqual(agenda.planned_ids(state,'2026-11-25',today),[])
    def test_queue_done_rule_strict_and_combined_names(self):
        state={'routines':[{'id':'a','name':'Push + Pull'},{'id':'b','name':'B'}],'week':{},'dayPlan':{},'queue':{'ids':['a','b'],'since':2000,'startsOn':'2026-11-24'},'workouts':[{'routineIds':['a'],'start':1000,'d':'2026-11-24','name':'Push + Pull + Core'}]}
        self.assertEqual(agenda.planned_ids(state,'2026-11-24','2026-11-24'),['b'])
        state['queue']['strict']=True;self.assertEqual(agenda.planned_ids(state,'2026-11-24','2026-11-24'),['a'])
    def test_mealie_pagination_fixed_endpoint_and_household_identity(self):
        calls=[]
        def fetch(url,headers):
            calls.append((url,headers));page=2 if 'page=2' in url else 1
            return json.dumps({'total_pages':2,'items':[{'id':page,'date':'2026-11-25','entryType':'lunch','recipe':{'name':'Receita '+str(page)}}]}).encode()
        rows=agenda.meals(fetch,'secret','native-user',dt.date(2026,11,23),dt.date(2026,11,29))
        self.assertEqual(len(rows),2);self.assertEqual(rows[0]['status'],'Almoço');self.assertEqual(calls[0][1]['X-Aurora-Identity'],'native-user')
        self.assertTrue(calls[0][0].startswith('http://mealie:9000/api/households/mealplans?start_date=2026-11-23&end_date=2026-11-29'))
    def test_partial_failure_does_not_hide_personal_entries(self):
        self.data.save('a',{'action':'add','kind':'event','title':'Pessoal','day':'2026-11-25','time':'09:00'})
        def unavailable(*args):raise OSError('private diagnostic')
        value=agenda.collect(self.data,{'opengymSecret':'secret'},dict(owner='a',identity='gym',mealieIdentity=None,value=self.range),unavailable)
        self.assertEqual(value['items'][0]['title'],'Pessoal');self.assertEqual([s['status'] for s in value['sources']],['unavailable','unauthorized'])
        self.assertNotIn('private diagnostic',json.dumps(value))
    def test_missing_mealie_secret_is_unauthorized_without_request(self):
        def fetch(url,headers):
            if 'mealie' in url:raise AssertionError('Mealie não deveria ser consultado')
            return json.dumps({'state':{}}).encode()
        value=agenda.collect(self.data,{'opengymSecret':'secret','mealieSecret':''},dict(owner='a',identity='gym',mealieIdentity='meal',value=self.range),fetch)
        self.assertEqual([s['status'] for s in value['sources']],['ok','unauthorized'])
    def test_cache_is_partitioned_by_native_identity_and_range(self):
        calls=[]
        def fetch(url,headers):
            calls.append(headers['X-Aurora-Identity']);return json.dumps({'state':{'workouts':[{'id':headers['X-Aurora-Identity'],'d':'2026-11-24','name':headers['X-Aurora-Identity']}]}}).encode()
        cfg={'opengymSecret':'secret'}
        for identity in ['native-a','native-a','native-b']:
            result=agenda.collect(self.data,cfg,dict(owner=identity,identity=identity,value=self.range),fetch)
            self.assertEqual(result['items'][0]['title'],identity)
        self.assertEqual(calls,['native-a','native-b'])
    def test_completed_and_future_plans_are_distinct_without_invented_past(self):
        state={'routines':[{'id':'r','name':'Força'}],'week':{'1':'r'},'dayPlan':{},'workouts':[{'id':'w','d':'2026-11-23','name':'Corrida','start':1795446000000}]}
        rows=agenda.workouts(state,dt.date(2026,11,16),dt.date(2026,11,30),'2026-11-24')
        self.assertEqual([(r['day'],r['status']) for r in rows],[('2026-11-23','Realizado'),('2026-11-30','Planejado')])

if __name__=='__main__':unittest.main()
