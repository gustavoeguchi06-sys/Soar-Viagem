# -*- coding: utf-8 -*-
"""Conteúdo editorial da página de viagem.

A página de detalhe (o "front" da expedição) mostra bem mais coisas do que os
campos do model — roteiro, acomodações, FAQ...  Aqui ficam
esses textos: um bloco padrão que serve para qualquer destino e ajustes por
destino (chave = slug), fáceis de editar depois.
"""
from django.templatetags.static import static

# --------------------------------------------------------------------------- #
# Fotos usadas quando o destino ainda não tem imagens cadastradas no admin
# --------------------------------------------------------------------------- #
FOTOS_PADRAO = [
    'img/hero-jalapao.svg',
    'img/cachoeira.svg',
    'img/rio.svg',
    'img/dunas.svg',
    'img/placa.svg',
    'img/palmeiras.svg',
]

FOTOS_HOSPEDAGEM = ['img/pousada.svg', 'img/quarto-1.svg', 'img/quarto-2.svg',
                    'img/quarto-3.svg', 'img/quarto-4.svg']

AVATARES = ['img/avatar-1.svg', 'img/avatar-2.svg', 'img/avatar-3.svg']

SERVICOS = [
    {'icone': 'ic-onibus', 'titulo': 'Transporte', 'sub': 'confortável'},
    {'icone': 'ic-cama', 'titulo': 'Hospedagem', 'sub': 'selecionada'},
    {'icone': 'ic-guia', 'titulo': 'Guias', 'sub': 'especializados'},
    {'icone': 'ic-escudo', 'titulo': 'Seguro', 'sub': 'viagem'},
    {'icone': 'ic-camera', 'titulo': 'Passeios', 'sub': 'inclusos'},
    {'icone': 'ic-coracao', 'titulo': 'Atendimento', 'sub': 'próximo'},
]

COMODIDADES = [
    {'icone': 'ic-ar', 'nome': 'Ar-condicionado'},
    {'icone': 'ic-wifi', 'nome': 'Wi-Fi'},
    {'icone': 'ic-piscina', 'nome': 'Piscina'},
    {'icone': 'ic-cafe', 'nome': 'Café da manhã'},
]

INCLUSO = [
    'Transporte durante toda a viagem',
    'Hospedagem com café da manhã',
    'Guias locais especializados',
    'Passeios e ingressos do roteiro',
    'Seguro viagem',
    'Grupo acompanhado por anfitrião Soar',
]

INFORMACOES = [
    'Leve documento oficial com foto (RG ou CNH) dentro da validade.',
    'Roupas leves, protetor solar, repelente e uma muda de roupa de banho.',
    'Os passeios têm nível leve a moderado: caminhadas curtas em terreno de areia e pedra.',
    'Bagagem recomendada: uma mala média por pessoa e uma mochila de ataque.',
    'O roteiro pode sofrer ajustes por condições climáticas, sempre priorizando a segurança do grupo.',
]

FAQ = [
    {'pergunta': 'Preciso ter experiência para fazer essa viagem?',
     'resposta': 'Não. O roteiro é pensado para todos os níveis, com caminhadas curtas e ritmo tranquilo.'},
    {'pergunta': 'Posso viajar sozinho(a)?',
     'resposta': 'Sim! Boa parte do grupo viaja sozinha. Na acomodação dupla dividimos o quarto com alguém do mesmo gênero.'},
    {'pergunta': 'E se eu precisar cancelar?',
     'resposta': 'Cancelamentos com até 30 dias da saída têm reembolso conforme as condições gerais do contrato.'},
]

