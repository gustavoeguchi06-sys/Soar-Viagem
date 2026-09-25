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
    'lencois-maranhenses': {
        'selo': 'Expedição',
        'subtitulo': 'Dunas brancas e lagoas azuis a perder de vista',
        'regiao': 'Nordeste',
        'estado': 'Maranhão',
        'hospedagem_nome': 'Pousada parceira em Barreirinhas',
        'hospedagem_sub': 'Na beira do Rio Preguiças',
        'fotos': ['img/dunas.svg', 'img/rio.svg', 'img/palmeiras.svg',
                  'img/hero-jalapao.svg', 'img/placa.svg', 'img/cachoeira.svg'],
        'destaques': [
            'Lagoa Azul', 'Lagoa Bonita', 'Rio Preguiças',
            'Vassouras e Mandacaru', 'Caburé', 'Pôr do sol nas dunas',
        ],
        'roteiro': [
            {'titulo': 'Dia 1: São Luís → Barreirinhas',
             'resumo': 'Recepção em São Luís e estrada até Barreirinhas.',
             'detalhe': 'Recepção da equipe Soar no aeroporto de São Luís e viagem de cerca de '
                        '4 horas até Barreirinhas, a porta de entrada do parque. Check-in e jantar '
                        'de boas-vindas com o grupo.'},
            {'titulo': 'Dia 2: Circuito Lagoa Azul',
             'resumo': 'Travessia de 4x4 e caminhada entre as dunas até a Lagoa Azul.',
             'detalhe': 'Saída de 4x4 com travessia do Rio Preguiças de balsa. Caminhada leve pelas '
                        'dunas até a Lagoa Azul e a Lagoa Esmeralda, com tempo para banho.'},
            {'titulo': 'Dia 3: Lagoa Bonita e pôr do sol',
             'resumo': 'Subida da grande duna da Lagoa Bonita e pôr do sol no parque.',
             'detalhe': 'À tarde, subida da duna mais alta do circuito até a Lagoa Bonita, banho '
                        'nas lagoas e o pôr do sol sobre os Lençóis, o momento mais bonito da viagem.'},
            {'titulo': 'Dia 4: Rio Preguiças',
             'resumo': 'Passeio de lancha até Vassouras, Mandacaru e Caburé.',
             'detalhe': 'Descida do Rio Preguiças com paradas nos Pequenos Lençóis de Vassouras, '
                        'no farol de Mandacaru e almoço em Caburé, entre o rio e o mar.'},
            {'titulo': 'Dia 5: Retorno',
             'resumo': 'Café da manhã e estrada de volta a São Luís.',
             'detalhe': 'Café da manhã, despedida de Barreirinhas e retorno a São Luís para o voo '
                        'de volta, conforme o horário de cada um.'},
        ],
    },
    'bonito': {
        'selo': 'Expedição',
        'subtitulo': 'Rios de água cristalina no coração do Mato Grosso do Sul',
        'regiao': 'Centro-Oeste',
        'estado': 'Mato Grosso do Sul',
        'hospedagem_nome': 'Pousada parceira no centro de Bonito',
        'hospedagem_sub': 'A poucos passos da rua principal',
        'fotos': ['img/rio.svg', 'img/cachoeira.svg', 'img/palmeiras.svg',
                  'img/hero-jalapao.svg', 'img/dunas.svg', 'img/placa.svg'],
        'destaques': [
            'Flutuação no Rio da Prata', 'Gruta do Lago Azul', 'Buraco das Araras',
            'Balneário Municipal', 'Cachoeiras da Boca da Onça', 'Centrinho de Bonito',
        ],
        'roteiro': [
            {'titulo': 'Dia 1: Campo Grande → Bonito',
             'resumo': 'Recepção em Campo Grande e estrada até Bonito.',
             'detalhe': 'Recepção da equipe Soar no aeroporto de Campo Grande e viagem de cerca de '
                        '4 horas até Bonito. Check-in e noite livre no centrinho.'},
            {'titulo': 'Dia 2: Gruta do Lago Azul e Balneário',
             'resumo': 'A gruta de água azul pela manhã e banho de rio à tarde.',
             'detalhe': 'Manhã na Gruta do Lago Azul, um dos cartões-postais da região. À tarde, '
                        'banho no Balneário Municipal, cheio de peixes na água transparente.'},
            {'titulo': 'Dia 3: Flutuação no Rio da Prata',
             'resumo': 'Flutuação com snorkel em um dos rios mais cristalinos do país.',
             'detalhe': 'Trilha curta pela mata e flutuação de colete e snorkel no Rio da Prata, '
                        'entre peixes e nascentes. Almoço na fazenda.'},
            {'titulo': 'Dia 4: Buraco das Araras e cachoeiras',
             'resumo': 'Dolina com araras-vermelhas e dia de cachoeiras.',
             'detalhe': 'Manhã no Buraco das Araras, uma dolina gigante onde vivem araras-vermelhas. '
                        'À tarde, trilha e banho nas cachoeiras da Boca da Onça.'},
            {'titulo': 'Dia 5: Retorno',
             'resumo': 'Café da manhã e estrada de volta a Campo Grande.',
             'detalhe': 'Café da manhã, despedida do grupo e retorno a Campo Grande para o voo de volta.'},
        ],
    },
    'serra-da-canastra': {
        'selo': 'Natureza',
        'subtitulo': 'Onde nasce o Rio São Francisco',
        'regiao': 'Sudeste',
        'estado': 'Minas Gerais',
        'hospedagem_nome': 'Pousada parceira em São Roque de Minas',
        'hospedagem_sub': 'Pé na serra, café mineiro na mesa',
        'fotos': ['img/cachoeira.svg', 'img/hero-jalapao.svg', 'img/rio.svg',
                  'img/placa.svg', 'img/palmeiras.svg', 'img/dunas.svg'],
        'destaques': [
            'Nascente do São Francisco', 'Cachoeira Casca d’Anta', 'Parte alta do parque',
            'Queijo canastra na fazenda', 'Mirantes da serra', 'São Roque de Minas',
        ],
        'roteiro': [
            {'titulo': 'Dia 1: Belo Horizonte → São Roque de Minas',
             'resumo': 'Recepção em Belo Horizonte e estrada até a serra.',
             'detalhe': 'Recepção da equipe Soar em Belo Horizonte e viagem até São Roque de Minas, '
                        'a cidade na porta do Parque Nacional. Jantar mineiro com o grupo.'},
            {'titulo': 'Dia 2: Parte alta e nascente',
             'resumo': 'Nascente do São Francisco e mirantes da parte alta do parque.',
             'detalhe': 'Dia de 4x4 pela parte alta do parque: a nascente histórica do Rio São '
                        'Francisco, os campos de altitude e o mirante da Casca d’Anta vista de cima.'},
            {'titulo': 'Dia 3: Cachoeira Casca d’Anta',
             'resumo': 'Trilha até a base da maior cachoeira do parque.',
             'detalhe': 'Trilha leve pela parte baixa até o poço da Casca d’Anta, com mais de '
                        '180 metros de queda. Tempo para banho e piquenique.'},
            {'titulo': 'Dia 4: Queijo e retorno',
             'resumo': 'Visita a uma fazenda de queijo canastra e volta para BH.',
             'detalhe': 'Manhã em uma fazenda de queijo canastra, com degustação, e retorno a Belo '
                        'Horizonte com previsão de chegada à noite.'},
        ],
    },
    'canions-do-sul': {
        'selo': 'Expedição',
        'subtitulo': 'Os grandes cânions entre a serra gaúcha e o litoral catarinense',
        'regiao': 'Sul',
        'estado': 'Rio Grande do Sul',
        'hospedagem_nome': 'Pousada parceira em Cambará do Sul',
        'hospedagem_sub': 'Lareira acesa e vista para os campos',
        'fotos': ['img/hero-jalapao.svg', 'img/cachoeira.svg', 'img/rio.svg',
                  'img/placa.svg', 'img/dunas.svg', 'img/palmeiras.svg'],
        'destaques': [
            'Cânion Itaimbezinho', 'Cânion Fortaleza', 'Trilha do Rio do Boi',
            'Cachoeira dos Venâncios', 'Campos de cima da serra', 'Praia Grande (SC)',
        ],
        'roteiro': [
            {'titulo': 'Dia 1: Porto Alegre → Cambará do Sul',
             'resumo': 'Recepção em Porto Alegre e subida da serra.',
             'detalhe': 'Recepção da equipe Soar em Porto Alegre e viagem de cerca de 3 horas até '
                        'Cambará do Sul. Check-in e jantar com o grupo.'},
            {'titulo': 'Dia 2: Cânion Itaimbezinho',
             'resumo': 'Trilhas do Vértice e do Cotovelo na borda do cânion.',
             'detalhe': 'Parque Nacional de Aparados da Serra: trilhas leves na borda do Itaimbezinho, '
                        'com as cachoeiras caindo cânion abaixo.'},
            {'titulo': 'Dia 3: Cânion Fortaleza',
             'resumo': 'Mirantes do Fortaleza e a Pedra do Segredo.',
             'detalhe': 'Parque Nacional da Serra Geral: trilha até os mirantes do Cânion Fortaleza, '
                        'de onde se vê o litoral em dia limpo, e a Pedra do Segredo.'},
            {'titulo': 'Dia 4: Os cânions por baixo',
             'resumo': 'Descida até Praia Grande e trilha do Rio do Boi.',
             'detalhe': 'Descida da serra até Praia Grande (SC) e trilha pelo leito do Rio do Boi, '
                        'dentro do Itaimbezinho, vendo o cânion de baixo para cima.'},
            {'titulo': 'Dia 5: Retorno',
             'resumo': 'Café da manhã e volta para Porto Alegre.',
             'detalhe': 'Café da manhã, despedida do grupo e retorno a Porto Alegre para o voo de volta.'},
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
        'preco_base': 3588,
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
    # Nota e quantidade vêm só das avaliações publicadas de verdade. Número
    # inventado na vitrine é propaganda enganosa (CDC, art. 37): sem nenhuma
    # avaliação, a página diz isso em vez de mostrar uma nota.
    nota = destino.media_avaliacoes
    total = len(avaliacoes)

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
        'nota': str(nota).replace('.', ',') if nota is not None else '',
        'estrelas': _estrelas(nota or 0),
        'total_avaliacoes': total,
        'fotos': fotos,
        'thumbs': fotos[1:5] if len(fotos) > 4 else fotos,
        'galeria': fotos,
        # as fotos que não cabem nas miniaturas do topo; o botão leva à galeria
        'mais_fotos': max(len(fotos) - 5, 0),
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
            # Criança até 8 anos não paga a viagem.
            {'chave': 'crianca', 'nome': 'Criança até 8 anos', 'pessoas': 'Não paga a viagem',
             'preco': 'Grátis', 'valor': 0, 'padrao': False, 'consulte': False, 'gratis': True},
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
