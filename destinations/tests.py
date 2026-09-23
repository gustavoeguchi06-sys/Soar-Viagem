"""Várias datas de saída por destino."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from reservas.models import Reserva

from .models import Destino, Saida


class SaidasTests(TestCase):
    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                              preco_base=3000)
        hoje = timezone.localdate()
        self.passada = Saida.objects.create(destino=self.destino, vagas=5,
                                            data_ida=hoje - timedelta(days=30),
                                            data_volta=hoje - timedelta(days=25))
        self.lotada = Saida.objects.create(destino=self.destino, vagas=0,
                                           data_ida=hoje + timedelta(days=20),
                                           data_volta=hoje + timedelta(days=24))
        self.livre = Saida.objects.create(destino=self.destino, vagas=8,
                                          data_ida=hoje + timedelta(days=60),
                                          data_volta=hoje + timedelta(days=65))
        self.outra = Saida.objects.create(destino=self.destino, vagas=None,
                                          data_ida=hoje + timedelta(days=120),
                                          data_volta=hoje + timedelta(days=125))

    def test_pagina_lista_todas_as_saidas_futuras(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        html = resposta.content.decode()
        self.assertContains(resposta, 'Próximas saídas')
        for saida in (self.lotada, self.livre, self.outra):
            self.assertIn(saida.texto, html)
        self.assertNotIn(self.passada.texto, html)
        self.assertContains(resposta, 'Esgotada')
        self.assertContains(resposta, '8 vagas')
        self.assertContains(resposta, 'Consulte')

    def test_capa_mostra_a_primeira_saida_com_vaga(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertEqual(resposta.context['viagem']['periodo'], self.livre.textos['periodo'])

    def test_reserva_grava_a_saida_escolhida(self):
        cliente = User.objects.create_user('cli', 'cli@exemplo.com', 'senha-boa-123')
        self.client.force_login(cliente)
        url = reverse('reservas:nova', args=[self.destino.slug])
        resposta = self.client.get(url + f'?saida={self.outra.pk}')
        self.assertEqual(resposta.context['form']['saida_escolhida'].value(), str(self.outra.pk))
        self.client.post(url, {'saida_escolhida': self.outra.pk, 'acomodacao': 'casal',
                               'pessoas': 2})
        self.assertEqual(Reserva.objects.get().saida, self.outra.texto)

    def test_saida_esgotada_nao_pode_ser_escolhida(self):
        cliente = User.objects.create_user('cli', 'cli@exemplo.com', 'senha-boa-123')
        self.client.force_login(cliente)
        url = reverse('reservas:nova', args=[self.destino.slug])
        resposta = self.client.post(url, {'saida_escolhida': self.lotada.pk,
                                          'acomodacao': 'casal', 'pessoas': 2})
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Reserva.objects.exists())

    def test_tudo_esgotado_volta_para_a_pagina(self):
        Saida.objects.filter(pk__in=[self.livre.pk, self.outra.pk]).update(vagas=0)
        cliente = User.objects.create_user('cli', 'cli@exemplo.com', 'senha-boa-123')
        self.client.force_login(cliente)
        resposta = self.client.get(reverse('reservas:nova', args=[self.destino.slug]))
        self.assertRedirects(resposta, self.destino.get_absolute_url(),
                             fetch_redirect_response=False)

    def test_sem_saidas_cadastradas_mantem_o_texto_antigo(self):
        Saida.objects.all().delete()
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'Próxima saída')
        self.assertContains(resposta, 'Vagas disponíveis')
