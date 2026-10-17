import pathlib,re,py_compile,sysconfig
path=pathlib.Path(sysconfig.get_paths()['purelib'])/'octoprint_powerfailure/__init__.py'
source=path.read_text()
pattern=r'(?m)^([ \t]*)self\.timer\.cancel\(\)[ \t]*$'
source,count=re.subn(pattern,lambda m:m[1]+'if getattr(self, "timer", None) is not None:\n'+m[1]+'    self.timer.cancel()',source)
assert count==4,count
path.write_text(source); py_compile.compile(str(path),doraise=True)
from octoprint_powerfailure import PowerFailurePlugin
from types import SimpleNamespace
for has_timer in (False,True):
    plugin=object.__new__(PowerFailurePlugin)
    plugin.will_print=''
    plugin.recovery_settings={'powerloss':True}
    plugin._write_recovery_settings=lambda:None
    cancelled=[]
    if has_timer: plugin.timer=SimpleNamespace(cancel=lambda:cancelled.append(True))
    plugin.on_event('Error',{})
    assert plugin.recovery_settings['powerloss'] is False
    assert len(cancelled)==int(has_timer)
print('PowerFailure: evento Error testado com e sem timer.')
