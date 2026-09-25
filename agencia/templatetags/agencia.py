import re

from django import template

register = template.Library()


@register.filter
def whatsapp(telefone):
    """(11) 98888-7777 vira https://wa.me/5511988887777. Número curto: vazio."""
    numeros = re.sub(r'\D', '', telefone or '')
    if len(numeros) < 10:
        return ''
    if not numeros.startswith('55'):
        numeros = '55' + numeros
    return 'https://wa.me/' + numeros


@register.filter
def reais(valor):
    """Decimal('6776.5') vira 6.776,50."""
    if valor is None:
        return ''
    inteiro, centavos = f'{valor:,.2f}'.split('.')
    return inteiro.replace(',', '.') + ',' + centavos
