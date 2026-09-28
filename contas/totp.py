"""Código de 6 dígitos do aplicativo autenticador (TOTP, RFC 6238).

É o mesmo esquema do Google Authenticator, Microsoft Authenticator, Authy e
afins: o site e o celular guardam o mesmo segredo, e a cada 30 segundos os
dois calculam o mesmo código a partir dele e do relógio. Feito só com a
biblioteca padrão do Python, para não trazer dependência nova.
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote, urlencode

PERIODO = 30          # segundos de validade de cada código
DIGITOS = 6
# Aceita o código do passo anterior e do seguinte: o relógio do celular pode
# estar alguns segundos adiantado ou atrasado, e a pessoa pode digitar o
# código no finzinho da validade.
TOLERANCIA = 1


def novo_segredo():
    """160 bits aleatórios em base32, o formato que os aplicativos leem."""
    return base64.b32encode(secrets.token_bytes(20)).decode('ascii')


def segredo_em_grupos(segredo):
    """"ABCD EFGH ..." — mais fácil de digitar à mão no aplicativo."""
    return ' '.join(segredo[i:i + 4] for i in range(0, len(segredo), 4))


def passo_atual(agora=None):
    return int((time.time() if agora is None else agora) // PERIODO)


def codigo(segredo, passo):
    chave = base64.b32decode(segredo.upper() + '=' * (-len(segredo) % 8))
    resumo = hmac.new(chave, struct.pack('>Q', passo), hashlib.sha1).digest()
    inicio = resumo[-1] & 0x0F
    numero = struct.unpack('>I', resumo[inicio:inicio + 4])[0] & 0x7FFFFFFF
    return str(numero % 10 ** DIGITOS).zfill(DIGITOS)


def conferir(segredo, digitado, ultimo_passo_usado=0, agora=None):
    """Devolve o passo do código se ele confere, ou None.

    Um código que já foi usado (passo <= `ultimo_passo_usado`) é recusado:
    quem viu a pessoa digitar não consegue reaproveitar o mesmo código.
    """
    digitado = ''.join(c for c in str(digitado or '') if c.isdigit())
    if len(digitado) != DIGITOS:
        return None
    atual = passo_atual(agora)
    for passo in range(atual - TOLERANCIA, atual + TOLERANCIA + 1):
        if passo <= ultimo_passo_usado:
            continue
        if hmac.compare_digest(codigo(segredo, passo), digitado):
            return passo
    return None


def link_do_aplicativo(segredo, conta, emissor='Soar Operadora'):
    """otpauth://... — no celular, tocar no link abre o aplicativo autenticador."""
    rotulo = quote('{}:{}'.format(emissor, conta))
    return 'otpauth://totp/{}?{}'.format(rotulo, urlencode({
        'secret': segredo, 'issuer': emissor, 'digits': DIGITOS, 'period': PERIODO,
    }))
