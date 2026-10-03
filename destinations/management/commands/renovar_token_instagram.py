# -*- coding: utf-8 -*-
"""Renova o token do Instagram antes de ele vencer (vence em 60 dias).

    python manage.py renovar_token_instagram           # só se passou de 7 dias
    python manage.py renovar_token_instagram --forcar  # renova agora

No servidor, deixe no cron uma vez por dia (ver deploy/DEPLOY.md). Mesmo sem
cron, a página inicial renova sozinha quando busca as fotos; o cron só garante
que a renovação aconteça mesmo numa semana sem visitas.
"""
from django.core.management.base import BaseCommand, CommandError

from destinations import instagram


class Command(BaseCommand):
    help = 'Renova o token do Instagram (SOAR_INSTAGRAM_TOKEN) para ele não vencer.'

    def add_arguments(self, parser):
        parser.add_argument('--forcar', action='store_true',
                            help='Renova agora, mesmo que a última renovação seja recente.')

    def handle(self, *args, **opcoes):
        if not instagram.configurado():
            raise CommandError('SOAR_INSTAGRAM_TOKEN não está no .env.')
        if not opcoes['forcar'] and not instagram.precisa_renovar():
            self.stdout.write('O token foi renovado há menos de 7 dias; nada a fazer.')
            return
        try:
            expira = instagram.renovar()
        except instagram.ErroInstagram as erro:
            raise CommandError('O Instagram recusou a renovação: {}. Token com menos de '
                               '24 h não pode ser renovado ainda; vencido ou revogado, só '
                               'gerando outro no painel da Meta.'.format(erro))
        quando = ' Vence em {:%d/%m/%Y}.'.format(expira) if expira else ''
        self.stdout.write(self.style.SUCCESS('Token do Instagram renovado.' + quando))
