"""Testes do Blog Soar gerenciado pelo painel.

    python manage.py test blog
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .admin import SecaoForm
from .models import Artigo, Categoria, Secao

HOJE = timezone.localdate


class BlogBase(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nome='Testes', slug='testes')

    def artigo(self, slug, publicado=True, dias=0, **extra):
        return Artigo.objects.create(
            titulo=extra.pop('titulo', 'Artigo ' + slug), slug=slug, categoria=self.cat,
            resumo='Resumo de ' + slug, publicado=publicado,
            data_publicacao=HOJE() + timedelta(days=dias), **extra)

    def dono(self):
        return User.objects.create_superuser('dono_teste', 'dono@example.com', 'Senha-longa-123')


class ConteudoMigradoTests(TestCase):
    """O artigo que o blog mostrava como página fixa continua no mesmo endereço."""

    def test_jalapao_no_ar_com_secoes_e_atracoes(self):
        jalapao = Artigo.objects.get(slug='jalapao')
        self.assertEqual(jalapao.situacao, 'no_ar')
        self.assertEqual(jalapao.secoes.count(), 5)
        self.assertEqual(jalapao.atracoes.count(), 4)
        resposta = self.client.get('/blog/jalapao/')
        self.assertContains(resposta, 'Fervedouro do Alecrim')
        self.assertContains(resposta, 'class="otima">MAI')

    def test_vitrine_continua_com_os_oito_cartoes(self):
        self.assertEqual(Artigo.objects.no_ar().count(), 8)
        indice = self.client.get('/blog/').content.decode()
        self.assertEqual(indice.count('<a class="blog-post'), 8)
        for aba in ('Destinos', 'Dicas de Viagem', 'Natureza', 'Roteiros', 'Experiências', 'Soar 60+'):
            self.assertIn(aba, indice)


class SituacaoTests(BlogBase):
    """Rascunho e agendado não aparecem para o público; o dono vê a prévia."""

    def test_rascunho_e_agendado_escondidos_do_publico(self):
        self.artigo('rascunho', publicado=False)
        self.artigo('agendado', dias=3)
        self.artigo('no-ar')
        self.assertEqual(self.client.get('/blog/rascunho/').status_code, 404)
        self.assertEqual(self.client.get('/blog/agendado/').status_code, 404)
        self.assertEqual(self.client.get('/blog/no-ar/').status_code, 200)
        indice = self.client.get('/blog/').content.decode()
        self.assertIn('Artigo no-ar', indice)
        self.assertNotIn('Artigo rascunho', indice)
        self.assertNotIn('Artigo agendado', indice)

    def test_dono_ve_previa_do_rascunho(self):
        self.artigo('rascunho', publicado=False)
        self.client.force_login(self.dono())
        resposta = self.client.get('/blog/rascunho/')
        self.assertContains(resposta, 'Pré-visualização')

    def test_agendado_entra_no_ar_sozinho_no_dia(self):
        a = self.artigo('amanha', dias=1)
        self.assertEqual(a.situacao, 'agendado')
        Artigo.objects.filter(pk=a.pk).update(data_publicacao=HOJE())   # o dia chegou
        a.refresh_from_db()
        self.assertEqual(a.situacao, 'no_ar')
        self.assertEqual(self.client.get('/blog/amanha/').status_code, 200)

    def test_leitura_conta_para_visitante_e_nao_para_o_dono(self):
        a = self.artigo('lido')
        self.client.get('/blog/lido/')
        self.client.get('/blog/lido/')
        self.client.force_login(self.dono())
        self.client.get('/blog/lido/')
        a.refresh_from_db()
        self.assertEqual(a.leituras, 2)


class IndiceTests(BlogBase):
    @staticmethod
    def _resultados(resposta):
        """Só a grade de artigos, sem a lateral (que lista os mais lidos)."""
        html = resposta.content.decode()
        return html.split('class="blog-corpo"')[1].split('class="blog-lado"')[0]

    def test_busca_e_categoria(self):
        self.artigo('quokka', titulo='Quokkas da ilha')
        outra = Categoria.objects.create(nome='Outra', slug='outra')
        Artigo.objects.create(titulo='Rio azul', slug='rio', categoria=outra, resumo='x',
                              publicado=True, data_publicacao=HOJE())
        busca = self._resultados(self.client.get('/blog/?q=quokka'))
        self.assertIn('Quokkas da ilha', busca)
        self.assertNotIn('Rio azul', busca)
        cat = self._resultados(self.client.get('/blog/?categoria=outra'))
        self.assertIn('Rio azul', cat)
        self.assertNotIn('Quokkas da ilha', cat)

    def test_paginacao(self):
        for n in range(12):
            self.artigo('p{}'.format(n), dias=-n)
        pagina2 = self.client.get('/blog/?pagina=2')
        self.assertEqual(pagina2.status_code, 200)
        self.assertContains(pagina2, 'aria-current="page"')


class SegurancaDoTextoTests(BlogBase):
    def test_texto_do_painel_nao_vira_html(self):
        a = self.artigo('xss', introducao='<script>alert(1)</script>')
        Secao.objects.create(artigo=a, titulo='<img src=x onerror=alert(1)>',
                             dicas='<b>negrito</b>')
        html = self.client.get('/blog/xss/').content.decode()
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn('<img src=x onerror', html)
        self.assertIn('&lt;script&gt;', html)


class PainelTests(BlogBase):
    def test_meses_viram_caixinhas_e_voltam(self):
        a = self.artigo('meses')
        form = SecaoForm(data={'artigo': a.pk, 'titulo': 'Quando ir', 'icone': 'calendario', 'ordem': 1,
                               'melhores_meses': ['9', '5', '6'], 'meses_bons': []})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['melhores_meses'], '5,6,9')
        self.assertEqual(form.cleaned_data['meses_bons'], '')

    def test_criar_artigo_pelo_painel_com_data_do_calendario(self):
        self.client.force_login(self.dono())
        dados = {
            'titulo': 'Chapada dos Veadeiros', 'slug': 'chapada', 'categoria': self.cat.pk,
            'resumo': 'Cachoeiras e cânions.', 'autor': 'Equipe Soar', 'publicado': 'on',
            'data_publicacao': '2030-01-20', 'cor_etiqueta': 'verde', 'introducao': 'Oi.',
            'secoes-TOTAL_FORMS': '1', 'secoes-INITIAL_FORMS': '0',
            'secoes-0-ordem': '1', 'secoes-0-titulo': 'Quando ir', 'secoes-0-icone': 'calendario',
            'secoes-0-melhores_meses': ['5', '6'],
            'atracoes-TOTAL_FORMS': '0', 'atracoes-INITIAL_FORMS': '0',
        }
        resposta = self.client.post(reverse('admin:blog_artigo_add'), dados)
        self.assertEqual(resposta.status_code, 302, resposta.content.decode()[:2000])
        a = Artigo.objects.get(slug='chapada')
        self.assertEqual(str(a.data_publicacao), '2030-01-20')
        self.assertEqual(a.situacao, 'agendado')
        self.assertEqual(a.secoes.get().melhores_meses, '5,6')

        edicao = self.client.get(reverse('admin:blog_artigo_change', args=[a.pk])).content.decode()
        self.assertIn('type="date"', edicao)
        self.assertIn('value="2030-01-20"', edicao)

    def test_tela_inicial_do_painel_mostra_o_blog(self):
        self.artigo('um')
        self.client.force_login(self.dono())
        html = self.client.get('/painel/').content.decode()
        self.assertIn('Blog Soar', html)
        self.assertIn('Novo artigo no blog', html)
