"""Traz para o banco o que o blog mostrava como página fixa.

O artigo do Jalapão vem completo e publicado, no mesmo endereço de antes
(/blog/jalapao/). Os outros sete cartões da vitrine só tinham título e resumo,
sem texto nenhum atrás (todos abriam o artigo do Jalapão); eles entram como
rascunho, para o dono escrever e publicar pelo painel quando quiser.
"""
from datetime import date

from django.db import migrations

CATEGORIAS = [
    ('Destinos', 'destinos', 'pin'),
    ('Dicas de Viagem', 'dicas-de-viagem', 'mala'),
    ('Natureza', 'natureza', 'coracao'),
    ('Roteiros', 'roteiros', 'doc'),
    ('Experiências', 'experiencias', 'camera'),
    ('Soar 60+', 'soar-60', 'grupo'),
]

RASCUNHOS = [
    # titulo, slug, resumo, categoria, etiqueta, cor, data, destino
    ('Alter do Chão: o paraíso amazônico do Pará', 'alter-do-chao',
     'Conheça as belezas de Alter do Chão e por que esse destino deve estar no seu próximo roteiro.',
     'destinos', 'Alter do Chão', 'teal', date(2024, 5, 10), 'alter-do-chao'),
    ('Serra da Canastra: o que fazer e melhores cachoeiras', 'serra-da-canastra',
     'Um guia completo para você explorar um dos parques mais incríveis do Brasil.',
     'natureza', 'Serra da Canastra', 'verde', date(2024, 5, 5), None),
    ('Santuário do Caraça: história, fé e natureza', 'santuario-do-caraca',
     'Um lugar que une espiritualidade, história e paisagens de tirar o fôlego.',
     'experiencias', 'Santuário do Caraça', 'roxo', date(2024, 5, 2), None),
    ('O que levar na mala para o Jalapão?', 'o-que-levar-na-mala-para-o-jalapao',
     'Lista completa para você não esquecer nada e aproveitar cada momento.',
     'dicas-de-viagem', 'Dicas de Viagem', 'laranja', date(2024, 4, 28), 'jalapao'),
    ('Por que viajar em grupo transforma experiências?', 'por-que-viajar-em-grupo',
     'Conheça os benefícios de viajar em grupo e fazer novas amizades.',
     'experiencias', 'Viajar em grupo', 'rosa', date(2024, 4, 25), None),
    ('Chapada das Mesas: belezas escondidas do Maranhão', 'chapada-das-mesas',
     'Cachoeiras, trilhas e paisagens incríveis que você precisa conhecer.',
     'destinos', 'Chapada das Mesas', 'azul', date(2024, 4, 22), None),
    ('Viagens 60+: conforto, segurança e novas amizades', 'viagens-60-mais',
     'Nossas viagens são pensadas para quem quer viver novas histórias.',
     'soar-60', 'Soar 60+', 'laranja', date(2024, 4, 22), None),
]


