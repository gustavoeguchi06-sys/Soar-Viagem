"""Formato brasileiro de telefone, CNPJ e CADASTUR, do lado do servidor.

O navegador já aplica a máscara enquanto a pessoa digita (static/js/
mascaras.js). Isto aqui é a outra metade: garante o mesmo formato mesmo quando
o JavaScript não roda, e recusa número com quantidade errada de dígitos.
"""
import re

from django.core.exceptions import ValidationError


def digitos(valor):
    return re.sub(r'\D', '', valor or '')


def formatar_telefone(valor):
    """'11988887777' -> '(11) 98888-7777'; '1133334444' -> '(11) 3333-4444'.

    Aceita o número com ou sem o 55 do Brasil na frente. Vazio fica vazio.
    """
    numeros = digitos(valor)
    if not numeros:
        return ''
    if len(numeros) in (12, 13) and numeros.startswith('55'):
        numeros = numeros[2:]
    if len(numeros) not in (10, 11):
        raise ValidationError('Telefone incompleto: digite o DDD e o número, '
                              'como (11) 98888-7777.')
    ddd, resto = numeros[:2], numeros[2:]
    return '({}) {}-{}'.format(ddd, resto[:-4], resto[-4:])


def formatar_cadastur(valor):
    """O número do certificado CADASTUR de empresa: 00.000000.00.0000-0."""
    numeros = digitos(valor)
    if len(numeros) != 15:
        raise ValidationError('O CADASTUR tem 15 números, no formato 00.000000.00.0000-0, '
                              'como aparece no certificado.')
    return '{}.{}.{}.{}-{}'.format(numeros[:2], numeros[2:8], numeros[8:10],
                                   numeros[10:14], numeros[14])
