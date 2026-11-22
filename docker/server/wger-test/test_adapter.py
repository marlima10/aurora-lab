import unittest,os
from unittest.mock import patch,Mock
from django.test import RequestFactory
from django.http import HttpResponse
from aurora_sso import AuroraSsoMiddleware
class DelegatedLoginTest(unittest.TestCase):
 def test_external_headers_without_secret_are_denied(self):
  with patch.dict(os.environ,{'AURORA_PROXY_SECRET':'s'*64}),patch('aurora_sso.get_user_model') as model:
   request=RequestFactory().get('/',HTTP_X_AURORA_IDENTITY='aurora@server.local',HTTP_X_AURORA_LAB_SECRET='fake')
   result=AuroraSsoMiddleware(lambda r:HttpResponse('wrong'))(request)
   self.assertEqual(result.status_code,403);model.assert_not_called()
 def test_wrong_identity_is_denied(self):
  with patch.dict(os.environ,{'AURORA_PROXY_SECRET':'s'*64}),patch('aurora_sso.get_user_model') as model:
   request=RequestFactory().get('/',HTTP_X_AURORA_IDENTITY='other@example.test',HTTP_X_AURORA_LAB_SECRET='s'*64)
   self.assertEqual(AuroraSsoMiddleware(lambda r:HttpResponse('wrong'))(request).status_code,403);model.assert_not_called()
 def test_valid_delegation_preserves_native_page_and_marks_evaluation(self):
  with patch.dict(os.environ,{'AURORA_PROXY_SECRET':'s'*64}),patch('aurora_sso.get_user_model') as model:
   user=Mock();model.return_value.objects.filter.return_value.first.return_value=user
   request=RequestFactory().get('/',HTTP_X_AURORA_IDENTITY='aurora@server.local',HTTP_X_AURORA_LAB_SECRET='s'*64)
   result=AuroraSsoMiddleware(lambda r:HttpResponse('<html><body>native page</body></html>'))(request)
   self.assertIs(request.user,user);self.assertIn(b'native page',result.content);self.assertIn(b'AVALIA',result.content);self.assertEqual(result['Cache-Control'],'no-store')
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DelegatedLoginTest))
if not result.wasSuccessful():raise RuntimeError('Delegated login tests failed')
