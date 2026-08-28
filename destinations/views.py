from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from reviews.forms import AvaliacaoForm

from .conteudo import montar_viagem
from .models import Destino


def home(request):
    """Página inicial: destinos em destaque e os mais recentes."""
    destaques = Destino.objects.filter(destaque=True)[:3]
    recentes = Destino.objects.order_by('-criado_em')[:6]
    return render(request, 'destinations/home.html', {
        'destaques': destaques,
        'recentes': recentes,
    })


def lista_destinos(request):
    """Lista de todos os destinos, com busca e filtro por continente."""
    destinos = Destino.objects.all()

    busca = request.GET.get('q', '').strip()
    if busca:
        destinos = destinos.filter(
            Q(nome__icontains=busca) | Q(pais__icontains=busca) | Q(descricao__icontains=busca)
        )

    continente = request.GET.get('continente', '')
    if continente:
        destinos = destinos.filter(continente=continente)

    return render(request, 'destinations/lista.html', {
        'destinos': destinos,
        'busca': busca,
        'continente_ativo': continente,
        'continentes': Destino.CONTINENTES,
    })


def detalhe_destino(request, slug):
    """Detalhe do destino: galeria, hospedagens e avaliações (com formulário)."""
    destino = get_object_or_404(
        Destino.objects.prefetch_related('imagens', 'hospedagens', 'avaliacoes'),
        slug=slug,
    )

    if request.method == 'POST':
        form = AvaliacaoForm(request.POST, request.FILES)
        if form.is_valid():
            avaliacao = form.save(commit=False)
            avaliacao.destino = destino
            avaliacao.save()
            messages.success(request, 'Obrigado! Sua avaliação foi publicada.')
            return redirect(destino.get_absolute_url() + '#avaliacoes')
    else:
        form = AvaliacaoForm()

    avaliacoes = list(destino.avaliacoes.all())

    return render(request, 'destinations/detalhe.html', {
        'destino': destino,
        'hospedagens': destino.hospedagens.filter(disponivel=True),
        'avaliacoes': avaliacoes,
        'viagem': montar_viagem(destino, avaliacoes),
        'form': form,
    })
