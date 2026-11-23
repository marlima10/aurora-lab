import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import api
import settings
import holidays

class CalendarWeatherTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'mirror.db';self.data=api.Data(str(self.path))
 def tearDown(self):self.temp.cleanup()
 def test_city_and_week_survive_restart_without_touching_events(self):
  self.data.save('a',{'action':'add','kind':'event','day':'2028-02-29','title':'Meu evento'})
  prefs=settings.defaults()|{'calendarView':'week','holidayRegion':'BR-SP-JACAREI','weatherLocation':{'name':'Jacareí, SP','lat':-23.3,'lon':-45.97}}
  self.data.save_settings(prefs);other=api.Data(str(self.path))
  self.assertEqual(other.settings(),prefs);self.assertEqual(other.state('a')['entries'][0]['title'],'Meu evento')
  self.assertEqual(other.state('b')['entries'],[])
  self.assertEqual(len(other.state('a')['holidays']),70)
 def test_legacy_preferences_are_extended_without_resetting_them(self):
  prefs=settings.defaults();prefs['fontScale']=115;prefs['shortcuts']['actual']=False
  for key in ('weatherLocation','calendarView','holidayRegion'):prefs.pop(key)
  with sqlite3.connect(self.path) as db:db.execute('UPDATE display_settings SET value=?',(json.dumps(prefs),))
  db.close()
  newer=api.Data(str(self.path)).settings()
  self.assertEqual(newer['fontScale'],115);self.assertFalse(newer['shortcuts']['actual']);self.assertEqual(newer['calendarView'],'month')
 def test_holidays_are_idempotent_regional_and_separate_from_personal_entries(self):
  rows=holidays.catalogue();self.assertEqual(len(rows),70);self.assertEqual(len({r['id'] for r in rows}),70)
  for _ in range(3):api.Data(str(self.path))
  for region,count in [('BR',45),('BR-SP',50),('BR-SP-JACAREI',70),('none',0)]:
   self.data.save_settings(settings.defaults()|{'holidayRegion':region});state=self.data.state('a')
   self.assertEqual(len(state['holidays']),count);self.assertEqual(state['entries'],[])
  self.assertTrue(all('2026-01-01'<=r['day']<='2030-12-31' for r in rows))
  self.assertFalse(any('Carnaval' in r['title'] for r in rows))
 def test_moving_holidays_and_same_day_events(self):
  rows=holidays.catalogue()
  self.assertEqual([r['day'] for r in rows if r['title']=='Corpus Christi'],['2026-06-04','2027-05-27','2028-06-15','2029-05-31','2030-06-20'])
  same=[r['title'] for r in rows if r['day']=='2026-04-03'];self.assertEqual(set(same),{'Sexta-feira Santa','Aniversário de Jacareí'})
 def test_saved_weather_uses_the_saved_city_and_cache(self):
  prefs=settings.defaults()|{'weatherLocation':{'name':'Jacareí, SP','lat':-23.305,'lon':-45.966}}
  self.data.save_settings(prefs)
  with patch.object(api,'fetch',return_value=b'{"current":{},"daily":{}}') as fetch:
   self.assertEqual(api.saved_weather(self.data)['location'],'Jacareí, SP');api.saved_weather(self.data)
   self.assertEqual(fetch.call_count,1);self.assertIn('api.open-meteo.com/v1/forecast?',fetch.call_args.args[0])
  self.data.save_settings(settings.defaults())
  with self.assertRaises(ValueError):api.saved_weather(self.data)
 def test_location_search_is_bounded_cached_and_fixed_upstream(self):
  raw={'results':[{'name':'Jacareí','admin1':'São Paulo','country':'Brasil','latitude':-23.3,'longitude':-45.97}]}
  with patch.object(api,'fetch',return_value=json.dumps(raw).encode()) as fetch:
   result=api.locations(self.data,'Jacareí, SP');api.locations(self.data,'Jacareí, SP')
   self.assertEqual(result['locations'][0]['name'],'Jacareí, São Paulo, Brasil');self.assertEqual(fetch.call_count,1)
   self.assertTrue(fetch.call_args.args[0].startswith('https://geocoding-api.open-meteo.com/v1/search?'))
  for query in ('a','x'*101,'x\ny',None):
   with self.assertRaises(ValueError):api.locations(self.data,query)
 def test_bad_locations_and_view_cannot_be_saved(self):
  for loc in ({'name':'x','lat':True,'lon':0},{'name':'x','lat':91,'lon':0},{'name':'x','lat':float('nan'),'lon':0},{'name':'x','lat':1,'lon':2,'url':'https://evil.test'}):
   with self.assertRaises(ValueError):settings.validate(settings.defaults()|{'weatherLocation':loc})
  for field,value in [('calendarView','year'),('holidayRegion','unknown')]:
   with self.assertRaises(ValueError):settings.validate(settings.defaults()|{field:value})

if __name__=='__main__':unittest.main()
