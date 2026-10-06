"""
Configurações do projeto Soar — Site de Viagem.

Nada sensível fica escrito aqui. O que muda entre a sua máquina e o servidor
vem de variáveis de ambiente, lidas do ambiente real ou de um arquivo `.env`
na raiz do projeto (que não vai para o repositório).

O padrão de cada variável é o valor **de produção** — o mais seguro. Rodar em
modo de desenvolvimento é que exige dizer isso explicitamente, porque o erro
caro é subir um servidor achando que ele está protegido, não o contrário.

    SOAR_DEBUG          0 (padrão) para servidor, 1 para desenvolvimento
    SOAR_SECRET_KEY     chave de assinatura (obrigatória quando SOAR_DEBUG=0)
    SOAR_ALLOWED_HOSTS  domínios separados por vírgula, ex.: soar.com.br,www.soar.com.br
    SOAR_HSTS_SECONDS   validade do HSTS em segundos (padrão 3600)
    SOAR_HSTS_PRELOAD   1 para entrar na lista de pré-carregamento dos navegadores
    SOAR_SSL_REDIRECT   1 (padrão) para forçar HTTPS quando SOAR_DEBUG=0
    SOAR_ATRAS_DE_PROXY 1 quando um Nginx/balanceador termina o HTTPS
    SOAR_CSP_SOMENTE_RELATORIO  0 (padrão) a CSP bloqueia; 1 só reporta, para depurar

    SOAR_DB_ENGINE      postgresql para usar Postgres (padrão: sqlite3)
    SOAR_DB_NAME/USER/PASSWORD/HOST/PORT

    SOAR_EMAIL_BACKEND  smtp para enviar de verdade (padrão: console)
    SOAR_EMAIL_HOST/PORT/USER/PASSWORD/TLS, SOAR_EMAIL_REMETENTE
    SOAR_GOOGLE_CLIENT_ID/SECRET  liga o botão "Continuar com Google"
    SOAR_RESERVAS_URL   endereço do sistema de reservas das agências (vazio esconde o botão)

Para desenvolver, copie `.env.example` para `.env` (já vem com SOAR_DEBUG=1):

    cp .env.example .env
    python manage.py runserver
"""
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _carregar_env(caminho):
    """Lê um arquivo .env para dentro de os.environ.

    Sem dependência externa e sem sobrescrever o que já veio do ambiente de
    verdade — no servidor, quem manda é a variável real, e o arquivo (se
    existir) só preenche o que faltou.
    """
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding='utf-8').splitlines():
        linha = linha.strip()
        if not linha or linha.startswith('#') or '=' not in linha:
            continue
        nome, _, valor = linha.partition('=')
        os.environ.setdefault(nome.strip(), valor.strip().strip('"').strip("'"))


_carregar_env(BASE_DIR / '.env')


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

# O padrão é produção. Esquecer a variável não deixa mais o site em modo de
# depuração — deixa ele exigindo a configuração que faltou, que é barulhento
# na hora certa em vez de silencioso do jeito errado.
DEBUG = _ligado('SOAR_DEBUG', False)

ALLOWED_HOSTS = _lista('SOAR_ALLOWED_HOSTS')
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# No servidor a chave de exemplo não serve: ela está no repositório, então
# qualquer pessoa conseguiria forjar sessões e tokens de CSRF.
if not DEBUG:
    if SECRET_KEY == CHAVE_DE_DESENVOLVIMENTO:
        raise ImproperlyConfigured(
            'Defina a variável de ambiente SOAR_SECRET_KEY antes de rodar com SOAR_DEBUG=0. '
            'Para gerar uma: python -c "from django.core.management.utils import '
            'get_random_secret_key; print(get_random_secret_key())"'
        )
    # Não basta ser diferente da chave de exemplo: uma chave curta ou repetitiva
    # é adivinhável, e adivinhar a chave é forjar qualquer sessão. Mesmo
    # critério que o `manage.py check --deploy` aplica.
    if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5:
        raise ImproperlyConfigured(
            'SOAR_SECRET_KEY é fraca demais: precisa de pelo menos 50 caracteres e 5 '
            'caracteres distintos. Gere uma com: python -c "from '
            'django.core.management.utils import get_random_secret_key; '
            'print(get_random_secret_key())"'
        )

if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        'Defina SOAR_ALLOWED_HOSTS com os domínios do site, separados por vírgula.'
    )

