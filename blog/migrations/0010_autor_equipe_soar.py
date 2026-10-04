"""O artigo do Jalapão volta a ser assinado pela "Equipe Soar".

A 0003 tinha posto um nome de pessoa que não é de ninguém da Soar. Como ela
roda também em banco novo (o do servidor), a troca fica aqui, depois dela.
"""
from django.db import migrations


def assinar_pela_equipe(apps, schema_editor):
    Artigo = apps.get_model('blog', 'Artigo')
    Artigo.objects.filter(autor='Camila Azevedo').update(autor='Equipe Soar')


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_etiqueta_sempre_verde'),
    ]

    operations = [
        migrations.RunPython(assinar_pela_equipe, migrations.RunPython.noop),
    ]
