"""Limite de tentativas e registro de eventos de segurança.

Duas coisas que o projeto não tinha e que andam juntas: impedir que alguém
tente senha à vontade, e deixar registrado quem tentou. Sem a segunda, a
primeira não tem como ser acompanhada.

A contagem vive no cache (`CACHES['default']`). Em desenvolvimento isso é
memória do processo; em produção, aponte SOAR_REDIS_URL para um Redis, senão
cada worker conta separado e o limite fica mais frouxo do que parece.
"""
import logging

from django.conf import settings
from django.core.cache import cache

log = logging.getLogger('soar.seguranca')


def ip_do_cliente(request):
    """IP de quem fez a requisição.

    Atrás de proxy, o IP real vem no X-Forwarded-For — mas esse cabeçalho é
    escrito pelo cliente e só dá para confiar nele quando existe um proxy
    nosso na frente reescrevendo o valor. Por isso ele só é lido quando
    SOAR_ATRAS_DE_PROXY está ligado; sem isso, qualquer um driblaria o limite
    mandando um cabeçalho falso a cada tentativa.
    """
    if getattr(settings, 'SECURE_PROXY_SSL_HEADER', None):
        encaminhado = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if encaminhado:
            return encaminhado.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or 'desconhecido'


class Limite:
    """Contador de tentativas por chave, com janela de tempo.

    Uso:
        limite = Limite('login', tentativas=5, janela=900)
        if limite.estourou(request, usuario):    # bloqueado?
            ...
        limite.registrar(request, usuario)       # +1 tentativa
        limite.limpar(request, usuario)          # deu certo, zera
    """

    def __init__(self, nome, tentativas, janela):
        self.nome = nome
        self.tentativas = tentativas
        self.janela = janela

    def _chaves(self, request, identificador=None):
        """Conta por IP e, quando existe, também por identificador.

        Só por IP puniria todo mundo atrás do mesmo NAT; só pelo usuário
        deixaria alguém varrer uma lista de contas de um IP só. As duas
        contagens juntas cobrem os dois casos.
        """
        chaves = ['limite:{}:ip:{}'.format(self.nome, ip_do_cliente(request))]
        if identificador:
            chaves.append('limite:{}:id:{}'.format(self.nome, str(identificador).lower()))
        return chaves

    def estourou(self, request, identificador=None):
        return any(cache.get(chave, 0) >= self.tentativas
                   for chave in self._chaves(request, identificador))

    def registrar(self, request, identificador=None):
        for chave in self._chaves(request, identificador):
            try:
                total = cache.incr(chave)
            except ValueError:                      # primeira tentativa da janela
                cache.set(chave, 1, self.janela)
                total = 1
            if total == self.tentativas:
                log.warning(
                    'limite atingido: %s chave=%s tentativas=%d janela=%ds ip=%s',
                    self.nome, chave, total, self.janela, ip_do_cliente(request),
                )

    def limpar(self, request, identificador=None):
        cache.delete_many(self._chaves(request, identificador))

    def segundos_restantes(self, request, identificador=None):
        """Quanto falta para liberar — só para a mensagem ao usuário."""
        return self.janela


# Limites usados pelas views. Os números vêm do settings para poderem ser
# ajustados sem mexer no código.
LIMITE_LOGIN = Limite('login',
                      settings.LIMITE_LOGIN_TENTATIVAS,
                      settings.LIMITE_LOGIN_JANELA)
LIMITE_CADASTRO = Limite('cadastro', settings.LIMITE_CADASTRO_POR_HORA, 3600)
LIMITE_AVALIACAO = Limite('avaliacao', settings.LIMITE_AVALIACAO_POR_HORA, 3600)
LIMITE_RESERVA = Limite('reserva', settings.LIMITE_RESERVA_POR_HORA, 3600)


def registrar_login_falho(sender, credentials, request=None, **kwargs):
    """Ligado ao sinal `user_login_failed` do Django.

    Guarda o usuário tentado e o IP. A senha vem em `credentials` e **não** é
    registrada — o Django já a mascara, e log de senha errada é vazamento de
    senha na hora em que alguém digita a certa no campo errado.
    """
    log.warning(
        'login falhou: usuario=%r ip=%s',
        credentials.get('username', ''),
        ip_do_cliente(request) if request else 'desconhecido',
    )


def registrar_login_ok(sender, request, user, **kwargs):
    log.info('login ok: usuario=%r staff=%s ip=%s',
             user.get_username(), user.is_staff, ip_do_cliente(request))
