import os
import re
from hmac import compare_digest
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import get_user_model
from django.urls import include, path

class AuroraSsoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/v2/version/':
            return self.get_response(request)
        secret = os.environ.get('AURORA_PROXY_SECRET', '')
        supplied = request.headers.get('X-Aurora-Lab-Secret', '')
        identity = request.headers.get('X-Aurora-Identity', '')
        if len(secret) < 32 or not compare_digest(secret.encode(), supplied.encode()) or identity != 'aurora@server.local':
            return JsonResponse({'error': 'Acesso somente pelo login AuroraLAB.'}, status=403)
        user = get_user_model().objects.filter(username='rafael', is_active=True).first()
        if not user:
            return JsonResponse({'error': 'Perfil de avaliação ainda não preparado.'}, status=503)
        request.user = user
        request._cached_user = user
        if any(part in request.path for part in ('/login/', '/signup/', '/password/', '/register/', '/logout/', '/token/', '/oidc/', '/headless/')):
            return HttpResponse('Use o login central do AuroraLAB.', status=403)
        response = self.get_response(request)
        if not response.streaming and 'text/html' in response.get('Content-Type', ''):
            banner = '<div style="padding:10px;background:#854d0e;color:white;text-align:center;font:14px system-ui">WGER · AMBIENTE DE AVALIAÇÃO · cópia independente do openGym. <a style="color:white;text-decoration:underline" href="/aurora-import/">Dados copiados</a> · <a style="color:white;text-decoration:underline" href="https://auroraserver.tail7d26f7.ts.net/mirror/">AuroraLAB</a></div>'
            response.content = re.sub(r'(<body[^>]*>)', lambda match:match.group(1)+banner, response.content.decode(response.charset), count=1, flags=re.I)
            if response.has_header('Content-Length'):
                del response['Content-Length']
        response['Cache-Control'] = 'no-store'
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response

def import_report(request):
    from report import render_report
    return render_report(request)

from wger.urls import urlpatterns as wger_patterns
urlpatterns = [path('aurora-import/', import_report)] + wger_patterns
