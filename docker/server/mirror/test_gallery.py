import io,json,os,sqlite3,tempfile,unittest
from pathlib import Path
from PIL import Image
import api,settings
from gallery import Gallery,MAX_BYTES

def photo(fmt='PNG',color='navy',size=(640,480)):
 out=io.BytesIO();Image.new('RGB',size,color).save(out,format=fmt);return out.getvalue()

class GalleryTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'backgrounds';self.gallery=Gallery(self.root)
 def tearDown(self):self.tmp.cleanup()
 def test_upload_is_deduplicated_persistent_and_served_as_metadata_free_jpeg(self):
  result=self.gallery.upload(photo(),'../../foto.png');identifier=result['uploadedId']
  self.assertEqual(len(result['images']),1);self.assertNotIn('..',result['images'][0]['name'])
  self.assertTrue(self.gallery.upload(photo(),'outra.png')['duplicate'])
  reopened=Gallery(self.root);self.assertEqual(reopened.scan()['images'][0]['id'],identifier)
  with Image.open(io.BytesIO(reopened.image(identifier))) as image:self.assertEqual(image.format,'JPEG');self.assertEqual(len(image.getexif()),0)
  with Image.open(io.BytesIO(reopened.image(identifier,True))) as image:self.assertLessEqual(image.width,480)
 def test_high_resolution_jpeg_is_reduced_for_the_screen(self):
  item=self.gallery.upload(photo('JPEG',size=(8000,6000)))
  with Image.open(io.BytesIO(self.gallery.image(item['uploadedId']))) as image:self.assertLessEqual(image.width,2560);self.assertLessEqual(image.height,1600)
 def test_manual_folder_uploads_are_detected_and_non_images_ignored(self):
  (self.root/'paisagem.webp').write_bytes(photo('WEBP'));(self.root/'notes.txt').write_text('private')
  first=self.gallery.scan();self.assertEqual(len(first['images']),1);self.assertEqual(first['skipped'],1)
  (self.root/'paisagem.webp').unlink();self.assertEqual(self.gallery.scan()['images'],[])
  with self.assertRaises(FileNotFoundError):self.gallery.image(first['images'][0]['id'])
 def test_invalid_animated_oversized_and_path_traversal_are_rejected(self):
  for raw in [b'<svg><script>bad</script></svg>',b'not a photo',b'x'*(MAX_BYTES+1),photo(size=(8000,7000))]:
   with self.assertRaises(ValueError):self.gallery.upload(raw,'fake.jpg')
  animation=io.BytesIO();Image.new('RGB',(10,10),'red').save(animation,format='PNG',save_all=True,append_images=[Image.new('RGB',(10,10),'blue')])
  with self.assertRaises(ValueError):self.gallery.upload(animation.getvalue(),'animated.png')
  for identifier in ['../private','abc','https://example.test/a']:
   with self.assertRaises(ValueError):self.gallery.image(identifier)
  self.assertEqual(self.gallery.scan()['images'],[])
 def test_symlinks_are_never_images(self):
  target=Path(self.tmp.name)/'private.png';target.write_bytes(photo())
  try:os.symlink(target,self.root/'outside.png')
  except OSError:self.skipTest('Platform does not permit symlink creation')
  self.assertEqual(self.gallery.scan()['images'],[])
 def test_selection_survives_restart_and_legacy_preferences_gain_defaults(self):
  dbpath=Path(self.tmp.name)/'mirror.sqlite3';data=api.Data(str(dbpath))
  image=data.gallery.upload(photo())['uploadedId']
  value=settings.defaults()|{'backgroundMode':'slideshow','backgroundImages':[image],'backgroundSeconds':30}
  data.save('a',{'action':'add','kind':'reminder','title':'Keep me'});data.save_settings(value)
  again=api.Data(str(dbpath));self.assertEqual(again.settings(),value);self.assertEqual(again.state('a')['entries'][0]['title'],'Keep me')
  legacy=settings.defaults();legacy['fontScale']=110
  for key in ['backgroundMode','backgroundImages','backgroundSeconds']:legacy.pop(key)
  db=sqlite3.connect(dbpath);db.execute('UPDATE display_settings SET value=?',(json.dumps(legacy),));db.commit();db.close()
  upgraded=api.Data(str(dbpath)).settings();self.assertEqual(upgraded['fontScale'],110);self.assertEqual(upgraded['backgroundMode'],'default')
 def test_active_selection_must_exist_and_settings_are_bounded(self):
  data=api.Data(str(Path(self.tmp.name)/'db.sqlite3'))
  with self.assertRaises(ValueError):data.save_settings(settings.defaults()|{'backgroundMode':'fixed','backgroundImages':['a'*64]})
  for values in [{'backgroundSeconds':True},{'backgroundSeconds':14},{'backgroundSeconds':3601},{'backgroundMode':'url'},{'backgroundImages':['../a']},{'backgroundImages':['a'*64,'a'*64]}]:
   with self.assertRaises(ValueError):settings.validate(settings.defaults()|values)

if __name__=='__main__':unittest.main()
