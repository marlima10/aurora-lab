"""Read Linux energy sensors; authenticated, allowlisted CPU/backlight controls."""
import datetime as dt
import hmac
import json
import math
import os
import pathlib
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROFILES = {
    'eco': ('powersave', 'power', '1'),
    'balanced': ('powersave', 'balance_performance', '0'),
    'performance': ('performance', 'performance', '0'),
}

def read(path, default=''):
    try:
        return pathlib.Path(path).read_text().strip()
    except OSError:
        return default


def number(path):
    try:
        value = float(read(path))
        return value if math.isfinite(value) else None
    except ValueError:
        return None


def ratio(value, divisor):
    return round(value / divisor, 3) if value is not None else None


def write_json(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False))
    tmp.chmod(0o600)
    tmp.replace(path)


class PowerService:
    def __init__(self, sysroot='/host/sys', cpu='/host/cpu', backlight='/host/backlight', state='/state', proc='/host/proc'):
        self.sys = pathlib.Path(sysroot)
        self.cpu = pathlib.Path(cpu)
        self.backlight = pathlib.Path(backlight)
        self.state = pathlib.Path(state)
        self.proc = pathlib.Path(proc)
        self.lock = threading.RLock()
        self.latest = {}
        self.previous = {}
        self.history = []
        self.last_history = 0
        self.last_save = 0
        self.last_sample = None
        try:
            self.meter = json.loads(read(self.state / 'energy.json', '{}'))
        except ValueError:
            self.meter = {}
        try:
            self.history = json.loads(read(self.state / 'history.json', '[]'))[-1440:]
        except (ValueError, TypeError):
            self.history = []

    def battery(self):
        supplies = self.sys / 'class/power_supply'
        ac = [read(p / 'online') == '1' for p in supplies.glob('*') if read(p / 'type') in ('Mains', 'USB', 'USB_C')]
        result = {'present': False, 'ac_online': any(ac) if ac else None}
        for path in supplies.glob('*'):
            if read(path / 'type') != 'Battery' or read(path / 'present', '1') == '0':
                continue
            voltage = number(path / 'voltage_now')
            design_voltage = number(path / 'voltage_min_design') or voltage
            power = number(path / 'power_now')
            current = number(path / 'current_now')
            if power is None and current is not None and voltage is not None:
                power = abs(current * voltage) / 1e6  # microwatts
            energy = number(path / 'energy_now')
            full = number(path / 'energy_full')
            design = number(path / 'energy_full_design')
            if design_voltage:
                charge, capacity, nominal = (number(path / key) for key in ('charge_now', 'charge_full', 'charge_full_design'))
                energy = energy if energy is not None else charge * design_voltage / 1e6 if charge is not None else None
                full = full if full is not None else capacity * design_voltage / 1e6 if capacity is not None else None
                design = design if design is not None else nominal * design_voltage / 1e6 if nominal is not None else None
            status = read(path / 'status', 'Unknown')
            watts = ratio(abs(power), 1e6) if power is not None else None
            result.update(present=True, name=path.name, percent=number(path / 'capacity'), status=status,
                          power_w=watts, energy_wh=ratio(energy, 1e6), full_wh=ratio(full, 1e6),
                          health_percent=round(100 * full / design, 1) if full is not None and design else None,
                          cycles=number(path / 'cycle_count'),
                          estimated_hours=round(energy / 1e6 / watts, 2) if status == 'Discharging' and energy is not None and watts and watts > 0.1 else None)
            break
        return result

    def rapl(self, now):
        values = []
        paths = self.sys.glob('class/powercap/intel-rapl/intel-rapl:*')
        for path in paths:
            name = read(path / 'name')
            if not (name.startswith('package-') or name in ('psys', 'uncore')):
                continue
            energy = number(path / 'energy_uj')
            maximum = number(path / 'max_energy_range_uj')
            key = str(path.resolve())
            previous = self.previous.get(key)
            watts = None
            if energy is not None and previous and 0 < now - previous[0] <= 30:
                delta = energy - previous[1]
                if delta < 0 and maximum:
                    delta += maximum
                if delta >= 0:
                    candidate = delta / (now - previous[0]) / 1e6
                    if 0 <= candidate <= 500:
                        watts = round(candidate, 3)
            if energy is not None:
                self.previous[key] = (now, energy)
            values.append({'name': name, 'power_w': watts})
            # Integrated GPU domain is a subzone; never add it to package total.
            for child in path.glob('intel-rapl:*'):
                if read(child / 'name') != 'uncore':
                    continue
                counter = number(child / 'energy_uj')
                childkey = str(child.resolve())
                old = self.previous.get(childkey)
                w = None
                if counter is not None and old and 0 < now - old[0] <= 30:
                    delta = counter - old[1]
                    if delta < 0:
                        delta += number(child / 'max_energy_range_uj') or 0
                    if delta >= 0:
                        w = delta / (now - old[0]) / 1e6
                if counter is not None:
                    self.previous[childkey] = (now, counter)
                values.append({'name': 'integrated_gpu', 'power_w': round(w, 3) if w is not None and w <= 200 else None})
        return values

    def gpus(self, domains):
        result = []
        igpu_power = next((d['power_w'] for d in domains if d['name'] == 'integrated_gpu'), None)
        for card in sorted(self.sys.glob('class/drm/card*')):
            if not re.fullmatch(r'card\d+', card.name):
                continue
            device = card / 'device'
            vendor, model = read(device / 'vendor'), read(device / 'device')
            driver = (device / 'driver').resolve().name if (device / 'driver').exists() else 'desconhecido'
            integrated = vendor == '0x8086'
            name = {('0x10de', '0x174e'): 'GeForce MX110', ('0x8086', '0x5917'): 'Intel UHD Graphics 620'}.get((vendor, model), ('Intel' if integrated else 'GPU') + ' ' + model)
            watts, temperature = None, None
            for hw in device.glob('hwmon/hwmon*'):
                watts = ratio(number(hw / 'power1_input'), 1e6)
                temperature = ratio(number(hw / 'temp1_input'), 1000)
            if watts is None and integrated:
                watts = igpu_power
            busy = number(device / 'gpu_busy_percent')
            result.append({'id': card.name, 'name': name, 'driver': driver, 'runtime_status': read(device / 'power/runtime_status', 'unknown'),
                           'utilization_percent': busy, 'power_w': watts, 'temperature_c': temperature,
                           'power_source': 'RAPL gráfico integrado' if integrated and igpu_power is not None else 'sensor hwmon' if watts is not None else None,
                           'reason': 'O driver não expõe watts/uso neste hardware.' if watts is None and busy is None else None})
        return result

    def manager(self):
        for process in self.proc.glob('[0-9]*/comm'):
            name = read(process)
            if name in ('power-profiles-d', 'tlp', 'tlp-rdw'):
                return name
        return None

    def controls(self):
        policies = sorted(self.cpu.glob('cpufreq/policy*'))
        managed = self.manager()
        governor = read(policies[0] / 'scaling_governor') if policies else ''
        preference = read(policies[0] / 'energy_performance_preference') if policies else ''
        turbo = read(self.cpu / 'intel_pstate/no_turbo')
        profile = next((key for key, values in PROFILES.items() if values == (governor, preference, turbo)), 'custom')
        maximum = number(self.backlight / 'max_brightness')
        current = number(self.backlight / 'brightness')
        return {'profile': profile, 'governor': governor, 'preference': preference, 'turbo_enabled': turbo == '0',
                'profiles_available': bool(policies) and not managed and all((p / 'energy_performance_preference').exists() for p in policies) and (self.cpu / 'intel_pstate/no_turbo').exists(),
                'manager': managed, 'brightness_percent': round(100 * current / maximum) if maximum and current is not None else None,
                'brightness_available': bool(maximum), 'night_schedule_enabled': False, 'rtc_test_required': True}

    def apply(self, payload):
        if not isinstance(payload, dict) or not payload or set(payload) - {'profile', 'brightness_percent'}:
            raise ValueError('Configuração inválida.')
        changes = []
        controls = self.controls()
        if 'profile' in payload:
            profile = payload['profile']
            if not isinstance(profile, str) or profile not in PROFILES:
                raise ValueError('Escolha um perfil válido.')
            if not controls['profiles_available']:
                raise ValueError('Perfis indisponíveis ou gerenciados por outro serviço.')
            governor, preference, turbo = PROFILES[profile]
            for policy in sorted(self.cpu.glob('cpufreq/policy*')):
                if governor not in read(policy / 'scaling_available_governors').split() or preference not in read(policy / 'energy_performance_available_preferences').split():
                    raise ValueError('Perfil não suportado pelo processador.')
                changes.extend([(policy / 'scaling_governor', governor), (policy / 'energy_performance_preference', preference)])
            changes.append((self.cpu / 'intel_pstate/no_turbo', turbo))
        if 'brightness_percent' in payload:
            percent = payload['brightness_percent']
            if type(percent) not in (int, float) or not math.isfinite(percent) or not 5 <= percent <= 100 or not controls['brightness_available']:
                raise ValueError('O brilho deve estar entre 5% e 100%.')
            maximum = number(self.backlight / 'max_brightness')
            changes.append((self.backlight / 'brightness', str(max(1, round(maximum * percent / 100)))))
        originals = [(path, read(path)) for path, _ in changes]
        try:
            for path, value in changes:
                path.write_text(value + '\n')
            settings = json.loads(read(self.state / 'settings.json', '{}'))
            settings.update(payload)
            write_json(self.state / 'settings.json', settings)
        except Exception:
            for path, value in originals:
                try:
                    path.write_text(value + '\n')
                except OSError:
                    pass
            raise
        return self.controls()

    def collect(self):
        now = time.monotonic()
        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
        battery = self.battery()
        domains = self.rapl(now)
        cpu_w = next((d['power_w'] for d in domains if d['name'].startswith('package-')), None)
        gpus = self.gpus(domains)
        day = dt.datetime.now().date().isoformat()
        if self.meter.get('day') != day:
            self.meter = {'day': day, 'cpu_kwh': 0.0, 'battery_discharge_kwh': 0.0, 'cpu_seconds': 0, 'battery_seconds': 0}
        elapsed = now - self.last_sample if self.last_sample is not None else 0
        # Ignore downtime/suspend gaps; do not extrapolate missing samples.
        if 0 < elapsed <= 30:
            if cpu_w is not None:
                self.meter['cpu_kwh'] += cpu_w * elapsed / 3600000
                self.meter['cpu_seconds'] += elapsed
            if battery.get('status') == 'Discharging' and battery.get('power_w') is not None:
                self.meter['battery_discharge_kwh'] += battery['power_w'] * elapsed / 3600000
                self.meter['battery_seconds'] += elapsed
        self.last_sample = now
        if now - self.last_history >= 60:
            self.history.append({'time': timestamp, 'cpu_w': cpu_w, 'battery_w': battery.get('power_w') if battery.get('status') == 'Discharging' else None})
            self.history = self.history[-1440:]
            self.last_history = now
        self.latest = {'generated': timestamp, 'battery': battery, 'cpu': {'power_w': cpu_w, 'source': 'Intel RAPL / pacote CPU'},
                       'gpus': gpus, 'controls': self.controls(), 'observed': self.meter.copy(), 'history': self.history[-180:],
                       'wall_power_w': None, 'wall_measurement_available': False}
        if now - self.last_save >= 60:
            write_json(self.state / 'energy.json', self.meter)
            write_json(self.state / 'history.json', self.history)
            self.last_save = now
        return self.latest

    def worker(self):
        saved = read(self.state / 'settings.json')
        if saved:
            try:
                self.apply(json.loads(saved))
            except (OSError, ValueError) as exc:
                print('Perfil salvo não aplicado:', type(exc).__name__, flush=True)
        while True:
            try:
                with self.lock:
                    self.collect()
            except Exception as exc:
                print('Falha na leitura de energia:', type(exc).__name__, flush=True)
            time.sleep(5)


