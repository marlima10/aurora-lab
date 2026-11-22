"""TLS tunnel to the fixed Gemini and native free speech hosts. No decrypted traffic or credential logs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import select
import socket
import threading
import time

DESTINATIONS = {'generativelanguage.googleapis.com':443, 'speech.platform.bing.com':443}
SLOTS = threading.BoundedSemaphore(8)

def allowed(target):
    return target.lower() in {host+':443' for host in DESTINATIONS}

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args): pass
    def do_GET(self):
        self.send_response(200 if self.path=='/health' else 403)
        self.send_header('Content-Length','0');self.end_headers()
    def do_CONNECT(self):
        if not allowed(self.path):
            self.send_error(403,'Destination not allowed');return
        if not SLOTS.acquire(False):
            self.send_error(429,'Busy');return
        try:
            with socket.create_connection((self.path.lower().rsplit(':',1)[0],443),timeout=15) as remote:
                self.send_response(200,'Connection Established');self.end_headers()
                self.wfile.flush()
                sockets=[self.connection,remote];end=time.monotonic()+300
                while time.monotonic()<end:
                    readable,_,_=select.select(sockets,[],[],75)
                    if not readable:return
                    for source in readable:
                        data=source.recv(65536)
                        if not data:return
                        (remote if source is self.connection else self.connection).sendall(data)
        except (OSError,TimeoutError): pass
        finally:
            self.close_connection=True;SLOTS.release()

if __name__=='__main__':
    ThreadingHTTPServer(('0.0.0.0',3128),Handler).serve_forever()
