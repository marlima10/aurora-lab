"""Native app reads with fixed origins and per-app identity mappings."""
import math
import os
import urllib.parse
from common import Problem, authorize, configuration, request, serve
from tools import validate


def fitness_summary(state, args):
    rows = [w for w in state.get('workouts', []) if isinstance(w, dict) and args['start'] <= str(w.get('d', '')) <= args['end']]
    rows.sort(key=lambda w: (w.get('d', ''), w.get('start') or 0), reverse=True)
    results = []
    for row in rows[:args.get('limit', 100)]:
        begin, end = row.get('start'), row.get('end')
        duration = (end-begin)/60000 if all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (begin, end)) and end >= begin else None
        calories = (row.get('garminActivity') or {}).get('calories')
        if isinstance(calories, bool) or not isinstance(calories, (int, float)) or not math.isfinite(calories) or calories < 0:
            calories = None
        results.append({'date': row.get('d'), 'name': str(row.get('name', ''))[:150], 'minutes': round(duration, 2) if duration is not None else None, 'calories': calories})
    return {'source': 'openGym', 'count': len(results), 'workouts': results, 'totalMinutes': round(sum(w['minutes'] for w in results if w['minutes'] is not None), 2),
            'knownCalories': sum(w['calories'] for w in results if w['calories'] is not None), 'missingCalories': sum(w['calories'] is None for w in results), 'truncated': len(rows) > len(results)}


def dispatch(method, path, headers, body):
    cfg = configuration()
    authorize(headers, cfg['token'])
    if method != 'POST' or path != '/query':
        raise Problem(404, 'Consulta não disponível.')
    name, args, identity = body.get('tool'), body.get('args', {}), body.get('identity')
    validate(name, args)
    role = os.environ['CONNECTOR_ROLE']
    app = cfg['apps']['manyfold' if name == 'aurora_model_library' else 'octoprint'] if role == 'print' else cfg
    if not app.get('ready') or not isinstance(identity, str) or identity not in app.get('identities', {}):
        raise Problem(403, 'Perfil não autorizado.')
    h = {'X-Aurora-Identity': identity, 'X-Aurora-Proxy-Secret': app['secret']}
    if role == 'fitness' and name == 'aurora_fitness_summary':
        return fitness_summary(request('http://opengym-api:3000/api/data', headers=h)['state'], args)
    if role == 'food':
        h['X-Mealie-Reverse-Proxy-Secret'] = app['secret']
        if name == 'aurora_recipes':
            query = urllib.parse.urlencode({'search': args.get('query', ''), 'perPage': 15})
            rows = request('http://mealie:9000/api/recipes?' + query, headers=h).get('items', [])
            return {'source': 'Mealie', 'recipes': [{k: row.get(k) for k in ('id', 'name', 'description', 'totalTime')} for row in rows[:15]]}
        if name == 'aurora_shopping_lists':
            rows = request('http://mealie:9000/api/households/shopping/lists?perPage=20', headers=h).get('items', [])
            return {'source': 'Mealie', 'lists': [{k: row.get(k) for k in ('id', 'name')} for row in rows[:20]]}
    if role == 'print' and name == 'aurora_print_status':
        result = request('http://octoprint:80/api/job', headers=h)
        return {'source': 'OctoPrint', 'state': result.get('state'), 'progress': result.get('progress'), 'job': result.get('job')}
    if role == 'print' and name == 'aurora_model_library':
        h['Accept'] = 'application/vnd.manyfold.v0+json'
        result = request('http://manyfold:3214/models?' + urllib.parse.urlencode({'q': args.get('query', '')}), headers=h)
        rows = result if isinstance(result, list) else result.get('models', result.get('member', []))
        if not isinstance(rows, list):
            raise Problem(503, 'Formato da biblioteca indisponível.')
        return {'source': 'Manyfold', 'models': [{k: row.get(k) for k in ('id', '@id', 'name', 'description')} for row in rows[:20] if isinstance(row, dict)]}
    raise Problem(403, 'O conector não permite esta operação.')


if __name__ == '__main__':
    serve(dispatch)
