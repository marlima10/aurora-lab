import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
from urllib.parse import parse_qs, urlsplit
import personal_api
os.environ.setdefault('PUBLIC_ORIGIN','https://test.ts.net:8081')
import server
from test_garmin import SAMPLE

class OfficialAPI(unittest.TestCase):
    def test_exchange_authorization_headers_and_filtered_pagination(self):
        calls=[]
        def open_request(request,timeout):
            calls.append(request)
            data={'access_token':'synthetic-access'} if len(calls)==1 else [SAMPLE]
            return io.BytesIO(json.dumps(data).encode())
        client=personal_api.PersonalAPI('synthetic-key')
        with patch.object(client.opener,'open',side_effect=open_request):
            self.assertEqual(client.activities(0,100,'2026-01-01','2026-10-21'),[SAMPLE])
            client.activities(100,100,'2026-01-01','2026-10-21')
        self.assertEqual(len(calls),3)
        self.assertEqual(calls[0].method,'POST')
        self.assertIsNone(calls[0].get_header('Content-type'))
        self.assertEqual(calls[0].get_header('Accept'),'*/*')
        self.assertEqual(calls[1].get_header('Accept'),'application/json')
        self.assertEqual(calls[0].get_header('Authorization'),'ApiKey synthetic-key')
        self.assertEqual(calls[1].get_header('Authorization'),'Bearer synthetic-access')
        self.assertEqual(urlsplit(calls[1].full_url).hostname,'personal.connectapi.garmin.com')
        query=parse_qs(urlsplit(calls[2].full_url).query)
        self.assertEqual(query['start'],['100'])
        self.assertEqual(query['startDate'],['2026-01-01'])
        self.assertEqual(query['endDate'],['2026-10-21'])
        self.assertNotIn('synthetic',calls[0].full_url)

    def test_token_endpoint_accepts_plain_text_and_json_string(self):
        for payload in (b'synthetic.jwt.token', b'"synthetic.jwt.token"'):
            client=personal_api.PersonalAPI('synthetic-key')
            calls=[]
            def respond(request,timeout):
                calls.append(request)
                if len(calls)==1:
                    if request.get_header('Accept') != '*/*':
                        raise urllib.error.HTTPError(request.full_url,406,'Not Acceptable',{},None)
                    return io.BytesIO(payload)
                self.assertEqual(request.get_header('Authorization'),'Bearer synthetic.jwt.token')
                return io.BytesIO(b'[]')
            with self.subTest(payload=payload),patch.object(client.opener,'open',side_effect=respond):
                self.assertEqual(client.activities(0,1),[])

    def test_rejected_key_and_rate_limit_never_echo_sensitive_response(self):
        for status in (401,403,429,500):
            client=personal_api.PersonalAPI('synthetic-key')
            error=urllib.error.HTTPError('https://example.invalid',status,'synthetic-secret',{},None)
            with self.subTest(status=status),patch.object(client.opener,'open',side_effect=error):
                with self.assertRaises(personal_api.PersonalAPIError) as caught:client.authenticate()
                self.assertNotIn('synthetic',str(caught.exception))
                self.assertEqual(caught.exception.http_status,status)
                self.assertEqual(caught.exception.phase,'token')
        for invalid in ('', 'key\nHeader:injected', 'key with spaces', 'á'):
            with self.assertRaises(personal_api.PersonalAPIError):personal_api.PersonalAPI(invalid)

    def test_redirect_does_not_forward_credentials(self):
        import http.server,threading
        hits=[]
        class Redirect(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                hits.append(self.path);self.send_response(302)
                self.send_header('Location','/credential-leak');self.end_headers()
            def do_GET(self):hits.append(self.path);self.send_response(200);self.end_headers()
        http=http.server.ThreadingHTTPServer(('127.0.0.1',0),Redirect)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            with patch.object(personal_api,'BASE','http://127.0.0.1:'+str(http.server_port)):
                with self.assertRaises(personal_api.PersonalAPIError):personal_api.PersonalAPI('synthetic-key').authenticate()
            self.assertEqual(hits,[personal_api.TOKEN_PATH])
        finally:http.shutdown();http.server_close();thread.join()

class OfficialBridge(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=server.ROOT;server.ROOT=Path(self.tmp.name)
        self.user=server.User('synthetic-user')
    def tearDown(self):server.ROOT=self.old;self.tmp.cleanup()
    def test_key_saved_only_after_validated_and_absent_from_status(self):
        self.user.save('imported.json',['12345'])
        with patch.object(server.PersonalAPI,'activities',return_value=[]):server.connect_personal(self.user,'synthetic-key')
        self.assertEqual(self.user.view()['provider'],'personal')
        self.assertTrue(self.user.view()['connected'])
        self.assertNotIn('synthetic-key',json.dumps(self.user.view()))
        self.assertEqual(self.user.ledger(),['12345'])
        if os.name=='posix':self.assertEqual((self.user.path/'personal-api.json').stat().st_mode&0o777,0o600)
        with patch.object(server.PersonalAPI,'activities',side_effect=personal_api.PersonalAPIError('Recusada',http_status=400,phase='token')):
            with self.assertRaises(personal_api.PersonalAPIError):server.connect_personal(self.user,'synthetic-invalid')
        self.assertEqual(json.loads((self.user.path/'personal-api.json').read_text())['api_key'],'synthetic-key')
        diagnostic=json.loads((self.user.path/'personal-api-status.json').read_text())
        self.assertEqual(diagnostic['http_status'],400)
        self.assertEqual(diagnostic['phase'],'token')
        self.assertNotIn('synthetic',json.dumps(diagnostic))

    def test_official_preview_keeps_legacy_activity_ids_for_deduplication(self):
        self.user.save('personal-api.json',{'api_key':'synthetic-key'})
        self.user.save('imported.json',['12345'])
        with patch.object(server.PersonalAPI,'activities',return_value=[SAMPLE]):
            server.load(self.user,'2026-10-17','2026-10-18')
        self.assertEqual(self.user.preview[0]['activity_id'],'12345')
        self.assertTrue(self.user.view()['activities'][0]['imported'])

    def test_official_small_pages_read_all_records_and_do_not_truncate_early(self):
        self.user.save('personal-api.json',{'api_key':'synthetic-key'})
        rows=[SAMPLE|{'activityId':i} for i in range(55)]
        calls=[]
        def activities(offset,limit,first,last):
            self.assertLessEqual(limit,25)
            calls.append(offset)
            return rows[offset:offset+limit]
        with patch.object(server.PersonalAPI,'activities',side_effect=activities):
            server.load(self.user,'2026-10-17','2026-10-18')
        self.assertEqual(calls,[0,25,50])
        self.assertEqual(len(self.user.preview),55)
        self.assertFalse(self.user.truncated)

    def test_personal_post_requires_authentication_and_trusted_origin(self):
        import threading,urllib.request
        http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        try:
            for origin,status in (('https://evil.invalid',403),(server.ORIGIN,401)):
                request=urllib.request.Request('http://127.0.0.1:'+str(http.server_port)+'/garmin/personal',data=b'{"apiKey":"synthetic-key"}',headers={'Origin':origin})
                with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(request)
                self.assertEqual(caught.exception.code,status)
        finally:http.shutdown();http.server_close();thread.join()

if __name__=='__main__':unittest.main()
