"""Stateless MCP JSON-RPC, delegated to fixed, separately isolated connectors."""
from common import Problem, authorize, configuration, request, serve
from tools import TOOLS, catalog, validate


def grants(cfg):
    result = request('http://auth:7777/auth/internal/javis', headers={'Authorization': 'Bearer ' + cfg['authToken']})
    return result['grants']


def dispatch(method, path, headers, message):
    cfg = configuration()
    authorize(headers, cfg['token'])
    if method != 'POST' or path != '/mcp':
        raise Problem(405, 'Use o transporte MCP autorizado.')
    mid, action = message.get('id'), message.get('method', '')
    if not isinstance(action, str):
        raise Problem(400, 'Método inválido.')
    if action.startswith('notifications/'):
        return None
    if action == 'initialize':
        result = {'protocolVersion': (message.get('params') or {}).get('protocolVersion', '2025-03-26'),
                  'capabilities': {'tools': {}}, 'serverInfo': {'name': 'AuroraLAB Data', 'version': '34.0.0'}}
    elif action in ('ping', 'resources/list', 'resources/templates/list', 'prompts/list'):
        key = {'resources/list': 'resources', 'resources/templates/list': 'resourceTemplates', 'prompts/list': 'prompts'}.get(action)
        result = {key: []} if key else {}
    elif action == 'tools/list':
        result = {'tools': catalog(grants(cfg))}
    elif action == 'tools/call':
        import json
        params = message.get('params') or {}
        name, arguments = params.get('name'), params.get('arguments', {})
        try:
            validate(name, arguments)
            app, role = TOOLS[name][:2]
            current = grants(cfg)
            if app not in current:
                raise Problem(403, 'Aplicativo não autorizado no AuroraLAB.')
            connector = cfg['connectors'][role]
            value = request('http://javis-' + role + ':8000/query', {'tool': name, 'args': arguments, 'identity': current[app]},
                            headers={'Authorization': 'Bearer ' + connector}, timeout=60)
            result = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}], 'isError': False}
        except Problem as error:
            result = {'content': [{'type': 'text', 'text': error.message}], 'isError': True}
    else:
        return {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': 'Método não disponível.'}}
    return {'jsonrpc': '2.0', 'id': mid, 'result': result}


if __name__ == '__main__':
    serve(dispatch)
