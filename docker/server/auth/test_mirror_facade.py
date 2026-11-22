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
    def test_portal_grant_required(self):
        with self.assertRaises(ValueError):mirror.query({'email':'x','grants':{}},{},'state')
if __name__=='__main__':unittest.main()
