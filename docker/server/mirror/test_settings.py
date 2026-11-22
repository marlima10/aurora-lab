import tempfile
import unittest
from pathlib import Path
import api
import settings

class SettingsTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.path=str(Path(self.temp.name)/'mirror.db');self.data=api.Data(self.path)
 def tearDown(self):self.temp.cleanup()
 def test_defaults_are_independent_and_preserve_existing_layout(self):
  a=settings.defaults();a['widgets']['clock']=False
  self.assertTrue(settings.defaults()['widgets']['clock']);self.assertEqual(self.data.settings()['order'],list(settings.WIDGETS))
 def test_settings_survive_reopen_without_changing_personal_data(self):
  self.data.save('person',{'action':'add','kind':'reminder','title':'Fixture'})
  p=settings.defaults();p['order'].reverse();p['temperatureUnit']='F';p['shortcuts']['javis']=False
  self.data.save_settings(p);reopened=api.Data(self.path)
  self.assertEqual(reopened.settings(),p);self.assertEqual(reopened.state('person')['entries'][0]['title'],'Fixture');self.assertEqual(reopened.state('other')['entries'],[])
 def test_cannot_hide_every_widget(self):
  p=settings.defaults();p['widgets']={k:False for k in settings.WIDGETS}
  with self.assertRaises(ValueError):self.data.save_settings(p)
  self.assertEqual(self.data.settings(),settings.defaults())
 def test_unknown_keys_urls_and_commands_are_rejected(self):
  for key in ('url','command','javascript','path'):
   p=settings.defaults();p[key]='https://example.test'
   with self.assertRaises(ValueError):settings.validate(p)
 def test_order_must_be_a_permutation(self):
  for order in (['clock']*7,list(settings.WIDGETS)[:-1],list(settings.WIDGETS)+['bad'],[{}]*7):
   p=settings.defaults();p['order']=order
   with self.assertRaises(ValueError):settings.validate(p)
 def test_numeric_limits_and_types(self):
  for key,value in (('fontScale',200),('refreshMinutes',1),('newsCount',True),('blur',17),('backgroundDim',-1),('panelOpacity','40')):
   p=settings.defaults();p[key]=value
   with self.assertRaises(ValueError):settings.validate(p)
if __name__=='__main__':unittest.main()
