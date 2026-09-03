# -*- coding: utf-8 -*-
"""Mantém no ar as avaliações que já estavam publicadas.

O campo `publicada` nasceu com `default=False`, para que toda avaliação nova
passe pela moderação do painel. Aplicado sozinho, isso tiraria do site as
avaliações que já estavam lá — que foram publicadas sob a regra antiga e não
têm por que sumir da noite para o dia.

Esta migração aprova o que já existia. Da próxima em diante, vale a fila.
"""
from django.db import migrations


def publicar_antigas(apps, schema_editor):
    Avaliacao = apps.get_model('reviews', 'Avaliacao')
    Avaliacao.objects.filter(autor__isnull=True).update(publicada=True)


def despublicar(apps, schema_editor):
    """Volta ao estado do campo recém-criado, para o caso de desfazer."""
    Avaliacao = apps.get_model('reviews', 'Avaliacao')
    Avaliacao.objects.update(publicada=False)


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_avaliacao_autor_avaliacao_ip_avaliacao_publicada_and_more'),
    ]

    operations = [
        migrations.RunPython(publicar_antigas, despublicar),
    ]