# --------------------------------------------------------------------------- #
# Ajustes por destino (chave = slug)
# --------------------------------------------------------------------------- #
POR_DESTINO = {
    'alter-do-chao': {
        'selo': 'Expedição',
        'subtitulo': 'O paraíso amazônico te espera',
        'regiao': 'Norte',
        'estado': 'Pará',
        'periodo': '15 a 18',
        'mes_ano': 'Maio 2027',
        'dias': '4 dias',
        'noites': '3 noites',
        'proxima_saida': '15 a 18 de Maio de 2027',
        'vagas': 14,
        'nota': '4,9',
        'total_avaliacoes': 128,
        'preco_base': 2980,
        'mais_fotos': 28,
        'hospedagem_nome': 'Pousada Vila Amazônia',
        'hospedagem_sub': 'A duas quadras da Ilha do Amor',
        'fotos': ['img/alter-1.svg', 'img/alter-2.svg', 'img/alter-3.svg',
                  'img/alter-4.svg', 'img/alter-5.svg', 'img/alter-por-do-sol.svg'],
        'destaques': [
            'Ilha do Amor', 'Lago Verde', 'Praia de Ponta de Pedras',
            'Floresta Nacional do Tapajós', 'Pôr do sol no Tapajós', 'Vila de Alter do Chão',
        ],
        'roteiro': [
            {'titulo': 'Dia 1: Chegada em Santarém',
             'resumo': 'Recepção no aeroporto e traslado até a vila de Alter do Chão.',
             'detalhe': 'Recepção da equipe Soar no aeroporto de Santarém e traslado de cerca de '
                        '40 minutos até a vila. Check-in, tarde livre e encontro do grupo ao pôr do sol.'},
            {'titulo': 'Dia 2: Ilha do Amor e Lago Verde',
             'resumo': 'Travessia para a Ilha do Amor e volta de barco pelo Lago Verde.',
             'detalhe': 'Manhã na Ilha do Amor, a faixa de areia branca que aparece na seca do Tapajós. '
                        'À tarde, passeio de barco pelo Lago Verde com paradas para banho.'},
            {'titulo': 'Dia 3: Floresta Nacional do Tapajós',
             'resumo': 'Trilha guiada na floresta e visita a uma comunidade ribeirinha.',
             'detalhe': 'Dia inteiro na Flona do Tapajós: trilha interpretativa com guia local, '
                        'a sumaúma gigante e almoço em uma comunidade ribeirinha.'},
            {'titulo': 'Dia 4: Ponta de Pedras e retorno',
             'resumo': 'Última manhã de praia e traslado de volta a Santarém.',
             'detalhe': 'Manhã livre na Praia de Ponta de Pedras, almoço na vila e traslado '
                        'para o aeroporto de Santarém conforme o horário do seu voo.'},
        ],
        'depoimentos': [
            {'nome': 'Mariana S.', 'local': 'São Paulo/SP', 'nota': 5,
             'texto': 'Lugar incrível! A Soar cuidou de tudo nos mínimos detalhes.'},
            {'nome': 'Bruno C.', 'local': 'Alter do Chão/PA', 'nota': 5,
             'texto': 'A Ilha do Amor no fim da tarde é uma das coisas mais bonitas que já vi no Brasil.'},
        ],
    },
    'jalapao': {
        'selo': 'Expedição',
        'subtitulo': 'Uma aventura no coração do Brasil',
        'regiao': 'Norte',
        'estado': 'Tocantins',
        'periodo': '16 a 21',
        'mes_ano': 'Junho 2027',
        'dias': '6 dias',
        'noites': '5 noites',
        'proxima_saida': '16 a 21 de Junho de 2027',
        'vagas': 12,
        'nota': '4,9',
        'total_avaliacoes': 87,
        'preco_base': 3588,
        'mais_fotos': 36,
        'hospedagem_nome': 'Pousada Jalapão',
        'hospedagem_sub': 'Conforto e natureza',
        'destaques': [
            'Fervedouro do Alecrim', 'Dunas do Jalapão', 'Cânion Sussuapara',
            'Cachoeira da Velha', 'Pôr do sol nas Dunas', 'E muito mais',
        ],
        'roteiro': [
            {'titulo': 'Dia 1: São Paulo → Palmas',
             'resumo': 'Embarque nos pontos de encontro e viagem noturna com destino a Palmas.',
             'detalhe': 'Encontro com a equipe Soar nos pontos combinados, embarque e viagem noturna. '
                        'Kit lanche a bordo e paradas programadas para descanso.'},
            {'titulo': 'Dia 2: Palmas → Jalapão',
             'resumo': 'Chegada, café da manhã e início dos passeios.',
             'detalhe': 'Chegada em Palmas, café da manhã e transfer 4x4 para o Jalapão. '
                        'À tarde, primeiro banho de rio e apresentação do grupo ao pôr do sol.'},
            {'titulo': 'Dia 3: Fervedouros e Cachoeiras',
             'resumo': 'Visita ao Fervedouro do Alecrim e Cachoeira da Velha.',
             'detalhe': 'Manhã no Fervedouro do Alecrim, onde a água brota do chão e é impossível afundar. '
                        'À tarde, mirante e banho na Cachoeira da Velha.'},
            {'titulo': 'Dia 4: Dunas e Cânions',
             'resumo': 'Dunas do Jalapão, Cânion Sussuapara e Pôr do sol.',
             'detalhe': 'Travessia até as Dunas, caminhada no Cânion Sussuapara e o famoso pôr do sol '
                        'no alto das dunas alaranjadas, o cartão-postal da viagem.'},
            {'titulo': 'Dia 5: Rio Sono e Cachoeiras',
             'resumo': 'Passeios guiados e tempo livre para relaxar.',
             'detalhe': 'Descida de bote no Rio Sono, parada nas cachoeiras do caminho e tarde livre '
                        'para descansar na pousada ou conhecer o artesanato de capim dourado.'},
            {'titulo': 'Dia 6: Retorno',
             'resumo': 'Café da manhã, saída e previsão de chegada à noite.',
             'detalhe': 'Café da manhã, despedida do grupo e retorno a Palmas para o voo/ônibus de volta. '
                        'Previsão de chegada em São Paulo no fim da noite.'},
        ],
        'depoimentos': [
            {'nome': 'Mariana S.', 'local': 'Serra da Canastra', 'nota': 5,
             'texto': 'Foi sem dúvidas a maior aventura que já fiz. Tudo muito bem organizado e os guias '
                      'são incríveis!'},
            {'nome': 'Ricardo T.', 'local': 'Jalapão/TO', 'nota': 5,
             'texto': 'O Jalapão com a Soar superou minhas expectativas. Cada detalhe feito com muito carinho.'},
            {'nome': 'Ana Paula L.', 'local': 'Alter do Chão/PA', 'nota': 5,
             'texto': 'A energia do grupo e os lugares incríveis tornam a viagem inesquecível. Já quero a próxima!'},
        ],
    },
}


