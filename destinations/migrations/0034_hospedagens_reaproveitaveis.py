"""Hospedagem deixa de pertencer a um destino só e vira um cadastro próprio.

Cada destino passa a escolher as hospedagens (muitos para muitos). As que já
existiam continuam ligadas ao mesmo destino, com as fotos.
"""
from django.db import migrations, models


def ligar_aos_destinos(apps, schema_editor):
    Hospedagem = apps.get_model('destinations', 'Hospedagem')
    for hospedagem in Hospedagem.objects.exclude(destino_antigo=None):
        hospedagem.destino_antigo.hospedagens.add(hospedagem)


def voltar(apps, schema_editor):
    Hospedagem = apps.get_model('destinations', 'Hospedagem')
    for hospedagem in Hospedagem.objects.all():
        primeiro = hospedagem.destinos.order_by('pk').first()
        if primeiro:
            hospedagem.destino_antigo = primeiro
            hospedagem.save(update_fields=['destino_antigo'])


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0033_bate_volta'),
    ]

    operations = [
        # 1. a ligação antiga troca de nome, para liberar "destino.hospedagens"
        migrations.RenameField('hospedagem', 'destino', 'destino_antigo'),
        migrations.AlterField(
            model_name='hospedagem',
            name='destino_antigo',
            field=models.ForeignKey(null=True, blank=True, on_delete=models.deletion.SET_NULL,
                                    related_name='+', to='destinations.destino'),
        ),
        # 2. a ligação nova: um destino escolhe várias hospedagens e vice-versa
        migrations.AddField(
            model_name='destino',
            name='hospedagens',
            field=models.ManyToManyField(
                blank=True, related_name='destinos', to='destinations.hospedagem',
                verbose_name='Hospedagens do pacote',
                help_text='Escolha nas hospedagens já cadastradas (com as fotos). Não achou? '
                          'O "+" cadastra uma nova sem sair daqui.'),
        ),
        # 3. cada hospedagem continua no destino em que estava
        migrations.RunPython(ligar_aos_destinos, voltar),
        # 4. a ligação antiga sai
        migrations.RemoveField('hospedagem', 'destino_antigo'),
    ]
