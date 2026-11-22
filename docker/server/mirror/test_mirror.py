import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import api

class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.data=api.Data(str(Path(self.tmp.name)/'test.db'))
    def tearDown(self):self.tmp.cleanup()
    def test_entries_and_goals_are_private(self):
        a=self.data.save('a',{'action':'add','kind':'event','title':'Treino','day':'2026-11-22'})
        self.assertEqual(self.data.state('b')['entries'],[])
        item=a['entries'][0]['id'];self.data.save('b',{'action':'delete','id':item})
        self.assertEqual(len(self.data.state('a')['entries']),1)
        self.data.save('a',{'action':'goals','sessions':3,'minutes':120,'calories':1000})
        self.assertIsNone(self.data.state('b')['goals'])
        self.assertEqual(self.data.state('a')['goals']['sessions'],3)
    def test_reminders_toggle_only_owner(self):
        result=self.data.save('a',{'action':'add','kind':'reminder','title':'Filamento'})
        id=result['entries'][0]['id'];self.data.save('b',{'action':'toggle','id':id})
        self.assertEqual(self.data.state('a')['entries'][0]['done'],0)
        self.data.save('a',{'action':'toggle','id':id})
        self.assertEqual(self.data.state('a')['entries'][0]['done'],1)
    def test_invalid_entries_and_goals(self):
        for value in ({'action':'add','kind':'event','title':'x','day':'invalid'},{'action':'add','kind':'reminder','title':''},{'action':'goals','sessions':True,'minutes':100,'calories':1000}):
            with self.assertRaises(ValueError):self.data.save('a',value)
    def test_weather_validates_coordinates_before_network(self):
        for lat,lon in ((float('nan'),0),(True,0),(91,0),(0,181)):
            with self.assertRaises(ValueError):api.weather(self.data,lat,lon)
    def test_unknown_calories_and_time_remain_unknown(self):
        day=api.dt.date.today().isoformat()
        fixture={'state':{'workouts':[{'d':day,'name':'Corrida','start':1000,'end':61000,'garminActivity':{}},{'d':day,'start':None,'end':None,'garminActivity':{'calories':150}}]}}
        with patch.object(api,'fetch',return_value=json.dumps(fixture).encode()):result=api.fitness({'opengymSecret':'fixture'},'user')
        self.assertEqual(result['workouts'][0]['minutes'],1)
        self.assertIsNone(result['workouts'][0]['calories'])
        self.assertIsNone(result['workouts'][1]['minutes'])
    def test_news_accepts_only_google_https_links(self):
        xml=b'<rss><channel><item><title>News</title><link>https://news.google.com/rss/articles/1</link></item><item><link>javascript:alert(1)</link></item></channel></rss>'
        with patch.object(api,'fetch',return_value=xml):result=api.news(self.data)
        self.assertEqual(len(result['items']),1)
if __name__=='__main__':unittest.main()