INSTALLED_APPS = [
    # O painel do dono no lugar do admin padrão: mesma máquina, outra tela
    # inicial e outra roupa (soar/painel.py).
    'soar.painel.SoarAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps do projeto
    'destinations',
    'reviews',
    'contas',
    'blog',
    'agencia',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'soar.middleware.ContentSecurityPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Depois do login, para saber se é a equipe (que pode mandar vídeo). Nenhum
    # dos de cima lê o corpo do envio, então ele ainda é recusado sem ser lido.
    'soar.middleware.LimiteDeEnvioMiddleware',
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
                'contas.context_processors.google_login',
                'contas.context_processors.sistema_reservas',
                'contas.context_processors.site_em_construcao',
            ],
        },
    },
]

WSGI_APPLICATION = 'soar.wsgi.application'

# --------------------------------------------------------------------------- #
# Banco
# --------------------------------------------------------------------------- #
# SQLite serve para desenvolver. Em produção ele serializa as escritas (duas
# reservas ao mesmo tempo viram "database is locked") e é um arquivo só dentro
# da pasta do projeto — configure SOAR_DB_ENGINE=postgresql no servidor.
if os.environ.get('SOAR_DB_ENGINE', 'sqlite3').strip() in ('postgresql', 'postgres'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('SOAR_DB_NAME', 'soar'),
            'USER': os.environ.get('SOAR_DB_USER', 'soar'),
            'PASSWORD': os.environ.get('SOAR_DB_PASSWORD', ''),
            'HOST': os.environ.get('SOAR_DB_HOST', 'localhost'),
            'PORT': os.environ.get('SOAR_DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# --------------------------------------------------------------------------- #
# Cache — sustenta os limites de tentativa (login, cadastro, avaliação)
# --------------------------------------------------------------------------- #
# LocMemCache é por processo: com vários workers, cada um conta em separado e o
# limite fica mais frouxo do que parece. Em produção aponte para Redis ou
# Memcached, que é onde a contagem passa a ser de verdade.
_redis = os.environ.get('SOAR_REDIS_URL', '').strip()
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': _redis,
    } if _redis else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'soar-limites',
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

# No ar, o collectstatic grava cada arquivo também com um código no nome
# (blog.css -> blog.3f9a2c1b.css) e o {% static %} aponta para esse. O Nginx
# manda o navegador guardar CSS e JS por 30 dias; sem o código, quem já tinha
# visitado o site ficava com o CSS velho mesmo depois de uma atualização. Com
# ele, arquivo mudado = endereço novo = o navegador busca na hora.
# Nos testes não há collectstatic, então fica o armazenamento simples.
STATICFILES_BACKEND = ('django.contrib.staticfiles.storage.StaticFilesStorage'
                       if sys.argv[1:2] == ['test']
                       else 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': STATICFILES_BACKEND},
}

# Arquivos enviados pelos usuários (fotos dos destinos, hospedagens, avaliações)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --------------------------------------------------------------------------- #
# Fotos e vídeos no Cloudflare R2 (opcional)
# --------------------------------------------------------------------------- #
# Com SOAR_R2_BUCKET definido, tudo o que o painel envia (fotos, vídeos, PDFs
# de capa) vai para o R2 em vez do disco da VPS: o servidor não enche de vídeo
# e o backup dos arquivos fica por conta do R2. Sem a variável, continua no
# disco (MEDIA_ROOT), do jeito de sempre.
#
#   SOAR_R2_BUCKET          nome do bucket
#   SOAR_R2_ACCOUNT_ID      ID da conta Cloudflare (vai no endereço da API)
#   SOAR_R2_ACCESS_KEY      chave de acesso (token de API do R2 com permissão
#   SOAR_R2_SECRET_KEY      só de leitura e escrita neste bucket)
#   SOAR_R2_DOMINIO         domínio público do bucket, ex.: midia.soar.com.br
R2_BUCKET = os.environ.get('SOAR_R2_BUCKET', '').strip()
R2_DOMINIO = os.environ.get('SOAR_R2_DOMINIO', '').strip()
if R2_BUCKET:
    for _variavel in ('SOAR_R2_ACCOUNT_ID', 'SOAR_R2_ACCESS_KEY', 'SOAR_R2_SECRET_KEY',
                      'SOAR_R2_DOMINIO'):
        if not os.environ.get(_variavel, '').strip():
            raise ImproperlyConfigured(
                'SOAR_R2_BUCKET está definido, mas falta {}.'.format(_variavel))
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                'bucket_name': R2_BUCKET,
                'endpoint_url': 'https://{}.r2.cloudflarestorage.com'.format(
                    os.environ['SOAR_R2_ACCOUNT_ID'].strip()),
                'access_key': os.environ['SOAR_R2_ACCESS_KEY'].strip(),
                'secret_key': os.environ['SOAR_R2_SECRET_KEY'].strip(),
                'region_name': 'auto',
                'signature_version': 's3v4',
                # As fotos são públicas por natureza (estão no site); o bucket
                # só é lido pelo domínio público, nunca listado.
                'custom_domain': R2_DOMINIO,
                'url_protocol': 'https:',
                'querystring_auth': False,
                'default_acl': None,
                # Nunca sobrescreve: dois envios com o mesmo nome viram dois arquivos.
                'file_overwrite': False,
                'object_parameters': {'CacheControl': 'public, max-age=2592000'},
            },
        },
        'staticfiles': {'BACKEND': STATICFILES_BACKEND},
    }
    MEDIA_URL = 'https://{}/'.format(R2_DOMINIO)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------- #