def _moeda(valor):
    """3588 -> '3.588'"""
    return '{:,.0f}'.format(valor).replace(',', '.')


def _estrelas(nota):
    """4.9 (ou '4,9') -> [True, True, True, True, True]"""
    cheias = int(round(float(str(nota).replace(',', '.'))))
    return [i < cheias for i in range(5)]


def _fotos_do_destino(destino, cfg):
    """Fotos cadastradas no admin; completa com os SVGs de exemplo do destino."""
    fotos = [img.imagem.url for img in destino.imagens.all() if img.imagem]
    if destino.imagem_capa:
        fotos.insert(0, destino.imagem_capa.url)
    reserva = cfg.get('fotos') or FOTOS_PADRAO
    if len(fotos) < 6:
        fotos += [static(f) for f in reserva[len(fotos):]]
    return fotos


def _roteiro_generico(destino):
    nome = destino.nome
    modelos = [
        ('Dia 1: Embarque', 'Encontro do grupo e viagem com destino a {}.'.format(nome),
         'Encontro com a equipe Soar nos pontos combinados e embarque.'),
        ('Dia 2: Chegada em {}'.format(nome), 'Chegada, café da manhã e início dos passeios.',
         'Acomodação, café da manhã e primeiro passeio de reconhecimento com o grupo.'),
        ('Dia 3: Passeios guiados', 'Os principais cartões-postais do destino.',
         'Dia inteiro de passeios guiados pelos pontos mais bonitos da região.'),
        ('Dia 4: Natureza e cultura', 'Trilhas, banhos e contato com a cultura local.',
         'Roteiro de natureza pela manhã e imersão na cultura local à tarde.'),
        ('Dia 5: Tempo livre', 'Passeios opcionais e tempo livre para relaxar.',
         'Manhã de passeio e tarde livre para descansar ou explorar por conta própria.'),
        ('Dia 6: Retorno', 'Café da manhã, saída e previsão de chegada à noite.',
         'Café da manhã, despedida do grupo e retorno com previsão de chegada à noite.'),
    ]
    return [{'titulo': t, 'resumo': r, 'detalhe': d} for t, r, d in modelos]


