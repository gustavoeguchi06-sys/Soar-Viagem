"""Monta a página inicial.

Tudo o que a página mostra sai do banco: as viagens com a próxima data e as
vagas, os destinos mais bem avaliados, as avaliações publicadas e os artigos
do blog. Nada de número inventado. Onde ainda falta foto de verdade, entram
as fotos e ilustrações de exemplo do próprio site.
"""
from django.db.models import Avg, Count, Prefetch, Q
from django.templatetags.static import static
from django.utils import timezone
from django.utils.text import slugify

from .models import MESES, Destino, ImagemDestino, Saida, SlideInicio

TITULO = 'O Brasil começa onde termina o óbvio.'
SUBTITULO = 'Descubra viagens em grupo para destinos que você nunca vai esquecer.'

# Fotos do carrossel enquanto o dono não cadastra as dele no painel.
SLIDES_PADRAO = [
    ('img/inicio/fervedouro.jpg', 'Fervedouro de água cristalina no Jalapão'),
    ('img/inicio/jalapao-comboio.jpg', 'Comboio de carros na estrada de terra do Jalapão'),
    ('img/inicio/jalapao-estrada.jpg', 'Estrada vermelha cortando o cerrado do Jalapão'),
]

# Onde a página ainda não tem foto de verdade, entram as ilustrações.
ILUSTRACOES = ['img/cachoeira.svg', 'img/rio.svg', 'img/dunas.svg', 'img/palmeiras.svg',
               'img/hero-jalapao.svg', 'img/placa.svg', 'img/alter-por-do-sol.svg']

MOTIVOS = [
    ('ic-onibus', 'Transporte confortável',
     'Veículos fretados e estrutura pensada para viagens em grupo.'),
    ('ic-hotel', 'Hospedagens selecionadas',
     'Hotéis e pousadas escolhidos de acordo com cada experiência.'),
    ('ic-guia', 'Guias especializados', 'Equipe Soar acompanhando o grupo.'),
    ('ic-escudo', 'Seguro viagem', 'Sua segurança é nossa prioridade em cada destino.'),
    ('ic-grupo', 'Experiência em grupo', 'Viajar sozinho não significa viajar sozinho.'),
    ('ic-coracao', 'Atendimento próximo',
     'Antes, durante e depois da viagem, estamos com você.'),
]


UF = {
    'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 'Ceará': 'CE',
    'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA',
    'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG', 'Pará': 'PA',
    'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio de Janeiro': 'RJ',
    'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR',
    'Santa Catarina': 'SC', 'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO',
}


def dias_da_saida(saida):
    return (saida.data_volta - saida.data_ida).days + 1


def _situacao(futuras, proxima):
    if not futuras:
        return 'breve', 'Em breve'
    if proxima is None:
        return 'esgotado', 'Esgotado'
    if proxima.vagas is not None and proxima.vagas <= 5:
        return 'ultimas', 'Últimas vagas'
    return 'disponivel', 'Disponível'


def _viagens(hoje):
    futuras = Prefetch('saidas', queryset=Saida.objects.filter(data_ida__gte=hoje)
                       .order_by('data_ida'), to_attr='futuras')
    destinos = (Destino.objects
                .annotate(n_avaliacoes=Count('avaliacoes', filter=Q(avaliacoes__publicada=True)),
                          nota=Avg('avaliacoes__nota', filter=Q(avaliacoes__publicada=True)))
                .prefetch_related(futuras))
    viagens = []
    for d in destinos:
        proxima = next((s for s in d.futuras if s.vagas != 0), None)
        chave, rotulo = _situacao(d.futuras, proxima)
        estilo = d.selo or 'Expedição'
        viagens.append({
            'destino': d,
            'nome': d.nome,
            'curto': d.nome.split('/')[0],
            # "JALAPÃO/TO": o nome com a sigla do estado, como no cartão
            'rotulo': '{}/{}'.format(d.nome.split('/')[0], UF[d.estado]) if d.estado in UF
                      else d.nome,
            'estado': d.estado or d.pais,
            'foto': d.capa_card,
            'proxima': proxima,
            'dias': dias_da_saida(proxima) if proxima else None,
            'situacao': chave,
            'situacao_rotulo': rotulo,
            'estilo': estilo,
            'estilo_classe': slugify(estilo),
            'preco': d.preco_base,
            'n_avaliacoes': d.n_avaliacoes,
            'nota': d.nota,
            'destaque': d.destaque,
        })
    return viagens


