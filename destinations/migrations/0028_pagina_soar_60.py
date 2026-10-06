"""A "Foto do Soar 60+" vira a página Soar 60+ inteira: o mesmo registro, com a foto que já estiver salva."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0027_foto_soar_60'),
    ]

    operations = [
        migrations.RenameModel('FotoSoar60', 'PaginaSoar60'),
    ]
