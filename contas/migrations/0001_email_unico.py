# -*- coding: utf-8 -*-
"""Índice único no e-mail do usuário.

O login por e-mail (contas/forms.py) traduz endereço em usuário com
`filter(email__iexact=...).first()`. Esse `.first()` só faz sentido se existir
no máximo um usuário por endereço — e o `User` do Django **não** garante isso:
`email` não tem UNIQUE. A única barreira era a validação do formulário de
cadastro, que o painel administrativo, o comando `criar_dono` e dois cadastros
simultâneos passavam por cima sem esforço.

Com e-mails repetidos, o `.first()` escolhe em silêncio a conta de menor id: a
pessoa digita o próprio endereço e a própria senha e é recusada, porque a
autenticação está sendo tentada contra outra conta.

A regra vai para o banco, que é onde ela não tem como ser contornada.
"""
from django.conf import settings
from django.db import migrations


def conferir_duplicatas(apps, schema_editor):
    """Recusa a migração se já houver e-mail repetido.

    Deduplicar sozinho significaria decidir qual conta perde o endereço — e
    isso é decisão de quem opera o site, não de uma migração. Melhor parar e
    dizer exatamente o que precisa ser resolvido.
    """
    Usuario = apps.get_model('auth', 'User')
    vistos, repetidos = {}, set()
    for pk, email in Usuario.objects.exclude(email='').values_list('pk', 'email'):
        chave = email.lower()
        if chave in vistos:
            repetidos.add(chave)
        vistos[chave] = pk

    if repetidos:
        raise RuntimeError(
            'Não dá para criar o índice único: estes e-mails aparecem em mais de uma '
            'conta — {}. Decida qual conta fica com cada endereço (o painel em /painel/ '
            'edita o e-mail), apague ou esvazie o campo das outras, e rode a migração '
            'de novo.'.format(', '.join(sorted(repetidos)))
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(conferir_duplicatas, migrations.RunPython.noop),
        migrations.RunSQL(
            # LOWER() porque o login compara sem diferenciar maiúsculas.
            # O WHERE deixa de fora as contas sem e-mail (superusuário criado
            # pelo createsuperuser pode não ter), que senão colidiriam entre si.
            sql="CREATE UNIQUE INDEX auth_user_email_unico "
                "ON auth_user (LOWER(email)) WHERE email <> '';",
            reverse_sql="DROP INDEX auth_user_email_unico;",
        ),
    ]
