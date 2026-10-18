import datetime as dt
import json
import os
import pathlib
import shutil
import socket
import subprocess
import struct
import fcntl
import ipaddress
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

PROC = pathlib.Path('/host/proc')
STATE = pathlib.Path('/state')
lock = threading.Lock()
latest = {}
history = []
previous = None
network_state = {'devices': [], 'total': 0, 'online': 0, 'offline': 0}

def text(path, default=''):
    try:
        return pathlib.Path(path).read_text().strip()
    except OSError:
        return default

def online(host, port):
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return 'online'
    except OSError:
        return 'offline'

def atomic(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False))
    tmp.replace(path)

def collect():
    global previous
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    mem = {row.split(':')[0]: int(row.split()[1]) for row in text(PROC/'meminfo').splitlines() if len(row.split()) >= 2 and row.split()[1].isdigit()}
    cpu = [int(v) for v in text(PROC/'stat').splitlines()[0].split()[1:9]]
    total, idle = sum(cpu), cpu[3]+cpu[4]
    usage = 0
    if previous and total > previous[0]:
        usage = round(100 * (1-(idle-previous[1])/(total-previous[0])), 1)
    previous = total, idle
    disk = shutil.disk_usage(STATE)
    temperatures = []
    for sensor in pathlib.Path('/host/sys/class/thermal').glob('thermal_zone*/temp'):
        try: temperatures.append(float(sensor.read_text())/1000)
        except (OSError, ValueError): pass
    temp = max((v for v in temperatures if 0 < v < 120), default=0)
    total_mem = mem.get('MemTotal', 1)
    available = mem.get('MemAvailable', mem.get('MemFree', 0))
    swap_total = mem.get('SwapTotal', 0)
    swap_used = swap_total-mem.get('SwapFree', 0)
    services = {name: online(host, port) for name,host,port in [('octoprint','127.0.0.1',5000),('webcam','127.0.0.1',8080),('nginx','127.0.0.1',80),('samba','127.0.0.1',445),('cockpit','127.0.0.1',9090),('casaos','127.0.0.1',81),('homeassistant','127.0.0.1',8123),('opengym','127.0.0.1',8081)]}
    data = dict(generated=now, hostname='AuroraServer', local_ip=os.environ.get('SERVER_IP','192.168.0.71'), tailscale_ip='Offline', uptime=f'{int(float(text(PROC/"uptime","0").split()[0])//3600)} h', os='Debian GNU/Linux 13 / containers', kernel=text(PROC/'sys/kernel/osrelease'), arch='x86_64', cpu_model=next((r.split(':',1)[1].strip() for r in text(PROC/'cpuinfo').splitlines() if r.startswith('model name')), 'Intel'), cores=os.cpu_count(), cpu=usage, memory=round(100*(total_mem-available)/total_mem), memory_total=total_mem//1024, memory_used=(total_mem-available)//1024, swap=round(100*swap_used/swap_total) if swap_total else 0, swap_total=swap_total//1024, swap_used=swap_used//1024, disk=round(100*disk.used/disk.total), disk_total=f'{disk.total/2**30:.1f} GiB', disk_used=f'{disk.used/2**30:.1f} GiB', disk_free=f'{disk.free/2**30:.1f} GiB', temperature=temp, load=text(PROC/'loadavg').split()[0], thresholds={'temperature':{'warn':75,'crit':85},'disk':{'warn':80,'crit':90}}, **services)
    data['opengym_url'] = os.environ.get('OPENGYM_ORIGIN','')
    data['tailscale'] = 'offline'
    data['printer'] = {'connected':False,'state':'Sem impressora conectada','usb':'offline','port':'','baudrate':0,'firmware':'--','tool':{'actual':0,'target':0},'bed':{'actual':0,'target':0},'job':{'file':'Nenhuma impressão','progress':0,'print_time':0,'print_time_left':0}}
    for key in ('octoprint_size','prints','uploads','timelapse','octo_logs','system_logs','apt_cache'):
        data[key] = 'Não medido'
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
            addr=fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s',b'tailscale0'))
            data['tailscale_ip']=socket.inet_ntoa(addr[20:24])
            data['tailscale']='online'
    except OSError: pass
    key=text('/run/secrets/octoprint-api.key')
    if key:
        def octo(endpoint):
            request=Request('http://127.0.0.1:5000/api/'+endpoint,headers={'X-Api-Key':key})
            with urlopen(request,timeout=1) as response: return json.load(response)
        try:
            p=octo('printer'); job=octo('job'); connection=octo('connection')
            current=connection.get('current',{})
            data['printer'].update(connected=True,state=p.get('state',{}).get('text','Operational'),port=current.get('port',''),baudrate=current.get('baudrate',0),usb='online')
            for name,source in [('tool','tool0'),('bed','bed')]:
                data['printer'][name]=p.get('temperature',{}).get(source,{'actual':0,'target':0})
            data['printer']['job']={'file':job.get('job',{}).get('file',{}).get('display') or 'Nenhuma impressão','progress':job.get('progress',{}).get('completion') or 0,'print_time':job.get('progress',{}).get('printTime') or 0,'print_time_left':job.get('progress',{}).get('printTimeLeft') or 0}
        except Exception: pass
    return data

def scan_network():
    global network_state
    known={}
    try:
        saved=json.loads(text(STATE/'network.json','{}'))
        known={d['ip']:d for d in saved.get('devices',[])}
    except (ValueError,KeyError): pass
    subnet=ipaddress.ip_network(os.environ.get('SERVER_IP','192.168.0.71')+'/24',strict=False)
    def ping(ip):
        try:
            return ip,subprocess.run(['ping','-c','1','-W','1',str(ip)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2).returncode==0
        except (OSError,subprocess.TimeoutExpired): return ip,False
    while True:
        now=dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            with ThreadPoolExecutor(max_workers=24) as pool:
                live={str(ip) for ip,alive in pool.map(ping,subnet.hosts()) if alive}
            neighbors=json.loads(subprocess.check_output(['ip','-j','neigh','show'],timeout=5))
            macs={d['dst']:d.get('lladdr','—') for d in neighbors if ipaddress.ip_address(d['dst']) in subnet}
            for ip in live:
                item=known.get(ip,{'ip':ip,'name':'','mac':'—'})
                item.update(online=True,last_seen=now,mac=macs.get(ip,item.get('mac','—')))
                if ip==os.environ.get('SERVER_IP'): item['name']='AuroraServer'
                known[ip]=item
            for ip,item in known.items(): item['online']=ip in live
            devices=sorted(known.values(),key=lambda d:ipaddress.ip_address(d['ip']))
            value={'generated':now,'subnet':str(subnet),'devices':devices,'total':len(devices),'online':len(live),'offline':len(devices)-len(live),'method':'ICMP; dispositivos que bloqueiam ping podem nao aparecer'}
            atomic(STATE/'network.json',value)
            with lock: network_state=value
        except Exception as exc: print('Falha na descoberta:',type(exc).__name__,flush=True)
        time.sleep(120)

def loop():
    global latest, history
    try:
        stored=json.loads(text(STATE/'history.json','[]'))
        history=stored if isinstance(stored,list) else []
    except ValueError: pass
    last_sample = 0
    while True:
        try:
            value = collect()
            with lock:
                latest = value
                if time.monotonic()-last_sample >= 60:
                    history.append(dict(time=value['generated'],cpu=value['cpu'],memory=value['memory'],swap=value['swap'],disk=value['disk'],temp=value['temperature'],load=value['load']))
                    history=history[-1440:]
                    atomic(STATE/'history.json', history)
                    last_sample = time.monotonic()
        except Exception as exc:
            print('Falha na coleta:', type(exc).__name__, flush=True)
        time.sleep(5)

class Handler(BaseHTTPRequestHandler):
    def power_proxy(self):
        path = self.path.split('?', 1)[0]
        if path not in ('/api/power', '/api/power/settings'):
            self.send_error(404)
            return
        headers = {}
        body = None
        if self.command == 'POST':
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self.send_error(400)
                return
            if not 0 < length <= 1024:
                self.send_error(413)
                return
            body = self.rfile.read(length)
            headers = {'Content-Type': self.headers.get('Content-Type', ''), 'Authorization': self.headers.get('Authorization', '')}
        request = Request('http://127.0.0.1:9110' + path, data=body, headers=headers, method=self.command)
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as exc:
            response = exc
        except (URLError, TimeoutError):
            payload = b'{"error":"Monitor de energia indisponivel."}'
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        with response:
            payload = response.read(1000000)
            self.send_response(response.code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def do_POST(self):
        self.power_proxy()

    def do_GET(self):
        if self.path.split('?', 1)[0].startswith('/api/power'):
            self.power_proxy()
            return
        name=self.path.split('?',1)[0].rsplit('/',1)[-1]
        with lock:
            if name=='status.json': result=latest.copy()
            elif name=='history.json': result=list(history)
            elif name=='network.json':
                result=network_state.copy()
            elif name=='diagnostics.json': result={'kernel':latest.get('kernel',''),'usb':'Dispositivos verificados na implantação.','serial':'Impressora USB ainda não conectada.','octoprint_logs':'Consultar docker compose logs octoprint no servidor.'}
            elif name=='fitness-backup.json':
                try: result=json.loads(text('/backup-status/fitness-backup.json','{}'))
                except ValueError: result={}
            else:
                self.send_error(404); return
        body=json.dumps(result,ensure_ascii=False).encode()
        self.send_response(200 if result else 503)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass

threading.Thread(target=loop,daemon=True).start()
threading.Thread(target=scan_network,daemon=True).start()
ThreadingHTTPServer(('0.0.0.0',9101),Handler).serve_forever()
