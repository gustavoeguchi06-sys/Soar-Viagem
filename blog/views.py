"""Páginas públicas do Blog Soar: o índice de artigos e cada artigo."""
import logging

from django import forms
from django.contrib import messages
from django.core import signing
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.utils import timezone

from destinations import instagram
from destinations.models import Destino
from soar.seguranca import LIMITE_NEWSLETTER, ip_do_cliente

from .models import Artigo, Categoria, Inscricao

log = logging.getLogger('soar.seguranca')

# O link de confirmação é o próprio e-mail assinado com a SECRET_KEY: não
# precisa de tabela de tokens e ninguém consegue montar um link para o e-mail
# de outra pessoa.
SAL_NEWSLETTER = 'blog.newsletter.confirmar'
VALIDADE_CONFIRMACAO = 7 * 24 * 3600

POR_PAGINA = 8
TAMANHO_MAXIMO_BUSCA = 80


def _lateral():
    """O que a barra lateral mostra nas duas páginas."""
    no_ar = Artigo.objects.no_ar()
    categorias = Categoria.objects.annotate(total=Count('artigos', filter=Q(
        artigos__publicado=True, artigos__data_publicacao__lte=timezone.localdate()),
    )).order_by('ordem', 'nome')   # consulta com contagem ignora a ordem padrão do modelo
    return {
        'categorias': categorias,
        'total_no_ar': no_ar.count(),
        'mais_lidos': no_ar.order_by('-leituras', '-data_publicacao')[:5],
    }


def _fotos_instagram():
    """A grade "Siga a Soar no Instagram": as últimas do perfil ou, sem elas, fotos das viagens."""
    fotos = instagram.ultimas_fotos()[:6]
    if fotos:
        return fotos
    viagens = Destino.objects.prefetch_related('imagens').order_by('-destaque', 'nome')[:6]
    return [{'foto': v.capa_card, 'link': instagram.PERFIL, 'legenda': ''} for v in viagens]


def indice(request):
    # o tempo de leitura do cartão soma as seções: vêm todas numa consulta só
    artigos = Artigo.objects.no_ar().select_related('categoria').prefetch_related('secoes')

    busca = request.GET.get('q', '').strip()[:TAMANHO_MAXIMO_BUSCA]
    if busca:
        artigos = artigos.filter(Q(titulo__icontains=busca) | Q(resumo__icontains=busca)
                                 | Q(introducao__icontains=busca))

    categoria = None
    slug_categoria = request.GET.get('categoria', '')
    if slug_categoria:
        categoria = Categoria.objects.filter(slug=slug_categoria).first()
        if categoria:
            artigos = artigos.filter(categoria=categoria)

    # O destaque abre a primeira página, grande, só na vitrine sem filtro.
    destaque = None
    numero = request.GET.get('pagina', '1')
    if not busca and not categoria and numero in ('', '1'):
        destaque = artigos.filter(destaque=True).first()
    if destaque:
        artigos = artigos.exclude(pk=destaque.pk)

    pagina = Paginator(artigos, POR_PAGINA).get_page(numero)

    return render(request, 'blog/indice.html', {
        'destaque': destaque,
        'pagina': pagina,
        'busca': busca,
        'categoria_ativa': categoria,
        **_lateral(),
    })


