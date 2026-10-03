"""A página "Sobre a Soar" e a edição dela no painel."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import DiferencialSobre, NumeroSobre, PaginaSobre


class PaginaSobreTests(TestCase):
    def test_menu_leva_para_a_pagina_com_o_texto_inicial(self):
        inicio = self.client.get('/')
        self.assertContains(inicio, 'href="{}">Sobre a Soar'.format(reverse('destinations:sobre')))
        resposta = self.client.get(reverse('destinations:sobre'))
        self.assertContains(resposta, '<h1>Sobre a Soar</h1>')
        self.assertContains(resposta, 'Quem somos')
        self.assertContains(resposta, 'Roteiros completos')
        # sem números nem fotos cadastrados, esses blocos não aparecem
        self.assertNotContains(resposta, 'class="sobre-numeros"')
        self.assertNotContains(resposta, 'class="sobre-fotos"')

    def test_o_que_o_dono_edita_aparece(self):
        pagina = PaginaSobre.atual()
        pagina.titulo = 'Nossa história'
        pagina.historia = 'Primeiro parágrafo.\n\nSegundo parágrafo.'
        pagina.save()
        NumeroSobre.objects.create(pagina=pagina, valor='+2.000', legenda='viajantes')
        DiferencialSobre.objects.create(pagina=pagina, icone='ic-barco', titulo='Passeio de barco')
        resposta = self.client.get(reverse('destinations:sobre'))
        self.assertContains(resposta, '<h1>Nossa história</h1>')
        self.assertContains(resposta, '<p>Primeiro parágrafo.</p><p>Segundo parágrafo.</p>')
        self.assertContains(resposta, '<strong>+2.000</strong><span>viajantes</span>')
        self.assertContains(resposta, 'href="#ic-barco"')

    def test_aba_do_painel_abre_direto_no_formulario(self):
        from contas.dois_fatores import CHAVE_OK
        dono = User.objects.create_superuser('dono', 'd@x.com', 'senha-boa-123')
        self.client.force_login(dono)
        sessao = self.client.session
        sessao[CHAVE_OK] = dono.pk
        sessao.save()
        self.assertContains(self.client.get(reverse('admin:index')), 'Sobre a Soar')
        lista = reverse('admin:destinations_paginasobre_changelist')
        resposta = self.client.get(lista)
        self.assertRedirects(resposta, reverse('admin:destinations_paginasobre_change',
                                               args=[PaginaSobre.atual().pk]))
        self.assertEqual(PaginaSobre.objects.count(), 1)
        formulario = self.client.get(resposta.url)
        self.assertContains(formulario, 'name="video_capa"')
        self.assertContains(formulario, 'Diferenciais (cartões com ícone)')
