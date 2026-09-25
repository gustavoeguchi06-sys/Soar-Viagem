"""O painel do dono.

É o admin do Django, mas com a cara do site e com uma tela inicial que responde
à pergunta que o dono faz ao abrir o painel: *o que precisa de mim agora?*

O admin padrão abre numa lista de tabelas ("Destinos", "Hospedagens",
"Reservas"...) — correta e inútil como primeira tela, porque não diz se há
reserva esperando resposta nem se um destino foi ao ar sem preço. Aqui a
primeira coisa é a fila de trabalho; a lista de tabelas continua embaixo.

Trocar o admin inteiro por este é feito pelo `SoarAdminConfig` lá no fim do
arquivo, que entra no INSTALLED_APPS no lugar de `django.contrib.admin`.
"""
from urllib.parse import urlencode

from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse

# As abas da faixa do topo: (nome, rota, permissão para ver, contador).
# Elas fazem o papel do menu lateral do admin, que fica desligado: o dono
# chega em qualquer parte com um clique, do mesmo jeito que no painel da
# agência. O que não está aqui continua em "Todos os cadastros", na tela
# inicial.
ABAS = [
    ('Visão geral', 'admin:index', None, None),
    ('Reservas', 'admin:reservas_reserva_changelist', 'reservas.view_reserva', 'reservas'),
    ('Orçamentos', 'admin:agencia_orcamento_changelist', 'agencia.view_orcamento', None),
    ('Destinos', 'admin:destinations_destino_changelist', 'destinations.view_destino', None),
    ('Hospedagens', 'admin:destinations_hospedagem_changelist',
     'destinations.view_hospedagem', None),
    ('Blog Soar', 'admin:blog_artigo_changelist', 'blog.view_artigo', None),
    ('Avaliações', 'admin:reviews_avaliacao_changelist', 'reviews.view_avaliacao', 'avaliacoes'),
    ('Agências', 'admin:contas_perfilagente_changelist', 'contas.view_perfilagente', None),
    ('Usuários', 'admin:auth_user_changelist', 'auth.view_user', None),
]


class PainelSoar(AdminSite):
    site_header = 'Soar | Painel do dono'
    site_title = 'Soar | Painel'
    index_title = 'Gerenciar o site de viagem'
    # O menu lateral dá lugar às abas da faixa verde (ver ABAS).
    enable_nav_sidebar = False

    def each_context(self, request):
        contexto = super().each_context(request)
        if request.user.is_active and request.user.is_staff:
            contexto['abas_painel'] = self._abas(request)
        return contexto

    def _abas(self, request):
        from reservas.models import Reserva
        from reviews.models import Avaliacao

        contadores = {
            'reservas': lambda: Reserva.objects.filter(status='pendente').count(),
            'avaliacoes': lambda: Avaliacao.objects.filter(publicada=False).count(),
        }
        inicio = reverse('admin:index', current_app=self.name)
        abas = []
        for nome, rota, permissao, contador in ABAS:
            if permissao and not request.user.has_perm(permissao):
                continue
            try:
                url = reverse(rota, current_app=self.name)
            except NoReverseMatch:
                continue
            # O blog tem artigos e categorias: a aba acende nos dois.
            prefixo = url.rsplit('/', 2)[0] + '/' if rota.startswith('admin:blog_') else url
            ativa = (request.path == inicio) if url == inicio else request.path.startswith(prefixo)
            abas.append({
                'nome': nome,
                'url': url,
                'ativa': ativa,
                'contador': contadores[contador]() if contador else 0,
            })
        return abas

    def login(self, request, extra_context=None):
        """O painel não tem tela de login própria.

        O admin do Django traz a dele, e ter duas telas de entrada no mesmo site
        é uma a mais para lembrar da senha, uma a mais para manter e uma a mais
        para um golpe copiar. Quem cai aqui é mandado para o *Entrar* do site,
        levando junto para onde queria ir — o `entrar` devolve a pessoa ao
        painel assim que ela entra, se for da equipe.
        """
        destino = reverse('admin:index', current_app=self.name)

        if self.has_permission(request):          # já é da equipe e já entrou
            return HttpResponseRedirect(request.GET.get(REDIRECT_FIELD_NAME) or destino)

        pedido = request.GET.get(REDIRECT_FIELD_NAME) or destino
        return HttpResponseRedirect('{}?{}'.format(
            reverse('contas:entrar'), urlencode({REDIRECT_FIELD_NAME: pedido})))

    def index(self, request, extra_context=None):
        """A tela inicial: fila de trabalho, atalhos e o que está sem preço."""
        # Importados aqui, e não no topo, porque este módulo é carregado quando
        # o app de admin sobe — antes dos models estarem prontos.
        from blog.models import Artigo
        from destinations.models import Destino, Hospedagem
        from reservas.models import Reserva
        from reviews.models import Avaliacao

        reservas = Reserva.objects.select_related('destino', 'usuario')
        pendentes = reservas.filter(status='pendente')

        # Um destino no ar sem preço nenhum mostra "sob consulta" no card de
        # reserva. Vale avisar antes de o cliente descobrir.
        sem_preco = Destino.objects.filter(preco_base__isnull=True,
                                           preco_medio_diaria__isnull=True)

        fila_avaliacoes = Avaliacao.objects.filter(publicada=False).select_related('destino')

        contexto = {
            **self.each_context(request),
            'title': self.index_title,
            'app_list': self.get_app_list(request),
            'painel': {
                'reservas_pendentes': pendentes.count(),
                'reservas_total': reservas.count(),
                'avaliacoes_na_fila': fila_avaliacoes.count(),
                'destinos_total': Destino.objects.count(),
                'destinos_sem_preco': sem_preco.count(),
                'hospedagens_total': Hospedagem.objects.count(),
                'artigos_no_ar': Artigo.objects.no_ar().count(),
                'artigos_total': Artigo.objects.count(),

                'ultimas_reservas': list(reservas[:8]),
                'lista_sem_preco': list(sem_preco[:6]),
                'lista_avaliacoes': list(fila_avaliacoes[:5]),

                'url_reservas': reverse('admin:reservas_reserva_changelist'),
                'url_reservas_pendentes':
                    reverse('admin:reservas_reserva_changelist') + '?status__exact=pendente',
                'url_destinos': reverse('admin:destinations_destino_changelist'),
                'url_destino_novo': reverse('admin:destinations_destino_add'),
                'url_hospedagens': reverse('admin:destinations_hospedagem_changelist'),
                'url_hospedagem_nova': reverse('admin:destinations_hospedagem_add'),
                'url_avaliacoes': reverse('admin:reviews_avaliacao_changelist'),
                'url_artigos': reverse('admin:blog_artigo_changelist'),
                'url_artigo_novo': reverse('admin:blog_artigo_add'),
                'url_avaliacoes_fila':
                    reverse('admin:reviews_avaliacao_changelist') + '?publicada__exact=0',
            },
            **(extra_context or {}),
        }
        request.current_app = self.name
        return render(request, self.index_template or 'admin/index.html', contexto)


class SoarAdminConfig(AdminConfig):
    """Faz o `admin.site` do projeto inteiro ser o `PainelSoar`.

    Entra no INSTALLED_APPS no lugar de `django.contrib.admin` — assim cada
    `@admin.register(...)` espalhado pelos apps continua funcionando igual,
    sem precisar apontar para um site diferente.
    """

    default_site = 'soar.painel.PainelSoar'
