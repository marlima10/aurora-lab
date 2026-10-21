"""Read-only Garmin Personal API client; credentials never leave the official host."""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://personal.connectapi.garmin.com'
TOKEN_PATH = '/personalapitoken-service/personal-api/personal-api-key/token'
ACTIVITIES_PATH = '/activitylist-service/activities/search/activities'

class PersonalAPIError(Exception):
    def __init__(self,message,http_status=None,phase=None):
        super().__init__(message)
        self.http_status=http_status
        self.phase=phase

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def valid_secret(value):
    return isinstance(value, str) and 1 <= len(value) <= 8192 and all(33 <= ord(c) < 127 for c in value)

class PersonalAPI:
    def __init__(self, api_key):
        if not valid_secret(api_key):
            raise PersonalAPIError('Informe a chave pessoal Garmin, sem espacos ou quebras de linha.')
        self.api_key = api_key
        self.access_token = None
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, path, authorization, method='GET'):
        request = urllib.request.Request(BASE + path, data=None,
            method=method, headers={'Authorization': authorization, 'Accept': '*/*' if path == TOKEN_PATH else 'application/json'})
        try:
            with self.opener.open(request, timeout=30) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise PersonalAPIError('Resposta Garmin excedeu o limite permitido.')
            try:
                return json.loads(raw)
            except (ValueError, UnicodeError):
                if path == TOKEN_PATH:
                    token=raw.decode('ascii').strip()
                    if valid_secret(token): return token
                raise
        except urllib.error.HTTPError as error:
            phase='token' if path == TOKEN_PATH else 'activities'
            step='gerar o token' if phase == 'token' else 'consultar atividades'
            if error.code in (400, 401, 403):
                message=f'A Garmin recusou o pedido ao {step} (HTTP {error.code}). Confira a chave pessoal e sua validade.'
            elif error.code == 429:
                message='A Garmin limitou as consultas (HTTP 429). Aguarde antes de tentar novamente.'
            else:
                message=f'A API Garmin retornou HTTP {error.code} ao {step}. O diagnostico foi registrado sem credenciais.'
            raise PersonalAPIError(message,http_status=error.code,phase=phase) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise PersonalAPIError('Nao foi possivel acessar a API oficial Garmin. Seus treinos foram preservados.') from None
        except (ValueError, UnicodeError):
            raise PersonalAPIError('Formato de resposta da API Garmin nao reconhecido.') from None

    def authenticate(self):
        result = self.request(TOKEN_PATH, 'ApiKey ' + self.api_key, 'POST')
        token = (result.get('access_token') or result.get('accessToken')) if isinstance(result, dict) else result if isinstance(result,str) else None
        if not valid_secret(token):
            raise PersonalAPIError('Resposta do token Garmin nao reconhecida. A chave anterior foi preservada.')
        self.access_token = token

    def activities(self, start, limit, first=None, last=None):
        if self.access_token is None:
            self.authenticate()
        query = {'start': start, 'limit': limit, 'sortOrder': 'desc', 'sortBy': 'startLocal', 'excludeChildren': 'true'}
        if first: query['startDate'] = first
        if last: query['endDate'] = last
        result = self.request(ACTIVITIES_PATH + '?' + urllib.parse.urlencode(query), 'Bearer ' + self.access_token)
        if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
            raise PersonalAPIError('Resposta de atividades Garmin nao reconhecida.')
        return result
