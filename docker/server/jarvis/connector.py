"""Narrow per-app tools; fixed destinations, no arbitrary URL, SQL or shell tool."""
import datetime as dt
import json
import math
import os
import urllib.parse
from common import Problem, authorize, config, rpc, serve, text


def day(value):
    return dt.date.fromisoformat(value).isoformat()


def fitness_summary(state, args):
    first, last = day(args['start']), day(args['end'])
    if last < first or (dt.date.fromisoformat(last)-dt.date.fromisoformat(first)).days > 366:
        raise Problem(400, 'Selecione um intervalo de até um ano.')
    rows = [w for w in state.get('workouts', []) if isinstance(w, dict) and first <= str(w.get('d', '')) <= last]
    rows.sort(key=lambda w: (w.get('d', ''), w.get('start') or 0), reverse=True)
    limit = args.get('limit', 100)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise Problem(400, 'Limite de treinos inválido.')
    results = []
    for w in rows[:limit]:
        begin, end = w.get('start'), w.get('end')
        duration = (end-begin)/60000 if all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (begin, end)) and end >= begin else None
        calories = (w.get('garminActivity') or {}).get('calories')
        if isinstance(calories, bool) or not isinstance(calories, (int, float)) or not math.isfinite(calories) or calories < 0:
            calories = None
        results.append({'date': w.get('d'), 'name': str(w.get('name', ''))[:180], 'minutes': round(duration, 2) if duration is not None else None, 'calories': calories})
    return {'source': 'openGym', 'start': first, 'end': last, 'workouts': results, 'count': len(results),
            'totalMinutes': round(sum(w['minutes'] for w in results if w['minutes'] is not None), 2),
            'knownCalories': sum(w['calories'] for w in results if w['calories'] is not None),
            'missingCalories': sum(w['calories'] is None for w in results), 'truncated': len(rows) > limit}


def dispatch(method, path, headers, data):
    cfg = config()
    authorize(headers, cfg['token'])
    if method != 'POST' or path != '/call':
        raise Problem(404, 'Operação não encontrada.')
    identity, tool, args = data.get('identity'), data.get('tool'), data.get('args', {})
    if not isinstance(args, dict):
        raise Problem(400, 'Argumentos inválidos.')
    role = os.environ['CONNECTOR_ROLE']
    if role == 'print':
        cfg = cfg['apps']['manyfold' if tool == 'print_library' else 'octoprint']
    if role != 'research' and (not cfg.get('ready') or identity not in cfg.get('identities', {})):
        raise Problem(403, 'Integração não autorizada para este perfil.')
    if role == 'research' and tool == 'research_search':
        from ddgs import DDGS
        query = text(args.get('query'), 300)
        try:
            rows = list(DDGS(timeout=12).text(query, max_results=5))
        except Exception:
            raise Problem(503, 'A pesquisa pública não respondeu. Tente novamente.') from None
        return {'source': 'Pesquisa pública', 'results': [{'title': str(r.get('title', ''))[:200], 'url': r.get('href'), 'summary': str(r.get('body', ''))[:1000]} for r in rows[:5]]}
    h = {'X-Aurora-Identity': identity, 'X-Aurora-Proxy-Secret': cfg['secret']}
    if role == 'fitness' and tool == 'fitness_summary':
        result = rpc('http://opengym-api:3000/api/data', headers=h)
        return fitness_summary(result['state'], args)
    if role == 'food':
        h['X-Mealie-Reverse-Proxy-Secret'] = cfg['secret']
        if tool == 'food_recipes':
            query = urllib.parse.urlencode({'search': str(args.get('query', ''))[:150], 'perPage': 15, 'page': 1})
            result = rpc('http://mealie:9000/api/recipes?' + query, headers=h)
            return {'source': 'Mealie', 'recipes': [{k: row.get(k) for k in ('id', 'slug', 'name', 'description', 'totalTime', 'recipeYield')} for row in result.get('items', [])[:15]]}
        if tool == 'food_shopping_lists':
            result = rpc('http://mealie:9000/api/households/shopping/lists?perPage=20', headers=h)
            return {'source': 'Mealie', 'lists': [{k: r.get(k) for k in ('id', 'name')} for r in result.get('items', [])[:20]]}
        if tool == 'food_add_recipe':
            name = text(args.get('name'), 150)
            result = rpc('http://mealie:9000/api/recipes', {'name': name}, headers=h)
            return {'saved': True, 'result': result}
    if role == 'print':
        if tool == 'print_status':
            result = rpc('http://octoprint:80/api/job', headers=h)
            return {'source': 'OctoPrint', 'state': result.get('state'), 'progress': result.get('progress'), 'job': result.get('job')}
        if tool == 'print_library':
            query = urllib.parse.urlencode({'q': str(args.get('query', ''))[:150]})
            h['Accept'] = 'application/vnd.manyfold.v0+json'
            result = rpc('http://manyfold:3214/models?' + query, headers=h)
            rows = result if isinstance(result, list) else result.get('models', result.get('member', result.get('@graph', [])))
            if not isinstance(rows, list):
                raise Problem(502, 'Formato da biblioteca Manyfold não reconhecido.')
            return {'source': 'Manyfold', 'models': [{k: r.get(k) for k in ('id', '@id', 'name', 'description', 'url')} for r in rows[:20] if isinstance(r, dict)]}
        if tool == 'print_pause':
            # Explicit target state; never toggle or start a print implicitly.
            rpc('http://octoprint:80/api/job', {'command': 'pause', 'action': 'pause'}, headers=h)
            return {'saved': True, 'action': 'pause'}
    raise Problem(404, 'Ferramenta não permitida neste conector.')


if __name__ == '__main__':
    serve(dispatch)