def artigo(request, slug):
    artigo = get_object_or_404(
        Artigo.objects.select_related('categoria')
                      .prefetch_related('secoes', 'atracoes', 'destinos'),
        slug=slug)

    # Rascunho e agendado só o dono vê, para conferir antes de ir ao ar.
    previa = not artigo.no_ar
    if previa and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404('Artigo não encontrado.')

    if not previa and not request.user.is_staff:
        Artigo.objects.filter(pk=artigo.pk).update(leituras=F('leituras') + 1)

    no_ar = Artigo.objects.no_ar()
    # Na ordem da vitrine: "anterior" é o que vem logo depois (mais antigo) e
    # "próximo" o que vem logo antes (mais novo). Mesma data: vale a ordem de cadastro.
    anterior = no_ar.filter(Q(data_publicacao__lt=artigo.data_publicacao)
                            | Q(data_publicacao=artigo.data_publicacao, pk__gt=artigo.pk)
                            ).order_by('-data_publicacao', 'pk').first()
    proximo = no_ar.filter(Q(data_publicacao__gt=artigo.data_publicacao)
                           | Q(data_publicacao=artigo.data_publicacao, pk__lt=artigo.pk)
                           ).order_by('data_publicacao', '-pk').first()

    return render(request, 'blog/artigo.html', {
        'artigo': artigo,
        'secoes': artigo.secoes.all(),
        'atracoes': artigo.atracoes.all(),
        'viagens': list(artigo.destinos.all()),
        'fotos_instagram': _fotos_instagram(),
        'previa': previa,
        'anterior': anterior,
        'proximo': proximo,
        **_lateral(),
    })


class _EmailForm(forms.Form):
    email = forms.EmailField(max_length=254)


@require_POST
def inscrever(request):
    """Recebe o e-mail dos formulários de newsletter do blog.

    A inscrição só vale depois que o dono do e-mail clica no link que chega
    na caixa dele. A tela diz sempre a mesma coisa, esteja o e-mail inscrito
    ou não: senão ela respondia a qualquer um se tal endereço recebe a
    newsletter da Soar. E cada IP (e cada e-mail) tem um limite de pedidos por
    hora, porque cada pedido manda um e-mail.
    """
    voltar = request.POST.get('voltar') or ''
    if not url_has_allowed_host_and_scheme(voltar, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        voltar = ''
    voltar = voltar or '/blog/'

    form = _EmailForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Esse e-mail não parece certo. Confira e tente de novo.')
        return redirect(voltar)

    email = form.cleaned_data['email'].strip().lower()
    if LIMITE_NEWSLETTER.estourou(request, email):
        log.warning('newsletter bloqueada por limite: email=%r ip=%s',
                    email, ip_do_cliente(request))
        messages.error(request, 'Muitos pedidos daqui agora há pouco. Tente de novo mais tarde.')
        return redirect(voltar)
    LIMITE_NEWSLETTER.registrar(request, email)

    inscricao, _ = Inscricao.objects.get_or_create(email=email, defaults={'origem': voltar[:120]})
    if not inscricao.confirmada:
        _enviar_confirmacao_newsletter(request, inscricao)
    messages.success(request, 'Quase lá! Enviamos um link para {}. Clique nele para '
                              'começar a receber as novidades da Soar.'.format(email))
    return redirect(voltar)


def _enviar_confirmacao_newsletter(request, inscricao):
    token = signing.dumps(inscricao.email, salt=SAL_NEWSLETTER)
    link = request.build_absolute_uri(reverse('blog:confirmar', args=[token]))
    corpo = render_to_string('blog/email/newsletter_confirmar.txt', {'link': link})
    send_mail('Confirme sua inscrição | Soar Operadora', corpo, None, [inscricao.email])


def confirmar(request, token):
    """Link do e-mail: liga a inscrição na newsletter."""
    try:
        email = signing.loads(token, salt=SAL_NEWSLETTER, max_age=VALIDADE_CONFIRMACAO)
    except signing.BadSignature:          # inclui SignatureExpired
        messages.error(request, 'Esse link de confirmação é inválido ou expirou. '
                                'Inscreva-se de novo aqui no blog.')
        return redirect('blog:indice')

    inscricao = Inscricao.objects.filter(email=email).first()
    if inscricao is None:
        messages.error(request, 'Essa inscrição não existe mais. Inscreva-se de novo aqui no blog.')
        return redirect('blog:indice')
    if not inscricao.confirmada:
        inscricao.confirmada_em = timezone.now()
        inscricao.save(update_fields=['confirmada_em'])
    messages.success(request, 'Inscrição confirmada! Você vai receber as novidades da Soar.')
    return redirect('blog:indice')
