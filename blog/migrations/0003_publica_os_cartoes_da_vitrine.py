"""Deixa a vitrine do blog como era antes de ir para o painel.

A 0002 trouxe os sete cartões sem texto como rascunho, o que tirou os sete
do site. A vitrine deve continuar igual à de antes, com os oito cartões, e
o dono decide pelo painel o que apagar ou despublicar.
"""
from django.db import migrations

CARTOES = [
    'alter-do-chao', 'serra-da-canastra', 'santuario-do-caraca',
    'o-que-levar-na-mala-para-o-jalapao', 'por-que-viajar-em-grupo',
    'chapada-das-mesas', 'viagens-60-mais',
]


def publicar(apps, schema_editor):
    Artigo = apps.get_model('blog', 'Artigo')
    Artigo.objects.filter(slug__in=CARTOES).update(publicado=True)
    Artigo.objects.filter(slug='jalapao', autor='Equipe Soar').update(autor='Camila Azevedo')


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_conteudo_inicial'),
    ]

    operations = [
        migrations.RunPython(publicar, migrations.RunPython.noop),
    ]
