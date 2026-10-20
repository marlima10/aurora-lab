"""Keep the AuroraServer running with its lid closed, without changing critical battery policy."""
import argparse,datetime as dt,json,os,pathlib,pwd,subprocess,tarfile
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--user',default='rafael');a=p.parse_args()
plan={'HandleLidSwitch':'ignore','HandleLidSwitchExternalPower':'ignore','HandleLidSwitchDocked':'ignore','IdleAction':'ignore'}
props={'lid-action-on-ac':0,'lid-action-on-battery':0,'inactivity-on-ac':0,'inactivity-on-battery':0}
print(json.dumps({'logind':plan,'xfce':props,'critical_battery_policy':'preserved'}))
if not a.apply:raise SystemExit(0)
assert os.geteuid()==0,'Execute como root.'
r=pathlib.Path(__file__).resolve().parents[3];user=pwd.getpwnam(a.user)
stage=r/'deploy-state'/('lid-before-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S'));stage.mkdir(mode=0o700)
xml=pathlib.Path(user.pw_dir)/'.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml'
with tarfile.open(stage/'config.tar.gz','w:gz') as t:
 for path in [pathlib.Path('/etc/systemd/logind.conf'),pathlib.Path('/etc/systemd/logind.conf.d'),xml]:
  if path.exists():t.add(path,arcname=str(path).lstrip('/'))
(stage/'config.tar.gz').chmod(0o600)
folder=pathlib.Path('/etc/systemd/logind.conf.d');folder.mkdir(exist_ok=True)
(folder/'90-auroralab-lid.conf').write_text('[Login]\n'+''.join(k+'='+v+'\n' for k,v in plan.items()))
base=['runuser','-u',a.user,'--','env','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/'+str(user.pw_uid)+'/bus','xfconf-query','-c','xfce4-power-manager']
previous={}
for key,value in props.items():
 prop='/xfce4-power-manager/'+key
 old=subprocess.run(base+['-p',prop],text=True,capture_output=True);previous[key]=old.stdout.strip() if old.returncode==0 else None
 command=base+['-p',prop,'-s',str(value)]
 if old.returncode:command+=['--create','-t','uint']
 subprocess.run(command,check=True)
 assert subprocess.check_output(base+['-p',prop],text=True).strip()==str(value),key
(stage/'xfce-properties.json').write_text(json.dumps(previous,indent=2))
subprocess.run(['systemctl','reload','systemd-logind'],check=True)
# Verify the effective merged system configuration. Physical close/open is a separate user check.
effective=subprocess.check_output(['systemd-analyze','cat-config','systemd/logind.conf'],text=True)
values={}
for line in effective.splitlines():
 if line.strip() and not line.lstrip().startswith(('#',';','[')) and '=' in line:
  k,v=line.split('=',1);values[k.strip()]=v.strip()
assert all(values.get(k)==v for k,v in plan.items()),'Politica efetiva de tampa divergente.'
record={'time':dt.datetime.now(dt.timezone.utc).isoformat(),'logind':plan,'xfce':props,'rollback':str(stage),'physical_lid_test':'pending','critical_battery_policy':'unchanged'}
(r/'deploy-state/lid-policy.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))