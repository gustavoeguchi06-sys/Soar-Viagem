"""Aviso por e-mail para a agência quando a Soar indica um cliente para ela.

Quem pede "Saiba mais" no site cai na lista de Interessados do dono. Quando o
dono marca uma ou mais agências nesse pedido (destinations/admin.py), cada
agência marcada agora recebe um e-mail avisando que tem cliente novo no painel.

O e-mail não leva o contato do cliente (e-mail, WhatsApp): leva o nome, a
viagem e o link do painel. Quem quiser os dados entra com login. Assim um
e-mail encaminhado por engano não espalha o contato de ninguém.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

log = logging.getLogger('soar.seguranca')


def avisar_agencias(interessado, agencias, request):
    """Manda o aviso para cada agência. Devolve (avisadas, sem_email, com_erro)."""
    link = request.build_absolute_uri(reverse('agencia:painel'))
    avisadas, sem_email, com_erro = [], [], []
    for agencia in agencias:
        email = agencia.usuario.email
        if not email:
            sem_email.append(agencia)
            continue
        corpo = render_to_string('agencia/email/interessado.txt', {
            'agencia': agencia, 'interessado': interessado, 'link': link,
        })
        assunto = 'Novo cliente indicado pela Soar: {}'.format(
            interessado.destino.nome if interessado.destino else interessado.nome)
        try:
            send_mail(assunto, corpo, settings.DEFAULT_FROM_EMAIL, [email])
        except Exception:
            log.exception('aviso de interessado nao enviado: interessado=%s agencia=%s',
                          interessado.pk, agencia.pk)
            com_erro.append(agencia)
        else:
            log.info('aviso de interessado enviado: interessado=%s agencia=%s',
                     interessado.pk, agencia.pk)
            avisadas.append(agencia)
    return avisadas, sem_email, com_erro