def criar(apps, schema_editor):
    Categoria = apps.get_model('blog', 'Categoria')
    Artigo = apps.get_model('blog', 'Artigo')
    Secao = apps.get_model('blog', 'Secao')
    Atracao = apps.get_model('blog', 'Atracao')
    Destino = apps.get_model('destinations', 'Destino')

    cat = {}
    for ordem, (nome, slug, icone) in enumerate(CATEGORIAS, start=1):
        cat[slug], _ = Categoria.objects.get_or_create(
            slug=slug, defaults={'nome': nome, 'icone': icone, 'ordem': ordem})

    def destino(slug):
        return Destino.objects.filter(slug=slug).first() if slug else None

    if not Artigo.objects.filter(slug='jalapao').exists():
        jalapao = Artigo.objects.create(
            titulo='Jalapão: guia completo para sua viagem inesquecível',
            slug='jalapao',
            categoria=cat['destinos'],
            resumo='Descubra tudo sobre o Jalapão: quando ir, o que fazer, onde se hospedar, '
                   'quanto custa e dicas essenciais.',
            autor='Equipe Soar',
            publicado=True,
            data_publicacao=date(2024, 5, 15),
            destaque=True,
            etiqueta='Jalapão',
            cor_etiqueta='verde',
            destino=destino('jalapao'),
            introducao=(
                'O Jalapão é um dos destinos mais surpreendentes do Brasil. Dunas douradas, '
                'fervedouros de águas cristalinas, cachoeiras incríveis e paisagens de tirar o '
                'fôlego fazem desse paraíso no Tocantins um lugar único e inesquecível.\n\n'
                'Se você está planejando sua viagem, preparamos este guia completo com todas as '
                'informações que você precisa para aproveitar o melhor do Jalapão!'),
        )
        secoes = [
            dict(titulo='Sobre o Jalapão', icone='info',
                 texto='Localizado no estado do Tocantins, o Jalapão é uma região preservada e '
                       'pouco explorada pelo turismo de massa. Suas belezas naturais '
                       'impressionam: fervedouros, cachoeiras, formações rochosas, rios de águas '
                       'cristalinas e o famoso pôr do sol nas dunas.',
                 nota='O Jalapão é um destino de natureza e aventura. Prepare-se para dias '
                      'intensos e cenários que parecem de outro planeta!'),
            dict(titulo='Quando ir ao Jalapão?', icone='calendario',
                 texto='A melhor época para visitar o Jalapão é durante a estação seca, entre '
                       'maio e setembro, quando as estradas estão em melhores condições e os '
                       'passeios ficam ainda mais incríveis.',
                 melhores_meses='5,6,7,8,9'),
            dict(titulo='O que fazer no Jalapão', icone='camera',
                 texto='Prepare-se para conhecer lugares incríveis e colecionar memórias '
                       'inesquecíveis.',
                 mostrar_atracoes=True),
            dict(titulo='Como chegar', icone='onibus',
                 texto='O acesso ao Jalapão é feito principalmente pela cidade de Palmas (TO). De '
                       'lá, os passeios começam em veículos 4x4, pois as estradas são de terra.',
                 nota='A Soar cuida de toda a logística para você: transporte, guia, hospedagem '
                      'e passeios. É só aproveitar!'),
            dict(titulo='Dicas essenciais para sua viagem', icone='escudo',
                 dicas='Leve roupas leves, chapéu, óculos de sol e protetor solar.\n'
                       'Hidrate-se bastante! O clima é quente e seco.\n'
                       'Leve dinheiro em espécie. Não há bancos ou caixas eletrônicos na região.\n'
                       'Respeite a natureza e preserve esse paraíso.\n'
                       'Viaje com uma operadora experiente e aproveite com segurança.'),
        ]
        for ordem, dados in enumerate(secoes, start=1):
            Secao.objects.create(artigo=jalapao, ordem=ordem, **dados)
        atracoes = [
            ('Fervedouro do Alecrim', 'Experiência única de flutuar nas águas cristalinas.'),
            ('Cachoeira da Velha', 'Uma das cachoeiras mais famosas da região.'),
            ('Dunas do Jalapão', 'Pôr do sol inesquecível nas dunas douradas.'),
            ('Cânion Sussuapara', 'Trilha leve com vista espetacular do cânion.'),
        ]
        for ordem, (nome, frase) in enumerate(atracoes, start=1):
            Atracao.objects.create(artigo=jalapao, ordem=ordem, nome=nome, descricao=frase)

    for titulo, slug, resumo, categoria, etiqueta, cor, data, dest in RASCUNHOS:
        Artigo.objects.get_or_create(slug=slug, defaults=dict(
            titulo=titulo, resumo=resumo, categoria=cat[categoria], etiqueta=etiqueta,
            cor_etiqueta=cor, data_publicacao=data, publicado=False, autor='Equipe Soar',
            destino=destino(dest)))


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
        ('destinations', '0009_tira_travessao_do_conteudo'),
    ]

    operations = [
        migrations.RunPython(criar, migrations.RunPython.noop),
    ]
