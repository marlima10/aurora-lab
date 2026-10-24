"""Run only inside the disposable Mealie fixture with its initial synthetic user."""
import json
import os
import urllib.error
import urllib.request


def check():
    if os.environ.get('AURORA_DISPOSABLE_FIXTURE') != '1':
        raise SystemExit('Use a disposable instance, never a personal database')
    from mealie.core.config import get_app_settings
    headers = {'X-Mealie-Reverse-Proxy-Secret':os.environ['REVERSE_PROXY_AUTH_SECRET'],
               'X-Aurora-Identity':get_app_settings()._DEFAULT_EMAIL,
               'Authorization':'Bearer old-other-profile-fixture-token'}
    url = 'http://127.0.0.1:9000/api/users/self'
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10) as response:
        assert json.load(response)['email'] == get_app_settings()._DEFAULT_EMAIL
        assert response.headers.get('Set-Cookie')
    for change in [{'X-Mealie-Reverse-Proxy-Secret':'forged'}, {'X-Aurora-Identity':'missing@example.test'}]:
        try:
            urllib.request.urlopen(urllib.request.Request(url, headers=headers|change), timeout=10)
        except urllib.error.HTTPError as error:
            assert error.code == 403
        else:
            raise AssertionError('Native identity was not enforced')
    print(json.dumps({'native_identity':True,'old_token_overridden':True,'untrusted_identity_denied':True}))


if __name__=='__main__':
    check()
