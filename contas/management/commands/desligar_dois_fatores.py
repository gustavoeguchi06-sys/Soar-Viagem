"""Desliga a verificação em duas etapas de uma conta (celular perdido ou trocado).

    python manage.py desligar_dois_fatores <usuario>

Roda só no servidor, por quem tem acesso a ele: é justamente isso que impede
um invasor com a senha de desligar a proteção pelo site. Na próxima entrada no
painel a pessoa cadastra o celular novo.
"""
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from contas.models import DoisFatores

log = logging.getLogger('soar.seguranca')


class Command(BaseCommand):
    help = 'Desliga a verificação em duas etapas de uma conta (celular perdido ou trocado).'

    def add_arguments(self, parser):
        parser.add_argument('usuario')

    def handle(self, *args, usuario, **options):
        conta = User.objects.filter(username__iexact=usuario).first()
        if conta is None:
            raise CommandError('Não existe conta com o usuário {!r}.'.format(usuario))
        apagados, _ = DoisFatores.objects.filter(usuario=conta).delete()
        if not apagados:
            self.stdout.write('A conta {} não tinha verificação em duas etapas.'.format(
                conta.get_username()))
            return
        log.warning('2fa desligado pelo servidor: usuario=%r', conta.get_username())
        self.stdout.write('Pronto. Na próxima entrada no painel, {} cadastra o celular '
                          'novo.'.format(conta.get_username()))
