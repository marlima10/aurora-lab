import json
import unittest
from unittest.mock import patch
import mirror
class FacadeTests(unittest.TestCase):
    def test_client_cannot_choose_native_identity_or_owner(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'{}'
        session={'email':'owner@example.test','grants':{'portal':'owner@example.test','opengym':'native-profile'}}
        with patch.object(mirror.urllib.request,'urlopen',return_value=Response()) as call:
            mirror.query(session,{'_mirror_secret':'x'*48},'save',{'owner':'attacker','identity':'another','action':'add'})
        body=json.loads(call.call_args.args[0].data)
        self.assertEqual(body['owner'],'owner@example.test');self.assertEqual(body['identity'],'native-profile')
    def test_weather_cannot_override_identity_action_or_admin(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'{}'
        session={'email':'owner@example.test','grants':{'portal':'owner','opengym':'native'},'admin':False}
        malicious={'lat':1,'lon':2,'owner':'victim','identity':'other','action':'settings-save','admin':True,'value':{}}
        with patch.object(mirror.urllib.request,'urlopen',return_value=Response()) as call:
            mirror.query(session,{'_mirror_secret':'x'*48},'weather',malicious)
        body=json.loads(call.call_args.args[0].data)
        self.assertEqual(body['action'],'weather');self.assertEqual(body['owner'],session['email'])
        self.assertEqual(body['identity'],'native');self.assertIs(body['admin'],False)
        self.assertNotIn('value',body);self.assertNotIn('lat',body);self.assertNotIn('lon',body)

    def test_background_image_is_forwarded(self):
        class Response:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'fixture-image'
        session={'email':'owner@example.test','grants':{'portal':'owner'}}
        with patch.object(mirror.urllib.request,'urlopen',return_value=Response()) as call:
            self.assertEqual(mirror.image(session,{'_mirror_secret':'x'*48},'a'*64,thumb=True),(200,b'fixture-image'))
        self.assertTrue(call.call_args.args[0].full_url.endswith('/backgrounds/'+'a'*64+'/thumb'))
        self.assertEqual(call.call_args.kwargs['timeout'],20)

    def test_portal_grant_required(self):
        with self.assertRaises(ValueError):mirror.query({'email':'x','grants':{}},{},'state')
if __name__=='__main__':unittest.main()
