from datetime import timedelta

from django.db import migrations, models


def preencher_validade(apps, schema_editor):
    """Orçamentos que já existiam passam a valer 72 horas a partir de quando foram criados."""
    Orcamento = apps.get_model('agencia', 'Orcamento')
    for orcamento in Orcamento.objects.filter(valido_ate__isnull=True):
        orcamento.valido_ate = orcamento.criado_em + timedelta(hours=72)
        orcamento.save(update_fields=['valido_ate'])


class Migration(migrations.Migration):

    dependencies = [
        ('agencia', '0004_idade_chd_ate_8'),
    ]

    operations = [
        migrations.AddField(
            model_name='orcamento',
            name='valido_ate',
            field=models.DateTimeField(blank=True, help_text='72 horas depois de criado.',
                                       null=True, verbose_name='Válido até'),
        ),
        migrations.RunPython(preencher_validade, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='orcamento',
            name='validade',
        ),
        migrations.AlterField(
            model_name='orcamento',
            name='valor',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True,
                                      help_text='Adultos pela tabela da viagem; crianças sob consulta.',
                                      verbose_name='Valor total (R$)'),
        ),
    ]
