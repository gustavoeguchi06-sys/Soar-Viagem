# -*- coding: utf-8 -*-
"""Conteúdo editorial da página de viagem.

A página de detalhe (o "front" da expedição) mostra bem mais coisas do que os
campos do model — calendário de embarque, pacotes de acomodação, itens
opcionais, roteiro, FAQ...  Aqui ficam esses textos: um bloco padrão que serve
para qualquer destino e ajustes por destino (chave = slug), fáceis de editar
depois.

A aba "Escolha sua viagem" é interativa: o dicionário `dados` devolvido no fim
vai para o JavaScript (via `json_script`) e alimenta o calendário, a troca de
pacote e o cálculo do total.
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

# --------------------------------------------------------------------------- #
# Abas do miolo da página (a barra logo abaixo do hero)
# --------------------------------------------------------------------------- #
ABAS = [
    {'chave': 'viagem', 'icone': 'ic-mala', 'rotulo': 'Escolha sua viagem'},
    {'chave': 'destino', 'icone': 'ic-mapa', 'rotulo': 'Sobre o destino'},
    {'chave': 'incluso', 'icone': 'ic-mochila', 'rotulo': 'O que está incluso'},
    {'chave': 'roteiro', 'icone': 'ic-doc', 'rotulo': 'Roteiro'},
    {'chave': 'hospedagens', 'icone': 'ic-cama', 'rotulo': 'Hospedagens'},
    {'chave': 'informacoes', 'icone': 'ic-info', 'rotulo': 'Informações'},
    {'chave': 'avaliacoes', 'icone': 'ic-estrela-c', 'rotulo': 'Avaliações'},
]

# --------------------------------------------------------------------------- #
# Blocos padrão (valem para qualquer destino)
# --------------------------------------------------------------------------- #
DURACOES = [
    {'chave': '4d', 'rotulo': '4 dias / 3 noites', 'padrao': True},
    {'chave': '5d', 'rotulo': '5 dias / 4 noites', 'padrao': False},
    {'chave': '6d', 'rotulo': '6 dias / 5 noites', 'padrao': False},
]

INCLUSO_ITENS = [
    {'icone': 'ic-onibus', 'nome': 'Transporte executivo'},
    {'icone': 'ic-hotel', 'nome': 'Hospedagem selecionada'},
    {'icone': 'ic-cafe', 'nome': 'Café da manhã'},
    {'icone': 'ic-ticket', 'nome': 'Passeios e entradas'},
    {'icone': 'ic-guia', 'nome': 'Guia local'},
    {'icone': 'ic-escudo', 'nome': 'Seguro viagem'},
]

PAGAMENTOS = [
    {'icone': 'ic-cartao', 'preenchido': False, 'nome': '10x sem juros no cartão'},
    {'icone': 'ic-boleto', 'preenchido': False, 'nome': 'Boleto bancário'},
    {'icone': 'ic-pix', 'preenchido': True, 'nome': 'PIX com desconto'},
]

CONFIANCA = [
    {'icone': 'ic-whats', 'preenchido': True, 'titulo': 'Dúvidas?',
     'sub': 'Fale com nosso time no WhatsApp'},
    {'icone': 'ic-relogio', 'preenchido': False, 'titulo': 'Atendimento',
     'sub': 'Segunda a sexta, das 9h às 18h'},
    {'icone': 'ic-mala', 'preenchido': False, 'titulo': 'Embarque',
     'sub': 'Diversos pontos em São Paulo'},
    {'icone': 'ic-cadeado', 'preenchido': False, 'titulo': 'Reserva segura',
     'sub': 'Ambiente 100% protegido'},
]

COMODIDADES = [
    {'icone': 'ic-ar', 'nome': 'Ar-condicionado'},
    {'icone': 'ic-wifi', 'nome': 'Wi-Fi'},
    {'icone': 'ic-piscina', 'nome': 'Piscina'},
    {'icone': 'ic-cafe', 'nome': 'Café da manhã'},
]

INCLUSO = [
    'Transporte executivo durante toda a viagem',
    'Hospedagem selecionada com café da manhã',
    'Guias locais especializados',
    'Passeios e ingressos do roteiro',
    'Seguro viagem',
    'Grupo acompanhado por anfitrião Soar',
]

NAO_INCLUSO = [
    'Passagem aérea até o destino',
    'Almoços, jantares e bebidas',
    'Passeios marcados como opcionais',
    'Gastos pessoais e gorjetas',
]

OPCIONAIS = [
    {'chave': 'traslado', 'nome': 'Traslado particular (Aeroporto / Hotel)',
     'unidade': 'Por trecho', 'preco': 120,
     'info': 'Carro exclusivo para você, com motorista aguardando no desembarque.'},
    {'chave': 'passeio', 'nome': 'Passeio de barco ao pôr do sol',
     'unidade': 'Por pessoa', 'preco': 120,
     'info': 'Saída no fim da tarde, com bebida a bordo e retorno após o pôr do sol.'},
    {'chave': 'jantar', 'nome': 'Jantar especial com culinária regional',
     'unidade': 'Por pessoa', 'preco': 150,
     'info': 'Menu de três tempos preparado com ingredientes da região.'},
    {'chave': 'seguro', 'nome': 'Seguro viagem premium (cobertura ampliada)',
     'unidade': 'Por pessoa', 'preco': 60,
     'info': 'Amplia as coberturas médicas, de bagagem e de cancelamento.'},
]

INFORMACOES = [
    'Leve documento oficial com foto — RG ou CNH dentro da validade.',
    'Roupas leves, protetor solar, repelente e uma muda de roupa de banho.',
    'Os passeios têm nível leve a moderado: caminhadas curtas em terreno de areia e pedra.',
    'Bagagem recomendada: uma mala média por pessoa e uma mochila de ataque.',
    'O roteiro pode sofrer ajustes por condições climáticas, sempre priorizando a segurança do grupo.',
]

FAQ = [
    {'pergunta': 'Preciso ter experiência para fazer essa viagem?',
     'resposta': 'Não. O roteiro é pensado para todos os níveis, com caminhadas curtas e ritmo tranquilo.'},
    {'pergunta': 'Como funciona o pagamento?',
     'resposta': 'Em até 10x sem juros no cartão, boleto bancário ou PIX com desconto. '
                 'A vaga é confirmada com a entrada.'},
    {'pergunta': 'Posso viajar sozinho(a)?',
     'resposta': 'Sim! Boa parte do grupo viaja sozinha. Na acomodação dupla dividimos o quarto '
                 'com alguém do mesmo gênero.'},
    {'pergunta': 'E se eu precisar cancelar?',
     'resposta': 'Cancelamentos com até 30 dias da saída têm reembolso conforme as condições '
                 'gerais do contrato.'},
]

# --------------------------------------------------------------------------- #
# Ajustes por destino (chave = slug)
# --------------------------------------------------------------------------- #
POR_DESTINO = {
    'alter-do-chao': {
        'selo': 'Alter do Chão - PA',
        'subtitulo': 'O paraíso amazônico te espera',
        'regiao': 'Pará',
        'estado': 'Pará',
        'nota': '4,9',
        'total_avaliacoes': 128,
        'mais_fotos': 28,
        'embarque_cidade': 'São Paulo - SP',
        'data_sugerida': [2027, 5, 15],
        'fotos': ['img/alter-1.svg', 'img/alter-2.svg', 'img/alter-3.svg',
                  'img/alter-4.svg', 'img/alter-5.svg', 'img/alter-por-do-sol.svg'],
        'promo_foto': 'img/alter-por-do-sol.svg',
        'promo_titulo': 'Quer uma experiência ainda mais completa?',
        'promo_texto': 'Conheça nossos pacotes de 5 e 6 dias com roteiros exclusivos!',
        'precos': {
            'duplo': {'4d': 2980, '5d': 3480, '6d': 3980},
            'triplo': {'4d': 2780, '5d': 3250, '6d': 3720},
            'single': {'4d': 4280, '5d': 4980, '6d': 5680},
        },
        'opcionais': [
            {'chave': 'traslado', 'nome': 'Traslado particular (Aeroporto de Santarém / Hotel)',
             'unidade': 'Por trecho', 'preco': 120,
             'info': 'Carro exclusivo para você, com motorista aguardando no desembarque '
                     'do aeroporto de Santarém.'},
            {'chave': 'voadeira', 'nome': 'Passeio de voadeira ao Lago Verde',
             'unidade': 'Por pessoa', 'preco': 120,
             'info': 'Volta de voadeira pelo Lago Verde, com parada para banho nas praias de areia branca.'},
            {'chave': 'jantar', 'nome': 'Jantar especial com culinária regional',
             'unidade': 'Por pessoa', 'preco': 150,
             'info': 'Menu de três tempos com peixes do Tapajós, tucupi e jambu.'},
            {'chave': 'seguro', 'nome': 'Seguro viagem premium (cobertura ampliada)',
             'unidade': 'Por pessoa', 'preco': 60,
             'info': 'Amplia as coberturas médicas, de bagagem e de cancelamento.'},
        ],
        'destaques': [
            'Ilha do Amor', 'Lago Verde', 'Praia de Ponta de Pedras',
            'Floresta Nacional do Tapajós', 'Pôr do sol no Tapajós', 'Vila de Alter do Chão',
        ],
        'roteiro': [
            {'titulo': 'Dia 1 — Chegada em Santarém',
             'resumo': 'Recepção no aeroporto e traslado até a vila de Alter do Chão.',
             'detalhe': 'Recepção da equipe Soar no aeroporto de Santarém e traslado de cerca de '
                        '40 minutos até a vila. Check-in, tarde livre e encontro do grupo ao pôr do sol.'},
            {'titulo': 'Dia 2 — Ilha do Amor e Lago Verde',
             'resumo': 'Travessia para a Ilha do Amor e volta de barco pelo Lago Verde.',
             'detalhe': 'Manhã na Ilha do Amor, a faixa de areia branca que aparece na seca do Tapajós. '
                        'À tarde, passeio de barco pelo Lago Verde com paradas para banho.'},
            {'titulo': 'Dia 3 — Floresta Nacional do Tapajós',
             'resumo': 'Trilha guiada na floresta e visita a uma comunidade ribeirinha.',
             'detalhe': 'Dia inteiro na Flona do Tapajós: trilha interpretativa com guia local, '
                        'a sumaúma gigante e almoço em uma comunidade ribeirinha.'},
            {'titulo': 'Dia 4 — Ponta de Pedras e retorno',
             'resumo': 'Última manhã de praia e traslado de volta a Santarém.',
             'detalhe': 'Manhã livre na Praia de Ponta de Pedras, almoço na vila e traslado '
                        'para o aeroporto de Santarém conforme o horário do seu voo.'},
        ],
        'depoimento_destaque': {
            'texto': 'Lugar incrível! A Soar cuidou de tudo nos mínimos detalhes.',
            'nome': 'Mariana S.', 'local': 'São Paulo - SP',
        },
    },
    'jalapao': {
        'selo': 'Jalapão - TO',
        'subtitulo': 'Uma aventura no coração do Brasil',
        'regiao': 'Tocantins',
        'estado': 'Tocantins',
        'nota': '4,9',
        'total_avaliacoes': 87,
        'mais_fotos': 36,
        'embarque_cidade': 'São Paulo - SP',
        'data_sugerida': [2027, 6, 16],
        'precos': {
            'duplo': {'4d': 3588, '5d': 4120, '6d': 4640},
            'triplo': {'4d': 3388, '5d': 3890, '6d': 4380},
            'single': {'4d': 4988, '5d': 5620, '6d': 6240},
        },
        'destaques': [
            'Fervedouro do Alecrim', 'Dunas do Jalapão', 'Cânion Sussuapara',
            'Cachoeira da Velha', 'Pôr do sol nas Dunas', 'E muito mais',
        ],
        'roteiro': [
            {'titulo': 'Dia 1 — São Paulo → Palmas',
             'resumo': 'Embarque nos pontos de encontro e viagem noturna com destino a Palmas.',
             'detalhe': 'Encontro com a equipe Soar nos pontos combinados, embarque e viagem noturna. '
                        'Kit lanche a bordo e paradas programadas para descanso.'},
            {'titulo': 'Dia 2 — Palmas → Jalapão',
             'resumo': 'Chegada, café da manhã e início dos passeios.',
             'detalhe': 'Chegada em Palmas, café da manhã e transfer 4x4 para o Jalapão. '
                        'À tarde, primeiro banho de rio e apresentação do grupo ao pôr do sol.'},
            {'titulo': 'Dia 3 — Fervedouros e Cachoeiras',
             'resumo': 'Visita ao Fervedouro do Alecrim e Cachoeira da Velha.',
             'detalhe': 'Manhã no Fervedouro do Alecrim, onde a água brota do chão e é impossível afundar. '
                        'À tarde, mirante e banho na Cachoeira da Velha.'},
            {'titulo': 'Dia 4 — Dunas e Cânions',
             'resumo': 'Dunas do Jalapão, Cânion Sussuapara e Pôr do sol.',
             'detalhe': 'Travessia até as Dunas, caminhada no Cânion Sussuapara e o famoso pôr do sol '
                        'no alto das dunas alaranjadas — o cartão-postal da viagem.'},
            {'titulo': 'Dia 5 — Rio Sono e Cachoeiras',
             'resumo': 'Passeios guiados e tempo livre para relaxar.',
             'detalhe': 'Descida de bote no Rio Sono, parada nas cachoeiras do caminho e tarde livre '
                        'para descansar na pousada ou conhecer o artesanato de capim dourado.'},
            {'titulo': 'Dia 6 — Retorno',
             'resumo': 'Café da manhã, saída e previsão de chegada à noite.',
             'detalhe': 'Café da manhã, despedida do grupo e retorno a Palmas para o voo/ônibus de volta. '
                        'Previsão de chegada em São Paulo no fim da noite.'},
        ],
        'depoimento_destaque': {
            'texto': 'Foi sem dúvidas a maior aventura que já fiz. Tudo muito bem organizado!',
            'nome': 'Mariana S.', 'local': 'São Paulo - SP',
        },
    },
}

# preços genéricos quando o destino não tem tabela própria (multiplicam a diária)
FATOR_PACOTE = {'duplo': 1.0, 'triplo': 0.93, 'single': 1.44}
FATOR_DURACAO = {'4d': 1.0, '5d': 1.17, '6d': 1.33}


def _moeda(valor):
    """2980 -> '2.980'"""
    return '{:,.0f}'.format(valor).replace(',', '.')


def _estrelas(nota):
    """4.9 (ou '4,9') -> [True, True, True, True, True]"""
    cheias = int(round(float(str(nota).replace(',', '.'))))
    return [i < cheias for i in range(5)]


def _fotos_do_destino(destino, cfg):
    """Fotos cadastradas no admin; completa com os SVGs de exemplo."""
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
        ('Dia 1 — Chegada', 'Recepção do grupo e traslado até a hospedagem.',
         'Recepção da equipe Soar, traslado, check-in e encontro do grupo no fim da tarde.'),
        ('Dia 2 — {}'.format(nome), 'Os principais cartões-postais do destino.',
         'Dia inteiro de passeios guiados pelos pontos mais bonitos da região.'),
        ('Dia 3 — Natureza e cultura', 'Trilhas, banhos e contato com a cultura local.',
         'Roteiro de natureza pela manhã e imersão na cultura local à tarde.'),
        ('Dia 4 — Retorno', 'Manhã livre e traslado de volta.',
         'Manhã livre para as últimas fotos e traslado conforme o horário do seu voo.'),
        ('Dia 5 — Passeios opcionais', 'Tempo livre e passeios opcionais.',
         'Manhã de passeio opcional e tarde livre para descansar ou explorar por conta própria.'),
        ('Dia 6 — Despedida', 'Café da manhã, saída e previsão de chegada à noite.',
         'Café da manhã, despedida do grupo e retorno com previsão de chegada à noite.'),
    ]
    return [{'titulo': t, 'resumo': r, 'detalhe': d} for t, r, d in modelos]


def _pacotes(destino, cfg):
    """Monta os quatro cartões de acomodação, cada um com preço por duração."""
    tabela = cfg.get('precos')
    if not tabela:
        diaria = float(destino.preco_medio_diaria or 598)
        base = round(diaria * 5 / 10) * 10
        tabela = {
            chave: {d: int(round(base * FATOR_PACOTE[chave] * FATOR_DURACAO[d] / 10) * 10)
                    for d in FATOR_DURACAO}
            for chave in FATOR_PACOTE
        }

    modelos = [
        ('duplo', 'Duplo/Casal', '2 pessoas', True),
        ('triplo', 'Triplo', '3 pessoas', False),
        ('single', 'Single', '1 pessoa', False),
    ]
    pacotes = [{'chave': c, 'nome': n, 'pessoas': p, 'padrao': d,
                'consulte': False, 'precos': tabela[c]} for c, n, p, d in modelos]
    pacotes.append({'chave': 'crianca', 'nome': 'Criança (até 10 anos)', 'pessoas': '',
                    'padrao': False, 'consulte': True, 'precos': {}})
    return pacotes


def montar_viagem(destino, avaliacoes):
    """Monta o dicionário usado pelo template da página de viagem."""
    cfg = POR_DESTINO.get(destino.slug, {})
    fotos = _fotos_do_destino(destino, cfg)
    curto = destino.nome.split('/')[0].strip()

    nota = cfg.get('nota') or destino.media_avaliacoes or 4.9
    total = cfg.get('total_avaliacoes') or len(avaliacoes) or 87

    roteiro = cfg.get('roteiro') or _roteiro_generico(destino)
    for i, dia in enumerate(roteiro):
        dia['foto'] = fotos[(i + 1) % len(fotos)]

    pacotes = _pacotes(destino, cfg)
    duracoes = [dict(d) for d in DURACOES]
    opcionais = cfg.get('opcionais') or OPCIONAIS

    hospedagens = list(destino.hospedagens.filter(disponivel=True))
    for i, h in enumerate(hospedagens):
        h.foto_url = h.imagem.url if h.imagem else static(FOTOS_HOSPEDAGEM[i % len(FOTOS_HOSPEDAGEM)])

    depoimentos = []
    for i, av in enumerate(sorted(avaliacoes, key=lambda a: a.criado_em, reverse=True)):
        depoimentos.append({
            'nome': av.nome_autor,
            'local': destino.nome,
            'estrelas': _estrelas(av.nota),
            'texto': av.comentario,
            'avatar': static(AVATARES[i % len(AVATARES)]),
            'foto': av.foto.url if av.foto else '',
            'data': av.criado_em.strftime('%d/%m/%Y'),
        })

    destaque = cfg.get('depoimento_destaque') or (
        {'texto': depoimentos[0]['texto'], 'nome': depoimentos[0]['nome'],
         'local': depoimentos[0]['local']} if depoimentos else
        {'texto': 'Viagem impecável do começo ao fim. Recomendo de olhos fechados!',
         'nome': 'Mariana S.', 'local': 'São Paulo - SP'}
    )
    destaque = dict(destaque, avatar=static(AVATARES[0]), estrelas=_estrelas(5))

    ano, mes, dia = cfg.get('data_sugerida', [2027, 5, 15])
    pacote_padrao = next(p for p in pacotes if p['padrao'])
    duracao_padrao = next(d for d in duracoes if d['padrao'])

    # tudo o que o JavaScript precisa para o calendário e o cálculo do total
    dados = {
        'ano': ano, 'mes': mes, 'dia': dia,
        'duracoes': [{'chave': d['chave'], 'rotulo': d['rotulo']} for d in duracoes],
        'duracaoPadrao': duracao_padrao['chave'],
        'pacotes': [{'chave': p['chave'], 'nome': p['nome'], 'pessoas': p['pessoas'],
                     'consulte': p['consulte'], 'precos': p['precos']} for p in pacotes],
        'pacotePadrao': pacote_padrao['chave'],
        'opcionais': [{'chave': o['chave'], 'nome': o['nome'], 'preco': o['preco']}
                      for o in opcionais],
        'parcelas': 10,
    }

    return {
        'selo': cfg.get('selo') or '{} - {}'.format(curto, destino.pais),
        'subtitulo': cfg.get('subtitulo') or 'Uma aventura no coração do Brasil',
        'regiao': cfg.get('regiao') or destino.get_continente_display(),
        'estado': cfg.get('estado') or destino.pais,
        'curto': curto,
        'abas': ABAS,

        # hero
        'fotos': fotos,
        'thumbs': fotos[:5],
        'mais_fotos': cfg.get('mais_fotos', 28),
        'hero_meta': [
            {'icone': 'ic-calendario', 'titulo': 'Embarque diário',
             'sub': 'De acordo com a data escolhida'},
            {'icone': 'ic-lua', 'titulo': '4, 5 ou 6 dias', 'sub': 'Escolha a duração ideal'},
            {'icone': 'ic-grupo', 'titulo': 'Viagem em grupo', 'sub': 'Saídas garantidas'},
        ],

        # aba "Escolha sua viagem"
        'duracoes': duracoes,
        'pacotes': pacotes,
        'incluso_itens': INCLUSO_ITENS,
        'opcionais': opcionais,
        'promo': {
            'foto': static(cfg.get('promo_foto', 'img/alter-por-do-sol.svg')),
            'titulo': cfg.get('promo_titulo', 'Quer uma experiência ainda mais completa?'),
            'texto': cfg.get('promo_texto',
                             'Conheça nossos pacotes de 5 e 6 dias com roteiros exclusivos!'),
        },

        # demais abas
        'destaques': cfg.get('destaques') or [
            'Roteiro completo', 'Guias especializados', 'Grupo pequeno',
            'Hospedagem selecionada', 'Passeios inclusos', 'E muito mais',
        ],
        'roteiro': roteiro,
        'incluso': INCLUSO,
        'nao_incluso': NAO_INCLUSO,
        'informacoes': INFORMACOES,
        'faq': FAQ,
        'hospedagens': hospedagens,
        'comodidades': COMODIDADES,
        'depoimentos': depoimentos,

        # lateral
        'embarque_cidade': cfg.get('embarque_cidade', 'São Paulo - SP'),
        'pagamentos': PAGAMENTOS,
        'confianca': CONFIANCA,
        'nota': str(nota).replace('.', ','),
        'estrelas': _estrelas(nota),
        'total_avaliacoes': total,
        'depoimento_destaque': destaque,
        'preco_inicial': _moeda(pacote_padrao['precos'][duracao_padrao['chave']]),

        'dados': dados,
    }
