from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from reviews.forms import AvaliacaoForm
from soar.seguranca import LIMITE_AVALIACAO, ip_do_cliente

from .conteudo import montar_viagem
from .models import Destino

# Uma busca útil cabe numa linha. Acima disso é só custo: o filtro varre a
# tabela inteira comparando substring em três colunas.
TAMANHO_MAXIMO_BUSCA = 80
POR_PAGINA = 12


def home(request):
    """Página inicial: destinos em destaque e os mais recentes."""
    destaques = Destino.objects.filter(destaque=True)[:3]
    recentes = Destino.objects.order_by('-criado_em')[:6]
    return render(request, 'destinations/home.html', {
        'destaques': destaques,
        'recentes': recentes,
    })


def lista_destinos(request):
    """Lista de todos os destinos, com busca e filtro por região."""
    destinos = Destino.objects.all()

    busca = request.GET.get('q', '').strip()[:TAMANHO_MAXIMO_BUSCA]
    if busca:
        destinos = destinos.filter(
            Q(nome__icontains=busca) | Q(pais__icontains=busca) | Q(descricao__icontains=busca)
        )

    regiao = request.GET.get('regiao', '')
    # Só região que existe: valor inventado devolve a lista inteira sem
    # filtro nenhum, o que confunde mais do que ajuda.
    if regiao in dict(Destino.REGIOES):
        destinos = destinos.filter(regiao=regiao)
    else:
        regiao = ''

    # Paginação: sem ela, uma busca ampla renderiza o catálogo todo de uma vez.
    pagina = Paginator(destinos, POR_PAGINA).get_page(request.GET.get('pagina'))

    return render(request, 'destinations/lista.html', {
        'destinos': pagina,
        'pagina': pagina,
        'busca': busca,
        'regiao_ativa': regiao,
        'regioes': Destino.REGIOES,
    })


def soar_60(request):
    """A página do programa Soar 60+.

    O botão da home ia direto para o WhatsApp: a pessoa era jogada numa
    conversa sem ter visto viagem nenhuma, e tinha que perguntar o que existe
    para só então decidir. Aqui ela conhece o programa e as viagens primeiro; o
    WhatsApp fica no fim, para quando ela realmente quiser reservar.

    Enquanto nenhuma viagem estiver marcada como 60+ no painel, a página mostra
    o catálogo inteiro — melhor do que uma página vazia, e é verdade: toda
    viagem da Soar pode ser feita no ritmo 60+, é só combinar.
    """
    viagens = Destino.objects.filter(soar_60=True)
    escolhidas = viagens.exists()
    if not escolhidas:
        viagens = Destino.objects.all()

    return render(request, 'destinations/soar_60.html', {
        'viagens': viagens[:POR_PAGINA],
        'escolhidas': escolhidas,
    })


def detalhe_destino(request, slug):
    """Detalhe do destino: galeria, hospedagens e avaliações (com formulário)."""
    destino = get_object_or_404(
        Destino.objects.prefetch_related('imagens', 'hospedagens'),
        slug=slug,
    )

    if request.method == 'POST':
        return _receber_avaliacao(request, destino)

    form = AvaliacaoForm() if request.user.is_authenticated else None

    # Só o que o dono aprovou no painel aparece aqui.
    avaliacoes = list(destino.avaliacoes.publicadas())

    return render(request, 'destinations/detalhe.html', {
        'destino': destino,
        'hospedagens': destino.hospedagens.all(),
        'avaliacoes': avaliacoes,
        'viagem': montar_viagem(destino, avaliacoes),
        'form': form,
        'ja_avaliou': _ja_avaliou(request, destino),
    })


def _ja_avaliou(request, destino):
    if not request.user.is_authenticated:
        return False
    return destino.avaliacoes.filter(autor=request.user).exists()


def _receber_avaliacao(request, destino):
    """Grava a avaliação enviada pelo formulário do destino.

    Exige conta: era aberto a anônimos, com o nome do autor em campo livre, e
    isso permitia assinar como a própria operadora e mexer na nota da vitrine
    sem deixar rastro.
    """
    destino_url = destino.get_absolute_url()

    if not request.user.is_authenticated:
        entrar = '{}?next={}#form-avaliacao'.format(reverse('contas:entrar'), destino_url)
        messages.info(request, 'Entre na sua conta para avaliar este destino.')
        return redirect(entrar)

    if _ja_avaliou(request, destino):
        messages.error(request, 'Você já avaliou este destino. Fale com a Soar para alterar.')
        return redirect(destino_url + '#avaliacoes')

    if LIMITE_AVALIACAO.estourou(request, request.user.pk):
        messages.error(request, 'Você enviou muitas avaliações agora há pouco. '
                                'Tente de novo daqui a pouco.')
        return redirect(destino_url + '#avaliacoes')

    form = AvaliacaoForm(request.POST, request.FILES)
    if not form.is_valid():
        avaliacoes = list(destino.avaliacoes.publicadas())
        return render(request, 'destinations/detalhe.html', {
            'destino': destino,
            'hospedagens': destino.hospedagens.all(),
            'avaliacoes': avaliacoes,
            'viagem': montar_viagem(destino, avaliacoes),
            'form': form,
            'ja_avaliou': False,
        })

    avaliacao = form.save(commit=False)
    avaliacao.destino = destino
    avaliacao.autor = request.user
    avaliacao.nome_autor = request.user.get_full_name() or request.user.username
    avaliacao.ip = ip_do_cliente(request)
    avaliacao.publicada = False          # entra na fila de moderação do painel
    try:
        avaliacao.save()
    except IntegrityError:
        # corrida entre dois envios simultâneos da mesma pessoa
        messages.error(request, 'Você já avaliou este destino.')
        return redirect(destino_url + '#avaliacoes')

    LIMITE_AVALIACAO.registrar(request, request.user.pk)
    messages.success(request, 'Obrigado! Sua avaliação foi enviada e aparece no site '
                              'assim que a Soar revisar.')
    return redirect(destino_url + '#avaliacoes')
