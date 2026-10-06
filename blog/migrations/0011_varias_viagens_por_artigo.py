"""O artigo passa a ligar mais de uma viagem; a viagem que já estava ligada continua."""
from django.db import migrations, models


def copiar(apps, schema_editor):
    Artigo = apps.get_model('blog', 'Artigo')
    for artigo in Artigo.objects.exclude(destino=None):
        artigo.destinos.add(artigo.destino_id)


def voltar(apps, schema_editor):
    Artigo = apps.get_model('blog', 'Artigo')
    for artigo in Artigo.objects.all():
        primeira = artigo.destinos.first()
        if primeira:
            artigo.destino = primeira
            artigo.save(update_fields=['destino'])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0010_autor_equipe_soar'),
        ('destinations', '0030_texto_inicial_soar_60'),
    ]

    operations = [
        # nome provisório no caminho de volta, para não brigar com o 'artigos' do campo antigo
        migrations.AddField(
            model_name='artigo',
            name='destinos',
            field=models.ManyToManyField(blank=True, related_name='artigos_novos',
                                         to='destinations.destino'),
        ),
        migrations.RunPython(copiar, voltar),
        migrations.RemoveField(model_name='artigo', name='destino'),
        migrations.AlterField(
            model_name='artigo',
            name='destinos',
            field=models.ManyToManyField(
                blank=True, related_name='artigos', to='destinations.destino',
                verbose_name='Viagens ligadas ao artigo',
                help_text='Opcional. O final do artigo ganha um botão para a página de cada viagem.'),
        ),
    ]
