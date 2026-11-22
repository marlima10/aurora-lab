import socket
import unittest
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import web_reader as web
from common import Problem

class WebTests(unittest.TestCase):
    def test_denies_private_and_rebinding_answers(self):
        for addresses in (['127.0.0.1'],['10.0.0.1'],['169.254.169.254'],['100.80.213.50'],['::1'],['::ffff:8.8.8.8'],['8.8.8.8','192.168.1.1']):
            answers=[(socket.AF_INET6 if ':' in ip else socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443)) for ip in addresses]
            with patch.object(web.socket,'getaddrinfo',return_value=answers),self.assertRaises(Problem):web.destination('https://public.example/page')
    def test_denies_credentials_ports_and_non_https(self):
        for url in ('http://example.org','https://localhost','https://host.local','https://server.ts.net','https://user:pass@example.org','https://example.org:8080','https://example.org/\nHost:x'):
            with self.assertRaises(Problem):web.destination(url)
    def test_returns_checked_address_and_real_hostname(self):
        row=(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))
        with patch.object(web.socket,'getaddrinfo',return_value=[row]):
            _,host,address=web.destination('https://example.org/data')
        self.assertEqual((host,address),('example.org',row))
    def test_html_scripts_are_data_not_executed_or_returned(self):
        parser=web.Text();parser.feed('<h1>Artigo</h1><script>secret</script><p>Texto</p>')
        self.assertEqual(parser.parts,['Artigo','Texto'])
    def test_redirect_to_internal_host_is_revalidated(self):
        class Response:
            status=302
            def getheader(self,name,*args):return 'https://localhost/private'
        class Connection:
            def __init__(self,*args):pass
            def request(self,*args,**kwargs):pass
            def getresponse(self):return Response()
            def close(self):pass
        row=(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))
        with patch.object(web.socket,'getaddrinfo',return_value=[row]),patch.object(web,'PinnedHTTPS',Connection),self.assertRaises(Problem):web.public_get('https://example.org/')
if __name__=='__main__':unittest.main()
