"""Tira o travessão (—) dos textos de viagem já gravados no banco.

O conteúdo padrão (destinations/conteudo.py) já foi reescrito sem ele; esta
migração acerta o que o `importar_conteudo` copiou para o banco antes disso.
Só mexe nos trechos conhecidos. Texto que o dono escreveu no painel com outra
redação fica como está.
"""
import re

from django.db import migrations

TROCAS = [
    ('Leve documento oficial com foto — RG ou CNH dentro da validade.',
     'Leve documento oficial com foto (RG ou CNH) dentro da validade.'),
    ('dunas alaranjadas — o cartão-postal', 'dunas alaranjadas, o cartão-postal'),
]
DIA = re.compile(r'^Dia (\d+) — ')


def _limpar(texto):
    for antigo, novo in TROCAS:
        texto = texto.replace(antigo, novo)
    return texto


def tirar_travessao(apps, schema_editor):
    Destino = apps.get_model('destinations', 'Destino')
    DiaRoteiro = apps.get_model('destinations', 'DiaRoteiro')

    for dia in DiaRoteiro.objects.filter(titulo__contains='—') | DiaRoteiro.objects.filter(detalhe__contains='—'):
        dia.titulo = DIA.sub(r'Dia \1: ', dia.titulo)
        dia.detalhe = _limpar(dia.detalhe)
        dia.save(update_fields=['titulo', 'detalhe'])

    for destino in Destino.objects.filter(informacoes__contains='—'):
        destino.informacoes = _limpar(destino.informacoes)
        destino.save(update_fields=['informacoes'])


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0008_alter_diaroteiro_titulo'),
    ]

    operations = [
        migrations.RunPython(tirar_travessao, migrations.RunPython.noop),
    ]
