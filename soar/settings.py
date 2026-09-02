"""
Configurações do projeto Soar — Site de Viagem.

Nada sensível fica escrito aqui. O que muda entre a sua máquina e o servidor
vem de variáveis de ambiente, e o padrão de cada uma é o valor seguro para
rodar localmente:

    SOAR_SECRET_KEY     chave de assinatura (obrigatória quando SOAR_DEBUG=0)
    SOAR_DEBUG          1 (padrão) para desenvolvimento, 0 no servidor
    SOAR_ALLOWED_HOSTS  domínios separados por vírgula, ex.: soar.com.br,www.soar.com.br
    SOAR_HSTS_SECONDS   validade do HSTS em segundos (padrão 3600)
    SOAR_SSL_REDIRECT   1 (padrão) para forçar HTTPS quando SOAR_DEBUG=0

Rodar assim continua funcionando sem configurar nada:

    python manage.py runserver
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _ligado(nome, padrao):
    """Lê uma variável de ambiente como sim/não."""
    return os.environ.get(nome, '1' if padrao else '0').strip().lower() in ('1', 'true', 'on', 'sim')


def _lista(nome):
    return [item.strip() for item in os.environ.get(nome, '').split(',') if item.strip()]


# --------------------------------------------------------------------------- #
# Básico
# --------------------------------------------------------------------------- #
CHAVE_DE_DESENVOLVIMENTO = 'django-insecure-soar-apenas-para-desenvolvimento-local'

SECRET_KEY = os.environ.get('SOAR_SECRET_KEY') or CHAVE_DE_DESENVOLVIMENTO

DEBUG = _ligado('SOAR_DEBUG', True)

ALLOWED_HOSTS = _lista('SOAR_ALLOWED_HOSTS')
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# No servidor a chave de exemplo não serve: ela está no repositório, então
# qualquer pessoa conseguiria forjar sessões e tokens de CSRF.
if not DEBUG and SECRET_KEY == CHAVE_DE_DESENVOLVIMENTO:
    raise ImproperlyConfigured(
        'Defina a variável de ambiente SOAR_SECRET_KEY antes de rodar com SOAR_DEBUG=0. '
        'Para gerar uma: python -c "from django.core.management.utils import '
        'get_random_secret_key; print(get_random_secret_key())"'
    )

if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        'Defina SOAR_ALLOWED_HOSTS com os domínios do site, separados por vírgula.'
    )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps do projeto
    'destinations',
    'reviews',
    'contas',
    'reservas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'soar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'soar.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos (CSS, JS)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Arquivos enviados pelos usuários (fotos dos destinos, hospedagens, avaliações)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------- #
# Contas
# --------------------------------------------------------------------------- #
# Quem tenta reservar sem estar logado cai aqui e volta para onde estava.
LOGIN_URL = 'contas:entrar'
LOGIN_REDIRECT_URL = 'destinations:home'
LOGOUT_REDIRECT_URL = 'destinations:home'

# --------------------------------------------------------------------------- #
# Segurança
# --------------------------------------------------------------------------- #
# Valem sempre — não atrapalham o desenvolvimento local.
SECURE_CONTENT_TYPE_NOSNIFF = True          # o navegador não "adivinha" o tipo do arquivo
SECURE_REFERRER_POLICY = 'same-origin'      # não vaza a URL interna para outros sites
X_FRAME_OPTIONS = 'DENY'                    # ninguém embute o site num iframe (clickjacking)
SESSION_COOKIE_HTTPONLY = True              # JavaScript não lê o cookie de sessão
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Limites de upload: a avaliação é um formulário público, então o tamanho do
# corpo da requisição precisa de teto (o campo de foto tem validação própria
# em reviews/forms.py).
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024     # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

# Só fazem sentido com HTTPS de verdade, então ligam junto com SOAR_DEBUG=0.
if not DEBUG:
    SECURE_SSL_REDIRECT = _ligado('SOAR_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS começa em 1 hora de propósito: ele é gravado no navegador e não dá
    # para cancelar antes de expirar. Confirme que o HTTPS está firme e só
    # então suba para 31536000 (um ano) via SOAR_HSTS_SECONDS.
    SECURE_HSTS_SECONDS = int(os.environ.get('SOAR_HSTS_SECONDS', 3600))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    # Atrás de um proxy/balanceador (Nginx, Heroku, Render...), é ele que fala
    # HTTPS com o visitante; o cabeçalho abaixo conta isso para o Django.
    if _ligado('SOAR_ATRAS_DE_PROXY', False):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    CSRF_TRUSTED_ORIGINS = ['https://{}'.format(host) for host in ALLOWED_HOSTS
                            if not host.startswith('.')]