def _roteiro_do_banco(destino, cfg):
    """Roteiro cadastrado no painel; sem isso, o editorial; sem isso, o genérico."""
    dias = list(destino.roteiro.all())
    if dias:
        return [{'titulo': d.titulo, 'resumo': d.resumo, 'detalhe': d.detalhe,
                 'foto_propria': d.imagem.url if d.imagem else ''} for d in dias]
    return [dict(d) for d in (cfg.get('roteiro') or _roteiro_generico(destino))]


def montar_viagem(destino, avaliacoes):
    """Monta o dicionário usado pelo template da página de viagem.

    A ordem de preferência é sempre a mesma: o que o dono cadastrou no painel
    vence; depois vem o conteúdo editorial fixo daqui (`POR_DESTINO`); e por
    último o texto padrão. Assim um destino recém-criado no admin já abre com
    a página inteira montada, e cada campo preenchido vai substituindo o padrão.
    """
    cfg = POR_DESTINO.get(destino.slug, {})
    fotos = _fotos_do_destino(destino, cfg)

    preco_base = destino.preco_base or cfg.get('preco_base')
    if preco_base is None:
        preco_base = int(destino.preco_medio_diaria * 6) if destino.preco_medio_diaria else 3588
    preco_base = int(preco_base)

    # a nota/quantidade da vitrine pode vir do conteúdo editorial (histórico da
    # operadora); sem isso, usa o que está no banco
    nota = cfg.get('nota') or destino.media_avaliacoes or 4.9
    total = cfg.get('total_avaliacoes') or len(avaliacoes) or 87

    roteiro = _roteiro_do_banco(destino, cfg)
    for i, dia in enumerate(roteiro):
        dia['foto'] = dia.get('foto_propria') or fotos[(i + 1) % len(fotos)]

    hospedagem_db = destino.hospedagens.first()
    fotos_hosp = []
    if hospedagem_db:
        if hospedagem_db.imagem:
            fotos_hosp.append(hospedagem_db.imagem.url)
        fotos_hosp += [i.imagem.url for i in hospedagem_db.imagens.all() if i.imagem]
    if len(fotos_hosp) < 5:
        fotos_hosp += [static(f) for f in FOTOS_HOSPEDAGEM[len(fotos_hosp):]]

    depoimentos = []
    for i, av in enumerate(sorted(avaliacoes, key=lambda a: a.criado_em)[:6]):
        depoimentos.append({
            'nome': av.nome_autor,
            'local': destino.nome,
            'estrelas': _estrelas(av.nota),
            'texto': av.comentario,
            'avatar': static(AVATARES[i % len(AVATARES)]),
            'foto': av.foto.url if av.foto else '',
            'data': av.criado_em.strftime('%d/%m/%Y'),
        })
    if not depoimentos:
        for i, d in enumerate(cfg.get('depoimentos', [])):
            depoimentos.append({
                'nome': d['nome'], 'local': d['local'], 'estrelas': _estrelas(d['nota']),
                'texto': d['texto'], 'avatar': static(AVATARES[i % len(AVATARES)]),
                'foto': '', 'data': '',
            })

    destaques = [d.texto for d in destino.destaques_viagem.all()] or cfg.get('destaques') or [
        'Roteiro completo', 'Guias especializados', 'Grupo pequeno',
        'Hospedagem selecionada', 'Passeios inclusos', 'E muito mais',
    ]

    faq = [{'pergunta': p.pergunta, 'resposta': p.resposta} for p in destino.perguntas.all()] or FAQ

    curto = destino.nome.split('/')[0]

    # Todas as saídas que ainda vão acontecer. A primeira com vaga é a que
    # manda no período mostrado na capa; sem nenhuma cadastrada, vale o
    # texto antigo do destino.
    saidas = [{
        'id': s.pk, 'texto': s.texto, 'vagas': s.vagas, 'esgotada': s.esgotada,
        'textos': s.textos,
    } for s in destino.saidas_futuras] if destino.pk else []
    livres = [s for s in saidas if not s['esgotada']]
    if livres:
        livres[0]['padrao'] = True
    primeira = (livres or saidas or [None])[0]
    prox = primeira['textos'] if primeira else {}

    return {
        'selo': destino.selo or cfg.get('selo', 'Expedição'),
        'subtitulo': destino.subtitulo or cfg.get('subtitulo')
                     or 'Uma aventura no coração do Brasil',
        'regiao': destino.regiao or cfg.get('regiao') or '',
        'estado': destino.estado or cfg.get('estado') or destino.pais,
        'curto': curto,
        'periodo': prox.get('periodo') or destino.periodo or cfg.get('periodo', '16 a 21'),
        'mes_ano': prox.get('mes_ano') or destino.mes_ano or cfg.get('mes_ano', 'Junho 2027'),
        'dias': prox.get('dias') or destino.dias or cfg.get('dias', '6 dias'),
        'noites': prox.get('noites') or destino.noites or cfg.get('noites', '5 noites'),
        'nota': str(nota).replace('.', ','),
        'estrelas': _estrelas(nota),
        'total_avaliacoes': total,
        'fotos': fotos,
        'thumbs': fotos[1:5] if len(fotos) > 4 else fotos,
        'galeria': fotos[:4],
        'mais_fotos': cfg.get('mais_fotos', 36),
        'servicos': SERVICOS,
        'destaques': destaques,
        'roteiro': roteiro,
        'incluso': destino.linhas('incluso') or INCLUSO,
        'informacoes': destino.linhas('informacoes') or INFORMACOES,
        'faq': faq,
        'preco': _moeda(preco_base),
        'preco_num': preco_base,
        'proxima_saida': prox.get('proxima_saida') or destino.proxima_saida or cfg.get('proxima_saida',
                                                          '16 a 21 de Junho de 2027'),
        'vagas': (primeira['vagas'] if primeira
                  else destino.vagas if destino.vagas is not None else cfg.get('vagas', 12)),
        'saidas': saidas,
        'tem_vaga': bool(livres) or not saidas,
        'acomodacoes': [
            {'chave': 'single', 'nome': 'Single', 'pessoas': '1 pessoa',
             'preco': 'R$ ' + _moeda(preco_base + 1400), 'valor': preco_base + 1400,
             'padrao': False, 'consulte': False},
            {'chave': 'casal', 'nome': 'Casal', 'pessoas': '2 pessoas (cama de casal)',
             'preco': 'R$ ' + _moeda(preco_base), 'valor': preco_base,
             'padrao': True, 'consulte': False},
            {'chave': 'duplo', 'nome': 'Duplo (Twin)', 'pessoas': '2 pessoas (camas separadas)',
             'preco': 'R$ ' + _moeda(preco_base), 'valor': preco_base,
             'padrao': False, 'consulte': False},
            {'chave': 'triplo', 'nome': 'Triplo', 'pessoas': '3 pessoas',
             'preco': 'R$ ' + _moeda(preco_base - 200), 'valor': preco_base - 200,
             'padrao': False, 'consulte': False},
            {'chave': 'crianca', 'nome': 'Criança (8 anos)', 'pessoas': 'Consulte condições',
             'preco': 'Consulte', 'valor': None, 'padrao': False, 'consulte': True},
        ],
        'hospedagem': {
            'nome': hospedagem_db.nome if hospedagem_db else cfg.get('hospedagem_nome', 'Pousada Soar'),
            'sub': destino.hospedagem_sub or cfg.get('hospedagem_sub', 'Conforto e natureza'),
            'fotos': fotos_hosp,
            'miniaturas': fotos_hosp[1:5],
            'comodidades': COMODIDADES,
        },
        'depoimentos': depoimentos,
    }
