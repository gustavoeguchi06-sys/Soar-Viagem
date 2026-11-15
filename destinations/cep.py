"""Endereço do CEP que o cliente digitou no "Saiba mais", para o painel do dono.

Consulta o ViaCEP (base pública dos Correios) e guarda no pedido: rua,
complemento, bairro, cidade e UF. Só o dono vê (destinations/admin.py,
Interessados); o cliente não vê nada disso.

A consulta tem tempo curto: se o ViaCEP demorar ou estiver fora, o pedido
entra do mesmo jeito e o painel tenta de novo quando o dono abrir a ficha.
"""
import json
import logging
import re
from urllib import error, request as http

from django.conf import settings
from django.utils import timezone

log = logging.getLogger('soar.cep')

URL = 'https://viacep.com.br/ws/{}/json/'
TEMPO_LIMITE = 2   # segundos: o cliente espera isso no máximo ao enviar


def buscar(cep):
    """{'endereco', 'bairro', 'cidade', 'uf'}; {} se o CEP não existe; None se não deu para consultar."""
    if not settings.CEP_CONSULTA_ATIVA:
        return None
    numeros = re.sub(r'\D', '', cep or '')
    if len(numeros) != 8:
        return {}
    pedido = http.Request(URL.format(numeros), headers={'User-Agent': 'SoarOperadora/1.0'})
    try:
        with http.urlopen(pedido, timeout=TEMPO_LIMITE) as resposta:
            dados = json.loads(resposta.read().decode())
    except (error.URLError, TimeoutError, ValueError, OSError) as erro:
        log.info('viacep sem resposta: cep=%s erro=%s', numeros, type(erro).__name__)
        return None
    if not isinstance(dados, dict) or dados.get('erro'):
        return {}
    rua = ', '.join(p for p in (dados.get('logradouro', ''), dados.get('complemento', '')) if p)
    return {'endereco': rua[:200], 'bairro': (dados.get('bairro') or '')[:100],
            'cidade': (dados.get('localidade') or '')[:100], 'uf': (dados.get('uf') or '')[:2]}


def preencher(interessado):
    """Consulta o CEP do pedido e grava o endereço. True se consultou (achando ou não)."""
    achado = buscar(interessado.cep)
    if achado is None:
        return False
    interessado.cep_endereco = achado.get('endereco', '')
    interessado.cep_bairro = achado.get('bairro', '')
    interessado.cep_cidade = achado.get('cidade', '')
    interessado.cep_uf = achado.get('uf', '')
    interessado.cep_consultado_em = timezone.now()
    if interessado.pk:
        type(interessado).objects.filter(pk=interessado.pk).update(
            cep_endereco=interessado.cep_endereco, cep_bairro=interessado.cep_bairro,
            cep_cidade=interessado.cep_cidade, cep_uf=interessado.cep_uf,
            cep_consultado_em=interessado.cep_consultado_em)
    return True
