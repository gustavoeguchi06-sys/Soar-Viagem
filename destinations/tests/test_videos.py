"""Vídeos enviados pelo painel: galeria da viagem, carrossel, blog e Soar 60+."""
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import Artigo, Categoria, Secao
from soar.videos import validar_video

from ..models import Destino, SlideInicio, VideoDestino, VideoSoar60

PASTA = tempfile.mkdtemp()
# o começo de um MP4 de verdade: a caixa "ftyp"
MP4 = b'\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom' + b'\x00' * 64
GIF = b'GIF89a\x01\x00\x01\x00\x00\x00\x00;'


def _video(nome='passeio.mp4', conteudo=MP4):
    return SimpleUploadedFile(nome, conteudo, content_type='video/mp4')


def _foto():
    return SimpleUploadedFile('capa.gif', GIF, content_type='image/gif')


@override_settings(MEDIA_ROOT=PASTA)
class VideosTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(PASTA, ignore_errors=True)

    def setUp(self):
        self.destino = Destino.objects.create(nome='Bonito', slug='bonito', descricao='Rios.')

    def test_aceita_so_video_de_verdade(self):
        validar_video(_video())
        validar_video(_video('passeio.webm', b'\x1a\x45\xdf\xa3' + b'\x00' * 32))
        with self.assertRaisesMessage(ValidationError, 'MP4 ou WebM'):
            validar_video(_video('passeio.avi'))
        # renomear outro arquivo para .mp4 não engana
        with self.assertRaisesMessage(ValidationError, 'não é um vídeo'):
            validar_video(_video('falso.mp4', b'MZ\x90\x00' + b'\x00' * 32))
        with override_settings(TAMANHO_MAXIMO_VIDEO=10):
            with self.assertRaisesMessage(ValidationError, 'grande demais'):
                validar_video(_video())

    def test_galeria_da_viagem_mostra_o_video(self):
        VideoDestino.objects.create(destino=self.destino, arquivo=_video(), legenda='Flutuação')
        resposta = self.client.get(self.destino.get_absolute_url())
        self.assertContains(resposta, 'class="galeria-videos"')
        self.assertContains(resposta, '<figcaption>Flutuação</figcaption>')
        self.assertContains(resposta, '/media/destinos/videos/')

    def test_carrossel_toca_o_video_com_a_foto_de_capa(self):
        SlideInicio.objects.create(imagem=_foto(), video=_video(), legenda='Rio da Prata')
        resposta = self.client.get('/')
        self.assertContains(resposta, '<video class="in-hero__foto ativo"')
        self.assertContains(resposta, 'poster="/media/inicio/')
        self.assertContains(resposta, 'muted loop playsinline')

    def test_secao_do_blog_mostra_o_video(self):
        categoria = Categoria.objects.create(nome='Guias', slug='guias')
        artigo = Artigo.objects.create(titulo='Guia de Bonito', slug='guia-de-bonito',
                                       categoria=categoria, resumo='Tudo sobre Bonito.',
                                       publicado=True)
        Secao.objects.create(artigo=artigo, titulo='Flutuação', video=_video())
        resposta = self.client.get(artigo.get_absolute_url())
        self.assertContains(resposta, 'class="blog-video"')

    def test_soar_60_mostra_so_os_videos_ativos(self):
        VideoSoar60.objects.create(titulo='Como é a viagem 60+', arquivo=_video())
        VideoSoar60.objects.create(titulo='Rascunho', arquivo=_video(), ativo=False)
        resposta = self.client.get(reverse('destinations:soar_60'))
        self.assertContains(resposta, 'Como é a viagem 60+')
        self.assertNotContains(resposta, 'Rascunho')
        VideoSoar60.objects.all().delete()
        self.assertNotContains(self.client.get(reverse('destinations:soar_60')), 'id="videos"')

    def test_painel_tem_os_campos_de_video(self):
        from contas.dois_fatores import CHAVE_OK
        dono = User.objects.create_superuser('dono', 'd@x.com', 'senha-boa-123')
        self.client.force_login(dono)
        sessao = self.client.session
        sessao[CHAVE_OK] = dono.pk
        sessao.save()
        editar = reverse('admin:destinations_destino_change', args=[self.destino.pk])
        self.assertContains(self.client.get(editar), 'Vídeos da galeria')
        self.assertContains(self.client.get(reverse('admin:destinations_slideinicio_add')),
                            'name="video"')
        self.assertContains(self.client.get(reverse('admin:destinations_videosoar60_add')),
                            'name="arquivo"')
        self.assertContains(self.client.get(reverse('admin:index')), 'Soar 60+')


class LimiteDeEnvioDeVideoTests(TestCase):
    """O teto maior de envio é só da equipe logada, e só no painel."""

    def _postar(self, caminho, tamanho):
        return self.client.post(caminho, data=b'x', content_type='application/octet-stream',
                                CONTENT_LENGTH=str(tamanho))

    @override_settings(TAMANHO_MAXIMO_ENVIO=1000, TAMANHO_MAXIMO_ENVIO_PAINEL=5000)
    def test_so_a_equipe_no_painel_manda_arquivo_grande(self):
        self.assertEqual(self._postar('/painel/', 3000).status_code, 413)
        cliente = User.objects.create_user('cli', 'c@x.com', 'senha-boa-123')
        self.client.force_login(cliente)
        self.assertEqual(self._postar('/painel/', 3000).status_code, 413)

        self.client.force_login(User.objects.create_user('equipe', 'e@x.com', 'senha-boa-123',
                                                         is_staff=True))
        self.assertNotEqual(self._postar('/painel/', 3000).status_code, 413)
        self.assertEqual(self._postar('/painel/', 6000).status_code, 413)
        # fora do painel vale o teto pequeno, mesmo para a equipe
        self.assertEqual(self._postar('/destinos/', 3000).status_code, 413)
