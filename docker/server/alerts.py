"""Persistent, bounded portal alerts. No Docker socket, commands or external delivery."""
import datetime as dt
import json
from pathlib import Path

class AlertStore:
    def __init__(self, path):
        self.path = Path(path)
        try: self.state = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError): self.state = {}
        self.state.setdefault('active', {}); self.state.setdefault('events', [])
        self.pending = {}; self.started = None

    def update(self, status, backup, now, restore=None):
        self.started = self.started if self.started is not None else now
        desired = {}
        names = {'octoprint':'OctoPrint','webcam':'Câmera USB','nginx':'Portal','samba':'Arquivos Samba','cockpit':'Cockpit','homeboard':'HomeBoard','homeassistant':'Home Assistant','opengym':'openGym'}
        for key, name in names.items():
            if status.get(key) == 'offline': desired['service:'+key] = ('critical',name+' está indisponível.')
        disk = status.get('disk')
        if isinstance(disk,(int,float)) and disk >= 80: desired['disk'] = ('critical' if disk >= 90 else 'warning',f'Disco com {disk}% de uso; revise o espaço livre.')
        if backup.get('status') == 'error': desired['backup'] = ('critical','A última tentativa de backup falhou. Confira Backup & Dados.')
        else:
            try: age = now - dt.datetime.fromisoformat(backup.get('time','')).timestamp()
            except (ValueError,TypeError): age = None
            if (age is None and now-self.started >= 300) or (age is not None and age > 36*3600): desired['backup'] = ('warning','Backup ausente ou atrasado há mais de 36 horas.')
        if restore and restore.get('status') == 'error': desired['restore'] = ('critical','O teste de restauração do backup falhou. Confira Backup & Dados.')
        changed = False
        for key in set(self.pending) - set(desired): self.pending.pop(key,None)
        for key,(level,message) in desired.items():
            since = self.pending.setdefault(key,now)
            if now-since < 30: continue
            old = self.state['active'].get(key)
            # Text values can change every sample; alert once per severity transition.
            if not old or old['level'] != level:
                item = {'id':key,'level':level,'message':message,'time':dt.datetime.fromtimestamp(now,dt.timezone.utc).isoformat(),'state':'active'}
                self.state['active'][key]=item;self.state['events'].append(item.copy());changed=True
        for key in list(self.state['active']):
            if key not in desired:
                old = self.state['active'].pop(key)
                item = old | {'time':dt.datetime.fromtimestamp(now,dt.timezone.utc).isoformat(),'state':'resolved','message':'Resolvido: '+old['message']}
                self.state['events'].append(item);changed=True
        self.state['events'] = self.state['events'][-200:]
        if changed:
            tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.state,ensure_ascii=False),encoding='utf-8');tmp.replace(self.path)
        return self.view(now)

    def view(self, now):
        return {'generated':dt.datetime.fromtimestamp(now,dt.timezone.utc).isoformat(),'active':list(self.state['active'].values()),'events':list(reversed(self.state['events'])),'delivery':'portal','confirmation_seconds':30}
