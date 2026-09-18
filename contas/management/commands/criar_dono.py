# -*- coding: utf-8 -*-
"""Cria (ou promove) a conta master do dono do site.

    python manage.py criar_dono

A senha nunca vem por parâmetro nem fica escrita em lugar nenhum: o comando
pergunta na hora e o Django guarda só o hash. É o mesmo que o
`createsuperuser` faz — a diferença é que aqui a conta já entra no grupo
"Dono do site", que é o que aparece no painel.
"""
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from getpass import getpass

GRUPO = 'Dono do site'


class Command(BaseCommand):
    help = 'Cria ou promove a conta master (dono) que administra o site pelo /painel/.'

    def add_arguments(self, parser):
        parser.add_argument('--usuario', help='Nome de usuário do dono.')
        parser.add_argument('--email', help='E-mail do dono.')
        parser.add_argument('--promover', action='store_true',
                            help='Só dá acesso de dono a um usuário que já existe, '
                                 'sem mexer na senha.')

    def handle(self, *args, **opcoes):
        usuario_nome = opcoes.get('usuario') or input('Nome de usuário do dono: ').strip()
        if not usuario_nome:
            raise CommandError('O nome de usuário não pode ficar em branco.')

        usuario = User.objects.filter(username=usuario_nome).first()

        if usuario is None:
            if opcoes['promover']:
                raise CommandError('Não existe usuário "{}" para promover.'.format(usuario_nome))
            email = opcoes.get('email') or input('E-mail do dono: ').strip()
            senha = self._perguntar_senha(usuario_nome, email)
            usuario = User.objects.create_user(username=usuario_nome, email=email, password=senha)
            self.stdout.write(self.style.SUCCESS('Conta "{}" criada.'.format(usuario_nome)))
        else:
            if opcoes.get('email'):
                usuario.email = opcoes['email']
            self.stdout.write('Usuário "{}" já existe — dando acesso de dono.'.format(usuario_nome))

        usuario.is_staff = True         # entra no /painel/
        usuario.is_superuser = True     # mexe em tudo lá dentro
        usuario.save()

        grupo, _ = Group.objects.get_or_create(name=GRUPO)
        usuario.groups.add(grupo)

        self.stdout.write(self.style.SUCCESS(
            'Pronto! "{}" agora é dono do site. Entre em /painel/ com essa conta.'.format(
                usuario_nome)))

    def _perguntar_senha(self, usuario_nome, email):
        """Pede a senha duas vezes e passa pelas regras do próprio Django."""
        while True:
            senha = getpass('Senha: ')
            if senha != getpass('Repita a senha: '):
                self.stderr.write('As senhas não conferem. Vamos de novo.')
                continue
            try:
                validate_password(senha, User(username=usuario_nome, email=email))
            except ValidationError as erro:
                for mensagem in erro.messages:
                    self.stderr.write('  · {}'.format(mensagem))
                continue
            return senha
