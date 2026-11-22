import base64,hashlib,io,json,sqlite3,tarfile,tempfile,unittest
from contextlib import closing
from pathlib import Path
from sanitize_print_backups import sanitize

class RetiredArchiveTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def archive(self,rows):
  p=self.root/'mixed.tar.gz'
  with tarfile.open(p,'w:gz') as t:
   for name,value in rows.items():
    m=tarfile.TarInfo(name);m.size=len(value);t.addfile(m,io.BytesIO(value))
  return p
 def test_removes_app_data_and_credentials_preserving_other_bytes(self):
  retained=b'fixture-mealie-data';p=self.archive({'octoprint/uploads/job.gcode':b'fixture','config/docker/server/camera/Dockerfile':b'fixture','mealie/data.db':retained,'secrets/sso/apps.json':json.dumps({'octoprint':{'secret':'fixture-old'},'manyfold':{'secret':'fixture-retained'}}).encode()})
  result=sanitize(p);self.assertEqual(result['removed'],2)
  with tarfile.open(p) as t:
   self.assertEqual(t.extractfile('mealie/data.db').read(),retained)
   cfg=json.loads(t.extractfile('secrets/sso/apps.json').read());self.assertEqual(cfg,{'manyfold':{'secret':'fixture-retained'}})
 def test_no_change_keeps_original_archive_hash(self):
  p=self.archive({'opengym/profile.json':b'{"workouts":[]}'})
  before=p.read_bytes();self.assertEqual(sanitize(p)['status'],'unchanged');self.assertEqual(p.read_bytes(),before)
 def test_auth_sqlite_removes_only_retired_grants(self):
  db=self.root/'auth.sqlite3'
  with closing(sqlite3.connect(db)) as c:
   c.executescript("CREATE TABLE users(email TEXT,key_hash TEXT);CREATE TABLE grants(email TEXT,app TEXT,identity TEXT);INSERT INTO users VALUES('fixture','preserved-hash');INSERT INTO grants VALUES('fixture','octoprint','old');INSERT INTO grants VALUES('fixture','manyfold','retained');")
  p=self.archive({'sqlite-snapshots/auth/auth.sqlite3':db.read_bytes()});sanitize(p)
  with tarfile.open(p) as t:db.write_bytes(t.extractfile('sqlite-snapshots/auth/auth.sqlite3').read())
  with closing(sqlite3.connect(db)) as c:
   self.assertEqual(c.execute('SELECT app FROM grants').fetchall(),[('manyfold',)])
   self.assertEqual(c.execute('SELECT key_hash FROM users').fetchone()[0],'preserved-hash')
 def test_nested_archives_are_cleaned(self):
  inner=self.archive({'octoprint/config.yaml':b'fixture','actual/retained':b'other'}).read_bytes()
  p=self.archive({'backups/old.tar.gz':inner});sanitize(p)
  with tarfile.open(p) as t,tarfile.open(fileobj=io.BytesIO(t.extractfile('backups/old.tar.gz').read())) as nested:self.assertEqual(nested.getnames(),['actual/retained'])
 def test_legacy_host_keys_and_services_removed_but_models_preserved(self):
  p=self.archive({'etc/printserver-octoprint.key':b'fixture','etc/systemd/system/octoprint.service.save':b'fixture','etc/systemd/system/ustreamer.service':b'fixture','manyfold/models/camera_mount.stl':b'preserved-model'})
  sanitize(p)
  with tarfile.open(p) as t:self.assertEqual(t.getnames(),['manyfold/models/camera_mount.stl'])
 def test_vpn_identity_and_other_services_preserved(self):
  config={'TCP':{'5000':{'HTTPS':True},'443':{'HTTPS':True}},'Web':{'fixture:5000':{},'fixture:443':{}}}
  state={'_machinekey':'fixture-retained','_serve/fixture':base64.b64encode(json.dumps(config).encode()).decode()}
  p=self.archive({'tailscale/tailscaled.state':json.dumps(state).encode()});sanitize(p)
  with tarfile.open(p) as t:after=json.loads(t.extractfile('tailscale/tailscaled.state').read())
  self.assertEqual(after['_machinekey'],'fixture-retained');serving=json.loads(base64.b64decode(after['_serve/fixture']))
  self.assertEqual(set(serving['TCP']),{'443'});self.assertEqual(set(serving['Web']),{'fixture:443'})

if __name__=='__main__':unittest.main()
