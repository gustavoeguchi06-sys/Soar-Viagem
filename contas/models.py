"""Perfil das agências de viagem (B2B).

O site usa o `User` do Django para todo mundo. Cada agente de viagens é um
`User` com um perfil a mais preso a ele: razão social, CNPJ e WhatsApp da
agência — os dados que a Soar precisa para conferir a agência e trabalhar a
comissão. O nome do agente e o e-mail ficam no próprio `User`.

Uma mesma agência (o mesmo CNPJ) pode ter vários agentes, cada um com o seu
login. Por isso o CNPJ se repete, e o que identifica quem atende é o nome do
agente. O CADASTUR de empresa usa o próprio número do CNPJ: ele é preenchido
sozinho, igual ao CNPJ.
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


def validar_cpf(valor):
    """Valida um CPF pelos dois dígitos verificadores (com ou sem máscara)."""
    cpf = so_digitos(valor)
    if len(cpf) != 11:
        raise ValidationError('CPF inválido: precisa ter 11 números.')
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11 % 10
        if int(cpf[tamanho]) != digito:
            raise ValidationError('CPF inválido: os dígitos verificadores não conferem.')


def formatar_cpf(valor):
    """'12345678909' -> '123.456.789-09' (depois de validar)."""
    cpf = so_digitos(valor)
    validar_cpf(cpf)
    return '{}.{}.{}-{}'.format(cpf[:3], cpf[3:6], cpf[6:9], cpf[9:])


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
    """Um agente de viagens de uma agência parceira, preso ao usuário que faz login."""

    usuario = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name='agente', verbose_name='Usuário')
    razao_social = models.CharField('Razão social', max_length=160)
    # Sem unique: vários agentes da mesma agência se cadastram com o mesmo CNPJ.
    cnpj = models.CharField('CNPJ', max_length=14, db_index=True,
                            validators=[validar_cnpj],
                            help_text='14 números, sem pontos nem barra. Pode repetir: '
                                      'cada agente da agência tem o seu cadastro.')
    cadastur = models.CharField('CADASTUR', max_length=30, blank=True, editable=False,
                                help_text='O CADASTUR da empresa é o próprio número do CNPJ: '
                                          'preenchido sozinho.')
    whatsapp = models.CharField('WhatsApp', max_length=20)
    aprovado = models.BooleanField('Aprovado pela Soar', default=False,
                                   help_text='Marque depois de conferir o CNPJ da agência.')
    codigo = models.CharField(
        'Código de indicação', max_length=12, unique=True, default=gerar_codigo_indicacao,
        editable=False,
        help_text='Vai no link que a agência manda para os clientes. Quem reserva '
                  'por esse link aparece no painel da agência.')
    criado_em = models.DateTimeField('Cadastrado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Agente B2B'
        verbose_name_plural = 'Agentes B2B'
        ordering = ['razao_social', 'usuario__first_name']

    def __str__(self):
        # O nome do agente vem primeiro: a mesma agência pode ter vários, e o
        # dono precisa saber para quem está mandando o cliente.
        return '{} — {} ({})'.format(self.nome_agente, self.razao_social, self.cnpj_formatado)

    def save(self, *args, **kwargs):
        self.cadastur = self.cnpj_formatado
        super().save(*args, **kwargs)

    @property
    def nome_agente(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def cnpj_formatado(self):
        c = self.cnpj
        if len(c) == 14:
            return '{}.{}.{}/{}-{}'.format(c[:2], c[2:5], c[5:8], c[8:12], c[12:])
        return c


class DoisFatores(models.Model):
    """Segredo do aplicativo autenticador de uma conta (contas/totp.py).

    Só a equipe é obrigada a ter (SOAR_2FA_EQUIPE). A senha sozinha não basta
    para o painel do dono: quem a descobrir ainda precisaria do celular.
    """

    usuario = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name='dois_fatores')
    segredo = models.CharField(max_length=64)
    # Passo (janela de 30 s) do último código aceito: o mesmo código não entra duas vezes.
    ultimo_passo = models.BigIntegerField(default=0)
    ativado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Verificação em duas etapas'
        verbose_name_plural = 'Verificação em duas etapas'

    def __str__(self):
        return self.usuario.get_username()
