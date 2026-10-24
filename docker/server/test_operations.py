from contextlib import closing
import hashlib, importlib.util, io, json, pathlib, sqlite3, tarfile, tempfile, unittest
from alerts import AlertStore
from restore_check import check_archive
class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_alert_confirmation_no_flood_recovery_and_persistence(self):
        a=AlertStore(self.root/'alerts.json');s={'opengym':'offline','disk':85};b={'status':'ok','time':'1970-01-01T00:00:00+00:00'}
        self.assertEqual(a.update(s,b,0)['active'],[]);self.assertEqual(len(a.update(s,b,30)['active']),2)
        self.assertEqual(len(a.update(s|{'disk':86},b,60)['events']),2)
        self.assertEqual(len(AlertStore(self.root/'alerts.json').view(61)['active']),2)
        self.assertEqual(a.update({'opengym':'online','disk':70},b,62)['active'],[]);self.assertEqual(len(a.view(62)['events']),4)
    def test_transient_failure_is_not_alerted_and_stale_backup_is(self):
        a=AlertStore(self.root/'a.json');a.update({'opengym':'offline'},{},0);a.update({'opengym':'online'},{},20);self.assertEqual(a.view(20)['events'],[])
        a.update({}, {},300);self.assertEqual(len(a.update({}, {},330)['active']),1)
    def archive(self, extra=None):
        db=self.root/'source.sqlite3'
        with closing(sqlite3.connect(db)) as c:c.execute('create table if not exists fixture (id integer)');c.commit()
        archive=self.root/'backup.tar.gz'
        with tarfile.open(archive,'w:gz') as t:
            t.add(db,arcname='sqlite-snapshots/fitness/fitness.sqlite3')
            value=b'{"workouts": [{"id": "fixture"}]}'
            item=tarfile.TarInfo('opengym/data/fixture.json');item.size=len(value);t.addfile(item,io.BytesIO(value))
            if extra:
                item=tarfile.TarInfo(extra);item.size=1;t.addfile(item,io.BytesIO(b'x'))
        return archive,hashlib.sha256(archive.read_bytes()).hexdigest()
    def test_restore_checks_bytes_sqlite_json_maps_snapshots_and_cleans_temporary(self):
        p,h=self.archive();seen=[]
        def probe(root):
            self.assertTrue((root/'fitness/fitness.sqlite3').exists());self.assertEqual(json.loads((root/'opengym/data/fixture.json').read_text())['workouts'][0]['id'],'fixture');seen.append(root);return {'health':True}
        result=check_archive(p,h,probe);self.assertEqual(result['sqlite_verified'],1);self.assertEqual(result['opengym_json_verified'],1);self.assertTrue(result['application_probe']['health']);self.assertFalse(seen[0].exists())
    def test_restore_refuses_bad_hash_and_traversal(self):
        p,h=self.archive();self.assertRaises(ValueError,check_archive,p,'0'*64)
        p,h=self.archive('../escape');self.assertRaises(ValueError,check_archive,p,h);self.assertFalse((self.root/'escape').exists())
    def test_restore_refuses_links_duplicate_and_invalid_json(self):
        for name,kind in [('link','link'),('opengym/data/fixture.json','duplicate'),('bad.json','json')]:
            p,h=self.archive()
            with tarfile.open(p,'r:gz') as t:members=[(m,t.extractfile(m).read()) for m in t if m.isfile()]
            with tarfile.open(p,'w:gz') as t:
                for m,value in members:t.addfile(m,io.BytesIO(value))
                m=tarfile.TarInfo(name)
                if kind=='link':m.type=tarfile.SYMTYPE;m.linkname='/etc/passwd';t.addfile(m)
                else:m.size=1;t.addfile(m,io.BytesIO(b'x'))
            h=hashlib.sha256(p.read_bytes()).hexdigest();self.assertRaises((ValueError,json.JSONDecodeError),check_archive,p,h)
if __name__=='__main__':unittest.main()
