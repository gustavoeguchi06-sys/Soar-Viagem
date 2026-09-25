"""Código de indicação das agências.

Em três passos porque cada agência que já existe precisa de um código
diferente: o default de uma coluna nova é calculado uma vez só e repetiria o
mesmo código para todas, o que quebraria o `unique`.
"""
from django.db import migrations, models

import contas.models


def preencher_codigos(apps, schema_editor):
    PerfilAgente = apps.get_model('contas', 'PerfilAgente')
    usados = set()
    for agente in PerfilAgente.objects.all():
        codigo = contas.models.gerar_codigo_indicacao()
        while codigo in usados:
            codigo = contas.models.gerar_codigo_indicacao()
        usados.add(codigo)
        agente.codigo = codigo
        agente.save(update_fields=['codigo'])


class Migration(migrations.Migration):

    dependencies = [
        ('contas', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilagente',
            name='codigo',
            field=models.CharField(max_length=12, null=True, editable=False,
                                   verbose_name='Código de indicação'),
        ),
        migrations.RunPython(preencher_codigos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='perfilagente',
            name='codigo',
            field=models.CharField(
                default=contas.models.gerar_codigo_indicacao, editable=False,
                help_text='Vai no link que a agência manda para os clientes. Quem reserva '
                          'por esse link aparece no painel da agência.',
                max_length=12, unique=True, verbose_name='Código de indicação'),
        ),
    ]
