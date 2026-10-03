"""Leva o preço antigo (um valor de casal, com os outros quartos calculados) para
a tabela nova de preços por quarto, com os mesmos valores que o site mostrava.

Antes: Single = casal + 1.400, Duplo = casal, Triplo = casal - 200. Depois da
migração cada valor fica gravado e o dono muda um sem mexer nos outros. O "a
partir de" passa a ser o menor deles.
"""
from decimal import Decimal

from django.db import migrations

DIFERENCAS = {'single': Decimal('1400'), 'casal': Decimal('0'), 'duplo': Decimal('0'),
              'triplo': Decimal('-200')}


def para_tabela(apps, schema_editor):
    Destino = apps.get_model('destinations', 'Destino')
    PrecoQuarto = apps.get_model('destinations', 'PrecoQuarto')
    for destino in Destino.objects.filter(preco_base__isnull=False):
        if PrecoQuarto.objects.filter(destino=destino).exists():
            continue
        precos = {tipo: destino.preco_base + d for tipo, d in DIFERENCAS.items()}
        PrecoQuarto.objects.bulk_create([PrecoQuarto(destino=destino, tipo=tipo, preco=preco)
                                         for tipo, preco in precos.items()])
        destino.preco_base = min(precos.values())
        destino.save(update_fields=['preco_base'])


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0019_precos_por_quarto'),
    ]

    operations = [
        migrations.RunPython(para_tabela, migrations.RunPython.noop),
    ]
