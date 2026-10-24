import importlib.util
import json
import pathlib
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

spec = importlib.util.spec_from_file_location('power', pathlib.Path(__file__).with_name('power.py'))
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)

class PowerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        self.service = power.PowerService(*(str(self.root / n) for n in ('sys', 'cpu', 'backlight', 'state', 'proc')))
        self.service.state.mkdir()
        self.put('sys/class/power_supply/BAT1/type', 'Battery')
        for key, value in {'present': 1, 'capacity': 50, 'status': 'Discharging', 'voltage_now': 12000000, 'voltage_min_design': 12000000, 'current_now': 1500000, 'charge_now': 2000000, 'charge_full': 4000000, 'charge_full_design': 5000000, 'cycle_count': 100}.items():
            self.put('sys/class/power_supply/BAT1/' + key, value)
        self.put('sys/class/power_supply/AC/type', 'Mains')
        self.put('sys/class/power_supply/AC/online', 0)
        for key, value in {'scaling_governor':'powersave','scaling_available_governors':'powersave performance','energy_performance_preference':'balance_performance','energy_performance_available_preferences':'power balance_performance performance'}.items():
            self.put('cpu/cpufreq/policy0/' + key, value)
        self.put('cpu/intel_pstate/no_turbo', 0)
        self.put('backlight/brightness', 100)
        self.put('backlight/max_brightness', 100)
    def tearDown(self):
        self.temp.cleanup()
    def put(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(value))
    def test_battery_micro_units_and_health(self):
        battery = self.service.battery()
        self.assertEqual(battery['power_w'], 18)
        self.assertEqual(battery['energy_wh'], 24)
        self.assertEqual(battery['health_percent'], 80)
        self.assertEqual(battery['estimated_hours'], 1.33)
        self.assertFalse(battery['ac_online'])
    def test_charging_is_not_notebook_draw(self):
        self.put('sys/class/power_supply/BAT1/status', 'Charging')
        self.put('sys/class/power_supply/AC/online', 1)
        battery = self.service.battery()
        self.assertTrue(battery['ac_online'])
        self.assertIsNone(battery['estimated_hours'])
        result = self.service.collect()
        self.assertEqual(result['observed']['battery_discharge_kwh'], 0)
        self.assertIsNone(result['wall_power_w'])
    def test_missing_battery_not_zero(self):
        self.put('sys/class/power_supply/BAT1/present', 0)
        self.assertFalse(self.service.battery()['present'])
        self.assertNotIn('power_w', self.service.battery())
    def test_rapl_wrap_and_package_no_double_count(self):
        prefix = 'sys/class/powercap/intel-rapl/intel-rapl:0/'
        self.put(prefix+'name', 'package-0')
        self.put(prefix+'energy_uj', 9000000)
        self.put(prefix+'max_energy_range_uj', 10000000)
        self.assertIsNone(self.service.rapl(10)[0]['power_w'])
        self.put(prefix+'energy_uj', 1000000)
        self.assertEqual(self.service.rapl(12)[0]['power_w'], 1)
        self.assertIsNone(self.service.rapl(100)[0]['power_w'])
    def test_profiles_brightness_and_persistence(self):
        self.service.apply({'profile':'eco','brightness_percent':20})
        self.assertEqual(self.service.controls()['profile'], 'eco')
        self.assertEqual(self.service.controls()['brightness_percent'], 20)
        self.assertEqual(json.loads((self.service.state/'settings.json').read_text())['profile'], 'eco')
        self.service.apply({'profile':'balanced','brightness_percent':100})
        self.assertEqual(self.service.controls()['profile'], 'balanced')
    def test_reject_unsafe_parameters_before_write(self):
        for payload in ({'profile':'; reboot'}, {'brightness_percent':0}, {'brightness_percent':True}, {'brightness_percent':float('nan')}, {'suspend':True}, {'profile':'eco','brightness_percent':101}):
            with self.assertRaises(ValueError): self.service.apply(payload)
        self.assertEqual(self.service.controls()['profile'], 'balanced')
        self.assertEqual(self.service.controls()['brightness_percent'], 100)
    def test_manager_conflict_blocks_profile(self):
        self.put('proc/123/comm', 'power-profiles-d')
        with self.assertRaises(ValueError): self.service.apply({'profile':'eco'})
        self.assertEqual(self.service.controls()['profile'], 'balanced')
    def test_failed_save_rolls_back_hardware(self):
        (self.service.state/'settings.tmp').mkdir()
        with self.assertRaises(OSError): self.service.apply({'profile':'eco','brightness_percent':20})
        self.assertEqual(self.service.controls()['profile'], 'balanced')
        self.assertEqual(self.service.controls()['brightness_percent'], 100)
    def test_http_auth_and_allowlist(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),power.handler(self.service,'test-only-secret'))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url='http://127.0.0.1:'+str(server.server_port)+'/api/power/settings'
        try:
            for token, payload, expected in [('',{'profile':'eco'},401),('wrong',{'profile':'eco'},401),('test-only-secret',{'suspend':True},400)]:
                request=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
                with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(request)
                self.assertEqual(error.exception.code,expected)
            self.assertEqual(self.service.controls()['profile'],'balanced')
            request=urllib.request.Request(url,data=b'{"profile":"eco"}',headers={'Content-Type':'application/json','Authorization':'Bearer test-only-secret'})
            with urllib.request.urlopen(request) as response: self.assertTrue(json.load(response)['ok'])
            self.assertEqual(self.service.controls()['profile'],'eco')
        finally:
            server.shutdown();server.server_close();thread.join()

class EnergyHistoryTests(unittest.TestCase):
    def test_daily_rollover_gaps_separate_scopes_and_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=pathlib.Path(tmp);service=power.PowerService(state=tmp)
            battery={'status':'Discharging','power_w':20}
            service.record_energy('2026-10-23',0,10,battery);service.record_energy('2026-10-23',10,10,battery)
            self.assertAlmostEqual(service.meter['cpu_kwh'],10*10/3600000)
            service.record_energy('2026-10-23',1000,10,battery)
            self.assertEqual(service.meter['cpu_seconds'],10)
            service.record_energy('2026-10-24',1005,10,battery)
            self.assertEqual(service.meter['cpu_seconds'],0);self.assertEqual(service.daily['2026-10-23']['battery_seconds'],10)
            service.record_energy('2026-10-24',1010,None,{'status':'Charging','power_w':20})
            self.assertEqual(service.meter['battery_seconds'],0)
            power.write_json(state/'energy.json',service.meter);power.write_json(state/'daily-energy.json',list(service.daily.values()))
            again=power.PowerService(state=tmp);again.record_energy('2026-10-24',5000,100,battery)
            self.assertEqual(again.meter['cpu_seconds'],0);self.assertEqual(len(again.daily),2)
    def test_retention_90_days_and_missing_sensor_not_zero_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            service=power.PowerService(state=tmp)
            for n in range(100):
                day=(power.dt.date(2026,1,1)+power.dt.timedelta(days=n)).isoformat();service.record_energy(day,n*100,None,{})
            self.assertEqual(len(service.daily),90);self.assertEqual(service.meter['cpu_seconds'],0)

if __name__=='__main__':
    unittest.main()
