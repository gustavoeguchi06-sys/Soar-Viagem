"""A foto da avaliação ganha nome sorteado, e só imagem de verdade entra."""
import re

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from reviews.models import Avaliacao, caminho_foto_avaliacao


class FotoDaAvaliacaoTests(TestCase):
    """A avaliação é cadastrada pelo dono no painel; estas regras valem lá."""

    def test_nome_gravado_e_sorteado(self):
        caminho = caminho_foto_avaliacao(None, 'joao-silva-cpf.jpg')
        self.assertRegex(caminho, r'^avaliacoes/[0-9a-f]{32}\.jpg$')
        self.assertNotIn('joao', caminho)
        self.assertNotEqual(caminho, caminho_foto_avaliacao(None, 'joao-silva-cpf.jpg'))

    def test_extensao_perigosa_nunca_e_gravada(self):
        self.assertTrue(re.fullmatch(r'avaliacoes/[0-9a-f]{32}',
                                     caminho_foto_avaliacao(None, 'x.html')))

    def test_arquivo_que_nao_e_imagem_e_recusado(self):
        campo = Avaliacao._meta.get_field('foto')
        falso = SimpleUploadedFile('foto.jpg', b'<script>alert(1)</script>')
        with self.assertRaises(ValidationError):
            campo.formfield().clean(falso)


class AvaliacaoDoVisitanteTests(TestCase):
    """O visitante avalia na página da viagem; só aparece depois que o dono aprova."""

    def setUp(self):
        from django.core.cache import cache
        from django.urls import reverse
        from destinations.models import Destino
        cache.clear()   # o limite de avaliações por hora conta no cache
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')
        self.url = reverse('destinations:avaliar', args=['bonito'])
        self.dados = {'nome_autor': 'Ana S.', 'nota': '5', 'aceite': 'on',
                      'comentario': 'Viagem incrível, guias muito atenciosos!'}

    def test_pagina_tem_o_botao_e_o_formulario(self):
        pagina = self.client.get(self.destino.get_absolute_url())
        self.assertContains(pagina, 'Avaliar esta viagem')
        self.assertContains(pagina, 'name="comentario"')

    def test_avaliacao_entra_na_fila_sem_aparecer(self):
        resposta = self.client.post(self.url, self.dados)
        self.assertRedirects(resposta, self.destino.get_absolute_url() + '?avaliacao=1#avaliacoes',
                             fetch_redirect_response=False)
        avaliacao = Avaliacao.objects.get()
        self.assertFalse(avaliacao.publicada)
        self.assertIsNone(avaliacao.autor)
        self.assertEqual(avaliacao.ip, '127.0.0.1')
        pagina = self.client.get(self.destino.get_absolute_url() + '?avaliacao=1')
        self.assertContains(pagina, 'Obrigado pela avaliação!')
        self.assertNotContains(pagina, 'guias muito atenciosos')

        avaliacao.publicada = True            # o dono aprova no painel
        avaliacao.save()
        self.assertContains(self.client.get(self.destino.get_absolute_url()),
                            'guias muito atenciosos')

    def test_sem_autorizar_nao_envia(self):
        resposta = self.client.post(self.url, {**self.dados, 'aceite': ''})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'É preciso autorizar a publicação')
        self.assertContains(resposta, 'id="avaliarPopup" data-popup open')
        self.assertContains(resposta, 'data-abrir-ja')
        self.assertFalse(Avaliacao.objects.exists())

    def test_robo_de_spam_e_descartado(self):
        self.client.post(self.url, {**self.dados, 'site': 'http://spam.example'})
        self.assertFalse(Avaliacao.objects.exists())

    def test_limite_por_hora(self):
        for _ in range(3):
            self.client.post(self.url, self.dados)
        self.client.post(self.url, self.dados)
        self.assertEqual(Avaliacao.objects.count(), 3)

    def test_so_aceita_envio(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
