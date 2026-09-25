"""Perfil das agências de viagem (B2B).

O site usa o `User` do Django para todo mundo. Uma agência é um `User` como
outro qualquer, com um perfil a mais preso a ele: razão social, CNPJ, CADASTUR
e WhatsApp — os dados que a Soar precisa para conferir a agência e trabalhar a
comissão. O nome completo e o e-mail ficam no próprio `User`.
"""
import re
import secrets

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


def so_digitos(valor):
    """Deixa só os números — o CNPJ é guardado sem pontos nem barra."""
    return re.sub(r'\D', '', valor or '')


def _digito(base, pesos):
    soma = sum(int(n) * p for n, p in zip(base, pesos))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def validar_cnpj(valor):
    """Valida um CNPJ pelos dois dígitos verificadores.

    Aceita com ou sem máscara; guarda-se só os 14 dígitos. Um CNPJ com todos os
    números iguais (ex.: 00000000000000) passa nas contas mas não existe, então
    é barrado à parte.
    """
    cnpj = so_digitos(valor)
    if len(cnpj) != 14:
        raise ValidationError('CNPJ inválido: precisa ter 14 números.')
    if cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido.')
    d1 = _digito(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _digito(cnpj[:12] + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    if cnpj[12:] != d1 + d2:
        raise ValidationError('CNPJ inválido: os dígitos verificadores não conferem.')


# Sem 0/O e 1/I/L: o código é lido em voz alta e digitado à mão.
_LETRAS_CODIGO = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def gerar_codigo_indicacao():
    return ''.join(secrets.choice(_LETRAS_CODIGO) for _ in range(8))


class PerfilAgente(models.Model):
    """Dados da agência parceira, presos ao usuário que faz login."""

    usuario = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name='agente', verbose_name='Usuário')
    razao_social = models.CharField('Razão social', max_length=160)
    cnpj = models.CharField('CNPJ', max_length=14, unique=True,
                            validators=[validar_cnpj],
                            help_text='14 números, sem pontos nem barra.')
    cadastur = models.CharField('CADASTUR', max_length=30)
    whatsapp = models.CharField('WhatsApp', max_length=20)
    aprovado = models.BooleanField('Aprovado pela Soar', default=False,
                                   help_text='Marque depois de conferir o CNPJ e o CADASTUR da agência.')
    codigo = models.CharField(
        'Código de indicação', max_length=12, unique=True, default=gerar_codigo_indicacao,
        editable=False,
        help_text='Vai no link que a agência manda para os clientes. Quem reserva '
                  'por esse link aparece no painel da agência.')
    criado_em = models.DateTimeField('Cadastrado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Agente B2B'
        verbose_name_plural = 'Agentes B2B'
        ordering = ['razao_social']

    def __str__(self):
        return '{} ({})'.format(self.razao_social, self.cnpj_formatado)

    @property
    def cnpj_formatado(self):
        c = self.cnpj
        if len(c) == 14:
            return '{}.{}.{}/{}-{}'.format(c[:2], c[2:5], c[5:8], c[8:12], c[12:])
        return c