# E-mail
# --------------------------------------------------------------------------- #
# Sem configurar nada, as mensagens saem no terminal — dá para desenvolver o
# fluxo de confirmação e de recuperação de senha sem servidor de e-mail.
if os.environ.get('SOAR_EMAIL_BACKEND', 'console').strip() == 'smtp':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('SOAR_EMAIL_HOST', '')
    EMAIL_PORT = int(os.environ.get('SOAR_EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('SOAR_EMAIL_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('SOAR_EMAIL_PASSWORD', '')
    EMAIL_USE_TLS = _ligado('SOAR_EMAIL_TLS', True)
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('SOAR_EMAIL_REMETENTE', 'Soar Operadora <contato@operadorasoar.com.br>')
EMAIL_TIMEOUT = 15   # segundos; sem isso um SMTP fora do ar trava a tela de cadastro

# Entrar com Google. As duas vêm do Google Cloud Console (ver README). Sem
# elas o botão não aparece e o site segue só com e-mail e senha.
GOOGLE_CLIENT_ID = os.environ.get('SOAR_GOOGLE_CLIENT_ID', '').strip()
GOOGLE_CLIENT_SECRET = os.environ.get('SOAR_GOOGLE_CLIENT_SECRET', '').strip()

# Sistema de reservas da operadora, onde as agências vendem os pacotes. É outro
# sistema, com banco e login próprios: o site só leva o agente até lá. Quando
# ele passar a ter HTTPS, troque o endereço aqui pelo https. Vazio esconde o botão.
SISTEMA_RESERVAS_URL = os.environ.get('SOAR_RESERVAS_URL',
                                      'http://www.reservassoar.com.br/login').strip()

# Tela "Site em Construção" por cima de todas as páginas, enquanto o dono
# termina de arrumar o site. Ele e a equipe (quem entra no painel) não veem.
# Ligar: SOAR_SITE_EM_CONSTRUCAO=1 no .env e reiniciar. Tirar: apagar a linha.
SITE_EM_CONSTRUCAO = _ligado('SOAR_SITE_EM_CONSTRUCAO', False)
# Link secreto para o login com a tela ligada: /entrar/?acesso=<este código>.
# Só quem tem o link vê a página de login (o dono e quem cuida do site).
SITE_EM_CONSTRUCAO_ACESSO = os.environ.get('SOAR_SITE_EM_CONSTRUCAO_ACESSO', '').strip()

# --------------------------------------------------------------------------- #
# Contas
# --------------------------------------------------------------------------- #
# Quem tenta reservar sem estar logado cai aqui e volta para onde estava.
# O backend padrao recusa usuario inativo direto no authenticate(), e a pessoa
# que ainda nao confirmou o e-mail recebe "senha nao confere", que e mentira.
# Com este, quem acerta a senha chega ate o formulario e ve o motivo de verdade
# ("falta confirmar o e-mail"). Quem erra a senha continua sem saber de nada.
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']

# Validade dos links de confirmação de e-mail e de troca de senha. O padrão do
# Django é 3 dias; um link de senha esquecido na caixa de entrada por tanto
# tempo é uma porta aberta para quem tiver acesso a ela depois.
PASSWORD_RESET_TIMEOUT = 24 * 3600

LOGIN_URL = 'contas:entrar'
LOGIN_REDIRECT_URL = 'destinations:home'
LOGOUT_REDIRECT_URL = 'destinations:home'

# --------------------------------------------------------------------------- #
# Limites de tentativa (contas/limites.py)
# --------------------------------------------------------------------------- #
LIMITE_LOGIN_TENTATIVAS = int(os.environ.get('SOAR_LIMITE_LOGIN', 5))
LIMITE_LOGIN_JANELA = int(os.environ.get('SOAR_LIMITE_LOGIN_JANELA', 900))       # 15 min
LIMITE_CADASTRO_POR_HORA = int(os.environ.get('SOAR_LIMITE_CADASTRO', 5))
# Cada pedido destes manda um e-mail: sem limite, dava para lotar a caixa de
# alguém com "troque sua senha" ou "confirme a newsletter" e, de quebra,
# estourar a cota diária do Gmail da Soar.
LIMITE_SENHA_POR_HORA = int(os.environ.get('SOAR_LIMITE_SENHA', 5))
LIMITE_NEWSLETTER_POR_HORA = int(os.environ.get('SOAR_LIMITE_NEWSLETTER', 5))
LIMITE_INTERESSE_POR_HORA = int(os.environ.get('SOAR_LIMITE_INTERESSE', 5))
LIMITE_AVALIACAO_POR_HORA = int(os.environ.get('SOAR_LIMITE_AVALIACAO', 3))
LIMITE_ORCAMENTO_POR_HORA = int(os.environ.get('SOAR_LIMITE_ORCAMENTO', 30))

# Verificação em duas etapas para a equipe (contas/dois_fatores.py). Desligada
# por pedido do cliente: o dono entra no painel só com a senha, sem o código do
# aplicativo autenticador. O código continua pronto: SOAR_2FA_EQUIPE=1 no .env
# volta a exigir o código do celular de quem é is_staff.
DOIS_FATORES_EQUIPE = _ligado('SOAR_2FA_EQUIPE', False)

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

# Duas semanas (o padrão do Django) é muito para um site que guarda telefone e
# dados de reserva. Uma semana cobre a viagem de ida e volta do cliente.
SESSION_COOKIE_AGE = int(os.environ.get('SOAR_SESSAO_SEGUNDOS', 7 * 24 * 3600))
SESSION_SAVE_EVERY_REQUEST = True           # a semana conta a partir do último acesso

# Limites de upload. Fora do painel, o site não recebe arquivo nenhum.
# Teto de qualquer envio ao site, conferido antes de ler o corpo
# (soar.middleware.LimiteDeEnvioMiddleware). Cobre as fotos do painel, que
# são maiores que as das avaliações. Use o mesmo valor no client_max_body_size
# do Nginx.
TAMANHO_MAXIMO_ENVIO = int(os.environ.get('SOAR_TAMANHO_MAXIMO_ENVIO_MB', 10)) * 1024 * 1024
# Vídeos do painel (galeria da viagem, carrossel da página inicial, blog e
# Soar 60+). O teto de envio maior vale só para a equipe logada no painel; no
# Nginx, use este valor (+ 5 MB de folga) no client_max_body_size do /painel/.
TAMANHO_MAXIMO_VIDEO = int(os.environ.get('SOAR_TAMANHO_MAXIMO_VIDEO_MB', 100)) * 1024 * 1024
TAMANHO_MAXIMO_ENVIO_PAINEL = TAMANHO_MAXIMO_VIDEO + 5 * 1024 * 1024
# Cada foto enviada pelo painel (capa, galeria, blog...). Foto de site não precisa de mais.
TAMANHO_MAXIMO_FOTO_PAINEL = int(os.environ.get('SOAR_TAMANHO_MAXIMO_FOTO_MB', 10)) * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024
# O formulário do destino no painel junta muitos blocos (preços por quarto,
# datas com os quartos de cada tipo, roteiro, fotos, vídeos, serviços...): uma
# viagem completa passa de 200 campos, e com 200 o painel recusava o salvar
# (TooManyFieldsSent). 1000 é o padrão do Django e ainda barra envio abusivo.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Content-Security-Policy — a rede que apara o que passar pelo escape dos
# templates. Sem 'unsafe-inline' em script-src: todo o JavaScript do site está
# em arquivos sob static/. Os estilos ainda precisam de inline por causa dos
# `style="..."` nos templates. As fontes são servidas pelo próprio site
# (static/fonts/), então nenhum domínio de fora entra na política.
# Bloqueando de verdade desde 28/09/2026: as páginas do site, da agência e do
# painel foram abertas com a política valendo e nenhuma violação apareceu.
# Ligue o modo relatório (1) só para investigar algo que parou de funcionar.
CSP_SOMENTE_RELATORIO = _ligado('SOAR_CSP_SOMENTE_RELATORIO', False)
# Token do Instagram para as fotos do #ViajantesSoar (destinations/instagram.py).
# Os testes nunca falam com o Instagram de verdade: os que precisam ligam um
# token falso com override_settings.
INSTAGRAM_TOKEN = ('' if sys.argv[1:2] == ['test']
                   else os.environ.get('SOAR_INSTAGRAM_TOKEN', '').strip())

CSP_DIRETIVAS = {
    'default-src': "'self'",
    'script-src': "'self'",
    'style-src': "'self' 'unsafe-inline'",
    'font-src': "'self'",
    'img-src': "'self' data:" + (' https://' + R2_DOMINIO if R2_DOMINIO else '')
               # fotos do #ViajantesSoar vêm direto do Instagram (destinations/instagram.py)
               + (' https://*.cdninstagram.com https://*.fbcdn.net' if INSTAGRAM_TOKEN else ''),
    'media-src': "'self'" + (' https://' + R2_DOMINIO if R2_DOMINIO else ''),
    'connect-src': "'self'",
    'form-action': "'self'",
    'frame-ancestors': "'none'",
    'base-uri': "'self'",
    'object-src': "'none'",
}

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
    # Só ligue o preload depois do HSTS estar em um ano e o HTTPS estável: sair
    # da lista dos navegadores demora meses.
    SECURE_HSTS_PRELOAD = _ligado('SOAR_HSTS_PRELOAD', False)

    # Atrás de um proxy/balanceador (Nginx, Heroku, Render...), é ele que fala
    # HTTPS com o visitante; o cabeçalho abaixo conta isso para o Django.
    if _ligado('SOAR_ATRAS_DE_PROXY', False):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    CSRF_TRUSTED_ORIGINS = ['https://{}'.format(host) for host in ALLOWED_HOSTS
                            if not host.startswith('.')]

# --------------------------------------------------------------------------- #
# Registro de eventos
# --------------------------------------------------------------------------- #
# Sem isto, um ataque de força bruta não deixa rastro nenhum: não dá para saber
# que aconteceu, quando começou, de onde veio nem se deu certo. `soar.seguranca`
# é onde caem as tentativas de login falhas e os limites estourados.
PASTA_LOGS = Path(os.environ.get('SOAR_PASTA_LOGS', BASE_DIR / 'logs'))
PASTA_LOGS.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'completo': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'completo',
        },
        # Um arquivo por dia, 183 dias guardados: os 6 meses de registro de
        # acesso que o Marco Civil (art. 15) exige e o aviso de privacidade
        # promete. Girar por tamanho (como era) não garantia prazo nenhum — com
        # pouco movimento guardava anos, com muito perdia a prova em semanas.
        # O `expurgar_dados` apaga o que sobrar de antes desta troca.
        # `delay` só abre o arquivo no primeiro registro: o processo vigia do
        # runserver nunca registra nada e não fica segurando o arquivo, o que no
        # Windows impediria a virada do dia.
        'arquivo_seguranca': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': PASTA_LOGS / 'seguranca.log',
            'when': 'midnight',
            'backupCount': 183,
            'delay': True,
            'encoding': 'utf-8',
            'formatter': 'completo',
        },
    },
    'loggers': {
        # Hosts recusados, CSRF quebrado, upload suspeito.
        'django.security': {
            'handlers': ['arquivo_seguranca', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Nossos eventos: login falho, limite estourado, conta criada.
        'soar.seguranca': {
            'handlers': ['arquivo_seguranca', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['arquivo_seguranca', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Falha ao apagar do disco/R2 um arquivo que ficou sem uso (soar/arquivos.py).
        'soar.arquivos': {
            'handlers': ['arquivo_seguranca', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Fotos do Instagram que não vieram e renovação do token (destinations/instagram.py).
        'soar.instagram': {
            'handlers': ['arquivo_seguranca', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
