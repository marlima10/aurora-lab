import importlib.util,json,os,pathlib,tempfile,unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('prepare_apps',pathlib.Path(__file__).parent/'apps/prepare_apps.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class AppsPreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name)
        (self.root/'.env').write_text('COMPOSE_FILE=compose.server.yaml:compose.printer.yaml\nOPENGYM_ORIGIN=https://example.tail123.ts.net:8081\nEXISTING_SECRET=fixture-do-not-change\nCOMPOSE_PROFILES=camera\n')
    def tearDown(self):self.tmp.cleanup()
    def prepare(self):
        with patch.object(module.os,'chown',create=True):return module.prepare(self.root)
    def test_idempotent_preserves_secrets_overlays_and_does_not_leak_credentials(self):
        first=self.prepare();creds=(self.root/'secrets/apps23-initial.json').read_bytes();key=(self.root/'secrets/manyfold.env').read_bytes();env=(self.root/'.env').read_bytes()
        self.assertNotIn('password',json.dumps(first));self.assertIn(b'compose.printer.yaml',env);self.assertIn(b'EXISTING_SECRET=fixture-do-not-change',env);self.assertIn(b'COMPOSE_PROFILES=camera',env)
        self.prepare();self.assertEqual(creds,(self.root/'secrets/apps23-initial.json').read_bytes());self.assertEqual(key,(self.root/'secrets/manyfold.env').read_bytes());self.assertEqual(env,(self.root/'.env').read_bytes())
        data=json.loads(creds);self.assertEqual(len({v['password'] for v in data.values()}),3);self.assertTrue(all(len(v['password'])>=32 for v in data.values()))
    def test_refuses_existing_application_data_without_install_credentials(self):
        folder=self.root/'data/actual';folder.mkdir(parents=True);(folder/'account.sqlite').write_bytes(b'fixture');before=(self.root/'.env').read_bytes();self.assertRaises(ValueError,self.prepare);self.assertEqual(before,(self.root/'.env').read_bytes())
    def test_rejects_unsafe_origin_before_changes(self):
        for origin in ['http://example.ts.net:8081','https://attacker.invalid:8081','https://u:p@example.ts.net:8081','https://example.ts.net:8081/path','https://example.ts.net:5000']:
            (self.root/'.env').write_text('COMPOSE_FILE=compose.server.yaml\nOPENGYM_ORIGIN='+origin+'\n');self.assertRaises(ValueError,self.prepare)
        self.assertFalse((self.root/'secrets/apps23-initial.json').exists())
class AppsPublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);(self.root/'deploy-state').mkdir()
        (self.root/'deploy-state/apps23-initialized.json').write_text(json.dumps({'manyfold':True,'mealie':True,'actual':True}))
        spec=importlib.util.spec_from_file_location('publish_apps',pathlib.Path(__file__).parent/'apps/publish_apps.py');self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
    def tearDown(self):self.tmp.cleanup()
    def test_preserves_previous_private_routes_without_reset_or_funnel(self):
        before={'TCP':{'443':{'HTTPS':True}},'Web':{'example:443':{'Handlers':{'/':{'Proxy':'http://127.0.0.1:80'}}}}};after=json.loads(json.dumps(before))
        for port in self.module.PORTS:after['TCP'][str(port)]={'HTTPS':True};after['Web']['example:'+str(port)]={'Handlers':{'/':{'Proxy':'http://127.0.0.1:'+str(port)}}}
        with patch.object(self.module.subprocess,'check_output',side_effect=[json.dumps(before).encode(),json.dumps(after).encode()]),patch.object(self.module.subprocess,'run') as run:
            run.return_value.returncode=0;result=self.module.publish(self.root)
            self.assertTrue(result['previous_routes_preserved']);self.assertFalse(result['funnel_enabled']);self.assertEqual(run.call_count,3)
            for call in run.call_args_list:self.assertNotIn('--reset',call.args[0]);self.assertNotIn('funnel',call.args[0])
    def test_refuses_uninitialized_accounts(self):
        (self.root/'deploy-state/apps23-initialized.json').write_text('{}')
        with patch.object(self.module.subprocess,'check_output') as query:self.assertRaises(ValueError,self.module.publish,self.root);query.assert_not_called()
    def test_does_not_overwrite_existing_unrelated_port(self):
        before={'TCP':{'3214':{'HTTPS':True}},'Web':{'example:3214':{'Handlers':{'/':{'Proxy':'http://127.0.0.1:1234'}}}}}
        with patch.object(self.module.subprocess,'check_output',return_value=json.dumps(before).encode()),patch.object(self.module.subprocess,'run') as run:self.assertRaises(ValueError,self.module.publish,self.root);run.assert_not_called()

if __name__=='__main__':unittest.main()