def handler(service, token):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, data):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path.split('?', 1)[0] != '/api/power':
                self.respond(404, {'error': 'Não encontrado.'})
                return
            with service.lock:
                self.respond(200 if service.latest else 503, service.latest or {'error': 'Aguardando primeira coleta.'})

        def do_POST(self):
            if self.path != '/api/power/settings':
                self.respond(404, {'error': 'Não encontrado.'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 1024:
                    self.respond(413, {'error': 'Requisição inválida.'})
                    return
                self.connection.settimeout(10)
                raw = self.rfile.read(size)
            except (ValueError, OSError):
                self.respond(400, {'error': 'Requisição inválida.'})
                return
            supplied = self.headers.get('Authorization', '')
            if not token or not hmac.compare_digest(supplied.encode(), ('Bearer ' + token).encode()):
                self.respond(401, {'error': 'Chave administrativa inválida.'})
                return
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                self.respond(415, {'error': 'Envie JSON.'})
                return
            try:
                payload = json.loads(raw)
                with service.lock:
                    result = service.apply(payload)
                    if service.latest:
                        service.latest['controls'] = result
                self.respond(200, {'ok': True, 'controls': result})
            except (ValueError, TypeError):
                self.respond(400, {'error': 'Configuração inválida ou indisponível.'})
            except OSError:
                self.respond(503, {'error': 'Não foi possível aplicar. Configuração anterior restaurada.'})

        def log_message(self, *_):
            pass
    return Handler


if __name__ == '__main__':
    os.umask(0o077)
    service = PowerService()
    service.state.mkdir(parents=True, exist_ok=True)
    token = read('/run/secrets/power-admin.key')
    threading.Thread(target=service.worker, daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1', 9110), handler(service, token)).serve_forever()
