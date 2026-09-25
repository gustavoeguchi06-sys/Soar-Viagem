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


class ServiceWorkerTests(TestCase):
    def test_sw_js_desinstala_o_worker_antigo(self):
        resposta = self.client.get('/sw.js')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('javascript', resposta['Content-Type'])
        self.assertIn('unregister', resposta.content.decode())
        self.assertEqual(resposta['Cache-Control'], 'no-store')


class PaginasDeErroTests(TestCase):
    def test_404_tem_a_cara_do_site(self):
        resposta = self.client.get('/pagina-que-nao-existe/')
        self.assertEqual(resposta.status_code, 404)
        self.assertContains(resposta, 'Essa página não existe', status_code=404)

    def test_500_renderiza_sem_request(self):
        from django.template.loader import render_to_string
        self.assertIn('Algo deu errado aqui', render_to_string('500.html'))


class CartaoDestinoTests(TestCase):
    def test_destino_sem_foto_usa_ilustracao(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.assertTrue(destino.capa_card.endswith('.svg'))
        resposta = self.client.get('/destinos/')
        self.assertNotContains(resposta, '🏝')


class CriancaNaoPagaTests(TestCase):
    def test_crianca_gratis_e_sem_botao_de_agente(self):
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                         preco_base=3000)
        resposta = self.client.get(destino.get_absolute_url())
        self.assertContains(resposta, 'Criança até 8 anos')
        self.assertContains(resposta, 'Grátis')
        self.assertNotContains(resposta, 'Falar com o agente')

    def test_reserva_de_crianca_sai_gratis(self):
        from django.contrib.auth.models import User
        from reservas.models import Reserva
        destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                         preco_base=3000)
        cliente = User.objects.create_user('cli', 'cli@exemplo.com', 'senha-boa-123')
        self.client.force_login(cliente)
        self.client.post('/reservar/bonito/', {'acomodacao': 'crianca', 'pessoas': 1})
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.preco_estimado, 0)
        self.assertContains(self.client.get('/minha-conta/'), 'Grátis')


class FuncionalidadesTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.',
                                              preco_base=3000)
        hoje = timezone.localdate()
        self.saida = Saida.objects.create(destino=self.destino, vagas=5,
                                          data_ida=hoje + timedelta(days=30),
                                          data_volta=hoje + timedelta(days=34))

    def test_sem_avaliacoes_nao_inventa_nota(self):
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'Ainda sem avaliações')
        self.assertNotContains(resposta, '87 avaliações')

    def test_calendario_lista_as_saidas(self):
        resposta = self.client.get('/calendario/')
        self.assertContains(resposta, 'Bonito')
        self.assertContains(resposta, self.saida.texto)
        self.assertContains(resposta, f'/reservar/bonito/?saida={self.saida.pk}')

    def test_newsletter_grava_o_email(self):
        from blog.models import Inscricao
        resposta = self.client.post('/blog/novidades/', {'email': 'Ana@Exemplo.com',
                                                         'voltar': '/blog/'})
        self.assertRedirects(resposta, '/blog/', fetch_redirect_response=False)
        self.assertTrue(Inscricao.objects.filter(email='ana@exemplo.com').exists())
        self.client.post('/blog/novidades/', {'email': 'ana@exemplo.com'})
        self.assertEqual(Inscricao.objects.count(), 1)
        resposta = self.client.post('/blog/novidades/', {'email': 'x',
                                                         'voltar': 'https://golpe.com/'})
        self.assertRedirects(resposta, '/blog/', fetch_redirect_response=False)


class ExemplosPorRegiaoTests(TestCase):
    def test_um_exemplo_por_regiao_sem_duplicar(self):
        from django.core.management import call_command
        from io import StringIO
        call_command('criar_exemplos_regioes', stdout=StringIO())
        call_command('criar_exemplos_regioes', stdout=StringIO())
        regioes = set(Destino.objects.values_list('regiao', flat=True))
        self.assertEqual(regioes, {'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'})
        self.assertEqual(Destino.objects.count(), 4)
        resposta = self.client.get('/destinos/?regiao=Sul')
        self.assertContains(resposta, 'Cânions do Sul')
        pagina = self.client.get('/destinos/lencois-maranhenses/')
        self.assertContains(pagina, 'Lagoa Bonita')
        self.assertContains(pagina, 'Maranhão')
