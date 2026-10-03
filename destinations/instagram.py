"""Últimas fotos do @operadorasoar, para o bloco #ViajantesSoar da página inicial.

Como funciona:

1. O token sai do .env (SOAR_INSTAGRAM_TOKEN), gerado uma vez no painel da
   Meta (app > Instagram > "Gerar tokens de acesso"). Sem ele, o bloco segue
   com as fotos do próprio site, como sempre foi.
2. A página pede as fotos ao Instagram no máximo uma vez por hora (cache). Se
   o Instagram não responder, a página não espera nem quebra: usa as fotos do
   site e tenta de novo em 15 minutos.
3. O token vence em 60 dias. Ele é renovado sozinho a cada 7 dias, tanto pelo
   comando `manage.py renovar_token_instagram` (cron, ver deploy/DEPLOY.md)
   quanto na própria busca das fotos, para o caso de o cron não existir. O
   token renovado fica no banco (TokenInstagram), porque o .env só se lê.

Só usa a biblioteca padrão do Python — nada novo para instalar.
"""
import hashlib
import json
import logging
from datetime import timedelta
from urllib import error, parse, request as http

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

log = logging.getLogger('soar.instagram')

URL_FOTOS = 'https://graph.instagram.com/me/media'
URL_RENOVAR = 'https://graph.instagram.com/refresh_access_token'
CAMPOS = 'id,media_type,media_url,thumbnail_url,permalink,caption'
PERFIL = 'https://instagram.com/operadorasoar'

QUANTAS = 7               # a grade da página inicial tem 7 fotos
TEMPO_LIMITE = 4          # segundos: a página inicial não pode ficar esperando
CACHE_FOTOS = 60 * 60     # 1 hora
CACHE_FALHA = 15 * 60     # depois de uma falha, 15 minutos sem tentar
RENOVAR_A_CADA = timedelta(days=7)
# O Instagram recusa renovar token com menos de 24 h; depois de uma tentativa
# (certa ou errada) espera um pouco antes da próxima.
INTERVALO_TENTATIVAS = 6 * 60 * 60

CHAVE_FOTOS = 'instagram:fotos'
CHAVE_TENTATIVA = 'instagram:tentou-renovar'


class ErroInstagram(Exception):
    pass


def _token_do_env():
    return settings.INSTAGRAM_TOKEN


def _impressao(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _guardado(token_env):
    """O token renovado no banco, se ele veio do token que está no .env agora."""
    from .models import TokenInstagram
    salvo = TokenInstagram.objects.first()
    if salvo and salvo.origem == _impressao(token_env):
        return salvo
    return None


def configurado():
    return bool(_token_do_env())


def token_atual():
    token_env = _token_do_env()
    if not token_env:
        return ''
    salvo = _guardado(token_env)
    return salvo.token if salvo else token_env


def _pedir(url, parametros):
    endereco = '{}?{}'.format(url, parse.urlencode(parametros))
    try:
        with http.urlopen(endereco, timeout=TEMPO_LIMITE) as resposta:
            return json.loads(resposta.read().decode())
    except error.HTTPError as erro:
        # a mensagem do Instagram ajuda a entender (token vencido, sem
        # permissão...) e não traz o token; o endereço traz, então não vai pro log
        try:
            detalhe = json.loads(erro.read().decode()).get('error', {}).get('message', '')
        except (ValueError, AttributeError):
            detalhe = ''
        raise ErroInstagram('HTTP {} {}'.format(erro.code, detalhe).strip()) from None
    except (error.URLError, TimeoutError, ValueError, OSError) as erro:
        raise ErroInstagram(type(erro).__name__) from None


def renovar():
    """Troca o token atual por um novo (mais 60 dias) e guarda no banco.

    Devolve a data em que o token novo vence. Levanta ErroInstagram se o
    Instagram recusar (token com menos de 24 h, vencido ou revogado).
    """
    from .models import TokenInstagram

    token_env = _token_do_env()
    if not token_env:
        raise ErroInstagram('SOAR_INSTAGRAM_TOKEN não está no .env')
    dados = _pedir(URL_RENOVAR, {'grant_type': 'ig_refresh_token',
                                 'access_token': token_atual()})
    novo = dados.get('access_token')
    if not novo:
        raise ErroInstagram('o Instagram não devolveu token')
    agora = timezone.now()
    segundos = int(dados.get('expires_in') or 0)
    expira = agora + timedelta(seconds=segundos) if segundos else None
    TokenInstagram.objects.all().delete()
    TokenInstagram.objects.create(token=novo, origem=_impressao(token_env),
                                  renovado_em=agora, expira_em=expira)
    log.info('Token do Instagram renovado; vence em %s', expira)
    return expira


def precisa_renovar():
    token_env = _token_do_env()
    if not token_env:
        return False
    salvo = _guardado(token_env)
    # sem nada no banco, a idade do token do .env é desconhecida: tenta
    return salvo is None or timezone.now() - salvo.renovado_em >= RENOVAR_A_CADA


def renovar_se_preciso():
    """Renova quando passou da hora, sem insistir se o Instagram recusar."""
    if not precisa_renovar() or not cache.add(CHAVE_TENTATIVA, 1, INTERVALO_TENTATIVAS):
        return
    try:
        renovar()
    except ErroInstagram as erro:
        log.warning('Não deu para renovar o token do Instagram: %s', erro)


def _foto(item):
    # vídeo e reels: a capa; foto e carrossel: a própria imagem
    if item.get('media_type') == 'VIDEO':
        imagem = item.get('thumbnail_url')
    else:
        imagem = item.get('media_url')
    if not imagem or not imagem.startswith('https://'):
        return None
    legenda = (item.get('caption') or '').strip().split('\n')[0][:120]
    link = item.get('permalink') or PERFIL
    return {'foto': imagem, 'link': link if link.startswith('https://') else PERFIL,
            'legenda': legenda}


def ultimas_fotos():
    """As últimas fotos do perfil, ou [] se não houver token ou o Instagram falhar."""
    if not configurado():
        return []
    fotos = cache.get(CHAVE_FOTOS)
    if fotos is not None:
        return fotos

    renovar_se_preciso()
    try:
        dados = _pedir(URL_FOTOS, {'fields': CAMPOS, 'limit': QUANTAS * 2,
                                   'access_token': token_atual()})
    except ErroInstagram as erro:
        log.warning('Não deu para buscar as fotos do Instagram: %s', erro)
        cache.set(CHAVE_FOTOS, [], CACHE_FALHA)
        return []

    fotos = [f for f in map(_foto, dados.get('data') or []) if f][:QUANTAS]
    cache.set(CHAVE_FOTOS, fotos, CACHE_FOTOS if fotos else CACHE_FALHA)
    return fotos
