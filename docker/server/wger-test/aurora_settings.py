from settings.main import *
import os
ALLOWED_HOSTS = ['auroraserver.tail7d26f7.ts.net', 'localhost', '127.0.0.1']
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
CSRF_TRUSTED_ORIGINS = ['https://auroraserver.tail7d26f7.ts.net:8444']
CSRF_COOKIE_NAME = 'csrftoken'
SESSION_COOKIE_NAME = 'wger_test_session'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Strict'
CACHES = {'default': {'BACKEND':'django.core.cache.backends.locmem.LocMemCache','TIMEOUT':1296000}}
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware')+1, 'aurora_sso.AuroraSsoMiddleware')
ROOT_URLCONF = 'aurora_sso'
REST_FRAMEWORK = dict(REST_FRAMEWORK, DEFAULT_AUTHENTICATION_CLASSES=('rest_framework.authentication.SessionAuthentication',))
AUTH_PROXY_HEADER = ''
AUTHENTICATION_BACKENDS = ('axes.backends.AxesStandaloneBackend', 'django.contrib.auth.backends.ModelBackend')
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
