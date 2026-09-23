"""Apaga o que passou do prazo — cumpre o que o aviso de privacidade promete.

O aviso (/privacidade/) diz por quanto tempo cada dado fica. Sem uma rotina que
apague, a promessa é só texto. Este comando faz a limpeza e pode rodar todo dia:
só mexe no que já venceu, então rodar duas vezes seguidas não apaga nada a mais.

    python manage.py expurgar_dados             # apaga
    python manage.py expurgar_dados --simular   # só conta, não apaga nada

O rodar.bat chama este comando toda vez que o servidor sobe. No servidor de
produção, agende uma vez por dia (cron ou Agendador de Tarefas do Windows).

Prazos — os mesmos do aviso de privacidade:

- Reservas: 5 anos após a viagem. A data da viagem é texto livre ("Julho de
  2026"), então a conta parte do pedido, com 1 ano de folga: 6 anos.
- IP das avaliações: 6 meses. A avaliação fica; só o IP some.
- Registro de acessos (logs/seguranca.log.*): 6 meses, o mínimo que o Marco
  Civil da Internet (art. 15) exige guardar — nem mais, nem menos.
- Cadastros nunca confirmados: 30 dias. Conta que nunca foi ativada nem usada
  não tem reserva nem avaliação: é só nome, e-mail e senha de alguém que não
  terminou o cadastro — ou de alguém que usou o e-mail de outra pessoa.
"""
import logging
import time
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from reservas.models import Reserva
from reviews.models import Avaliacao

log = logging.getLogger('soar.seguranca')

PRAZO_RESERVA = timedelta(days=6 * 365)
PRAZO_IP_AVALIACAO = timedelta(days=183)
PRAZO_LOG = timedelta(days=183)
PRAZO_CADASTRO_PENDENTE = timedelta(days=30)


class Command(BaseCommand):
    help = 'Apaga os dados pessoais que passaram do prazo do aviso de privacidade.'

    def add_arguments(self, parser):
        parser.add_argument('--simular', action='store_true',
                            help='Só conta o que seria apagado, sem apagar nada.')

    def handle(self, *args, simular=False, **options):
        agora = timezone.now()

        reservas = Reserva.objects.filter(criado_em__lt=agora - PRAZO_RESERVA)
        ips = Avaliacao.objects.filter(criado_em__lt=agora - PRAZO_IP_AVALIACAO,
                                       ip__isnull=False)
        # last_login vazio = nunca entrou. Sem isso, uma conta que o dono
        # desativou de propósito no painel também seria apagada.
        pendentes = User.objects.filter(
            is_active=False, last_login__isnull=True,
            is_staff=False, is_superuser=False,
            date_joined__lt=agora - PRAZO_CADASTRO_PENDENTE,
        )
        logs = self._logs_vencidos()

        totais = {
            'reservas antigas': reservas.count(),
            'IPs de avaliação': ips.count(),
            'cadastros nunca confirmados': pendentes.count(),
            'arquivos de log': len(logs),
        }

        if not simular:
            with transaction.atomic():
                reservas.delete()
                ips.update(ip=None)
                pendentes.delete()
            for arquivo in logs:
                arquivo.unlink(missing_ok=True)
            if any(totais.values()):
                log.info('expurgo: %s', ', '.join(
                    '{}={}'.format(nome, total) for nome, total in totais.items()))

        self.stdout.write('Seria apagado (simulação):' if simular else 'Expurgo feito:')
        for nome, total in totais.items():
            self.stdout.write('  {:<30} {}'.format(nome, total))

    @staticmethod
    def _logs_vencidos():
        """Arquivos antigos do log de segurança — nunca o que está em uso."""
        limite = time.time() - PRAZO_LOG.total_seconds()
        return [arquivo for arquivo in settings.PASTA_LOGS.glob('seguranca.log.*')
                if arquivo.is_file() and arquivo.stat().st_mtime < limite]
