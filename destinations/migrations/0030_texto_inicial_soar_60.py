"""Cartões, passos e perguntas da página Soar 60+ como estavam escritos no código.

A página passa a vir do painel; esta migração põe nele o mesmo conteúdo que já
estava no ar, para nada mudar no site até o dono editar. Os títulos e frases
já vêm dos valores padrão dos campos.
"""
from django.db import migrations

ITENS = [
    ('ic-relogio', 'Ritmo sem pressa',
     'Menos paradas por dia, mais tempo em cada uma. Nada de acordar às quatro da manhã '
     'para não perder nada.'),
    ('ic-guia', 'Guia junto o tempo todo',
     'Alguém da Soar acompanha o grupo do embarque ao desembarque. Não é só levar até o '
     'lugar e sumir.'),
    ('ic-grupo', 'Grupo pequeno',
     'Gente na mesma fase da vida, em turmas que cabem numa mesa de jantar. Muita gente '
     'viaja sozinha e volta com amizade.'),
    ('ic-hotel', 'Hospedagem no centro',
     'Perto do que interessa, com elevador e quarto no plano certo. Menos caminhada até a '
     'cama no fim do dia.'),
    ('ic-escudo', 'Seguro e apoio',
     'Seguro viagem incluso e um telefone da Soar que atende, inclusive para a família que '
     'ficou em casa.'),
]

PASSOS = [
    ('Escolha a viagem',
     'Abra o destino que te interessou: lá estão o roteiro dia a dia, as datas de saída, o '
     'que está incluso e quanto custa por pessoa.'),
    ('Peça sua vaga',
     'Fale com a sua agência de viagens parceira da Soar e diga qual viagem, a data e '
     'quantas pessoas vão. Nada é cobrado no site.'),
    ('A agência confirma com você',
     'A agência confirma a vaga com a Soar, tira as dúvidas e combina o pagamento do jeito '
     'que for melhor para você.'),
]

PERGUNTAS = [
    ('Preciso viajar acompanhado?',
     'Não. Boa parte do grupo viaja sozinha. É justamente por isso que as turmas são '
     'pequenas e o guia fica junto o tempo todo.'),
    ('E se eu tiver dificuldade para caminhar?',
     'Conte para a gente na hora de reservar. Cada roteiro tem alternativa mais leve, e em '
     'alguns destinos dá para acompanhar o grupo de carro até o ponto de encontro.'),
    ('Tomo remédio de horário. Isso é um problema?',
     'Não é. Avise no pedido de reserva: o guia leva a informação com ele e as paradas do '
     'dia são organizadas com isso em conta.'),
    ('Como pago?',
     'Nada é cobrado no site. Depois que a vaga é confirmada, a equipe combina com você a '
     'forma e o parcelamento.'),
    ('Posso levar meu neto ou minha filha?',
     'Pode. As saídas 60+ têm ritmo próprio, mas ninguém fica de fora: é só avisar quantas '
     'pessoas vão no pedido de reserva.'),
]


def criar(apps, schema_editor):
    PaginaSoar60 = apps.get_model('destinations', 'PaginaSoar60')
    ItemSoar60 = apps.get_model('destinations', 'ItemSoar60')
    PassoSoar60 = apps.get_model('destinations', 'PassoSoar60')
    PerguntaSoar60 = apps.get_model('destinations', 'PerguntaSoar60')
    # a foto, se já foi enviada, mora no registro que existe
    pagina = PaginaSoar60.objects.first() or PaginaSoar60.objects.create()
    if not ItemSoar60.objects.filter(pagina=pagina).exists():
        ItemSoar60.objects.bulk_create([
            ItemSoar60(pagina=pagina, icone=icone, titulo=titulo, texto=texto, ordem=i)
            for i, (icone, titulo, texto) in enumerate(ITENS)])
    if not PassoSoar60.objects.filter(pagina=pagina).exists():
        PassoSoar60.objects.bulk_create([
            PassoSoar60(pagina=pagina, titulo=titulo, texto=texto, ordem=i)
            for i, (titulo, texto) in enumerate(PASSOS)])
    if not PerguntaSoar60.objects.filter(pagina=pagina).exists():
        PerguntaSoar60.objects.bulk_create([
            PerguntaSoar60(pagina=pagina, pergunta=pergunta, resposta=resposta, ordem=i)
            for i, (pergunta, resposta) in enumerate(PERGUNTAS)])


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0029_pagina_soar_60_textos'),
    ]

    operations = [
        migrations.RunPython(criar, migrations.RunPython.noop),
    ]