def _fotos_viajantes(slides, viagens, artigos):
    """As fotos do bloco #ViajantesSoar: primeiro as de verdade, depois ilustrações."""
    fotos = []
    for avaliacao_foto in _fotos_de_avaliacoes():
        fotos.append(avaliacao_foto)
    for s in slides:
        fotos.append(s['url'])
    for v in viagens:
        if v['destino'].imagem_capa:
            fotos.append(v['destino'].imagem_capa.url)
    fotos += [i.imagem.url for i in ImagemDestino.objects.exclude(imagem='')[:10]]
    fotos += [a.capa.url for a in artigos if a.capa]
    fotos += [static(f) for f in ILUSTRACOES]
    # a mesma foto pode estar em dois lugares (ex.: capa e galeria): compara
    # pelo nome do arquivo para não repetir na grade
    vistas, unicas = set(), []
    for url in fotos:
        nome = url.rsplit('/', 1)[-1].split('.')[0].lower()
        chave = nome.replace('jalapao-', '').replace('-jalapao', '')
        if chave not in vistas:
            vistas.add(chave)
            unicas.append(url)
    return unicas[:7]


def _fotos_de_avaliacoes():
    from reviews.models import Avaliacao
    return [a.foto.url for a in Avaliacao.objects.publicadas().exclude(foto='')
            .exclude(foto__isnull=True).order_by('-criado_em')[:4]]


def montar_inicio():
    from blog.models import Artigo
    from reviews.models import Avaliacao

    hoje = timezone.localdate()

    slides = [{'url': s.imagem.url, 'legenda': s.legenda}
              for s in SlideInicio.objects.filter(ativo=True).exclude(imagem='')]
    if not slides:
        slides = [{'url': static(f), 'legenda': legenda} for f, legenda in SLIDES_PADRAO]

    viagens = _viagens(hoje)
    experiencias = sorted(viagens, key=lambda v: (
        v['proxima'] is None, v['proxima'].data_ida if v['proxima'] else hoje, v['nome']))
    amados = sorted(viagens, key=lambda v: (-v['n_avaliacoes'], -(v['nota'] or 0),
                                            not v['destaque'], v['nome']))[:6]

    depoimentos = []
    for i, a in enumerate(Avaliacao.objects.publicadas().select_related('destino')
                          .order_by('-criado_em')[:6]):
        depoimentos.append({
            'nome': a.nome_autor,
            'destino': a.destino.nome,
            'url': a.destino.get_absolute_url(),
            'texto': a.comentario,
            'nota': a.nota,
            'avatar': static('img/avatar-{}.svg'.format(i % 3 + 1)),
            'foto': a.foto.url if a.foto else a.destino.capa_card,
        })

    artigos = list(Artigo.objects.no_ar().select_related('categoria')[:5])

    estilos = sorted({v['estilo'] for v in viagens})

    return {
        'titulo': TITULO,
        'subtitulo': SUBTITULO,
        'slides': slides,
        'nomes': [v['curto'] for v in sorted(viagens, key=lambda v: (not v['destaque'], v['nome']))][:6],
        'meses': [(n, MESES[n]) for n in range(1, 13)],
        'estilos': estilos,
        # "Para onde?": todos os destinos do site, em ordem alfabética
        'destinos': sorted(v['nome'] for v in viagens),
        'experiencias': experiencias,
        'amados': amados,
        'motivos': MOTIVOS,
        'depoimentos': depoimentos,
        'viajantes': _fotos_viajantes(slides, viagens, artigos),
        'artigos': artigos,
        'fundo_cta': slides[-1]['url'],
    }
