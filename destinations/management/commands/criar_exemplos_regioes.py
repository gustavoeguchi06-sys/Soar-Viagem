# -*- coding: utf-8 -*-
"""Cria um destino de exemplo para cada região que ainda não tem nenhum.

    python manage.py criar_exemplos_regioes

O catálogo filtra por região (Norte, Nordeste, Centro-Oeste, Sudeste, Sul).
Para a apresentação, cada filtro precisa mostrar ao menos uma viagem. O
Jalapão já cobre o Norte; este comando cria as outras quatro com textos,
datas de saída, preço por pessoa e hospedagem. Os roteiros e destaques vêm de
destinations/conteudo.py e são copiados para o banco pelo importar_conteudo,
para o dono poder editar tudo no painel.

Não mexe em destino que já existe (compara pelo endereço/slug), então pode
rodar de novo sem duplicar nada.
"""
from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from destinations.models import Destino, Hospedagem, Saida

EXEMPLOS = [
    {
        'slug': 'lencois-maranhenses', 'nome': 'Lençóis Maranhenses', 'regiao': 'Nordeste',
        'descricao': 'Um deserto de dunas brancas pontilhado de lagoas de água doce azul-turquesa. '
                     'Entre junho e setembro, as chuvas do começo do ano enchem as lagoas e o '
                     'parque fica no auge. Base em Barreirinhas, na beira do Rio Preguiças.',
        'melhor_epoca': 'Junho a setembro', 'preco_base': 3290,
        'hospedagem': 'Pousada parceira em Barreirinhas',
        'saidas': [((2027, 6, 17), (2027, 6, 21), 14), ((2027, 7, 15), (2027, 7, 19), 12),
                   ((2027, 8, 19), (2027, 8, 23), 14)],
    },
    {
        'slug': 'bonito', 'nome': 'Bonito', 'regiao': 'Centro-Oeste',
        'descricao': 'Rios de água tão transparente que dá para ver cada peixe, grutas de água '
                     'azul, cachoeiras e flutuação com snorkel. Um roteiro de natureza tranquilo, '
                     'bom para todas as idades.',
        'melhor_epoca': 'O ano todo; de maio a setembro a água fica ainda mais clara',
        'preco_base': 3690,
        'hospedagem': 'Pousada parceira no centro de Bonito',
        'saidas': [((2027, 5, 20), (2027, 5, 24), 12), ((2027, 7, 22), (2027, 7, 26), 12),
                   ((2027, 9, 16), (2027, 9, 20), 10)],
    },
    {
        'slug': 'serra-da-canastra', 'nome': 'Serra da Canastra', 'regiao': 'Sudeste',
        'descricao': 'Campos de altitude, a nascente do Rio São Francisco e a Casca d’Anta, '
                     'com mais de 180 metros de queda. De quebra, o queijo canastra direto da '
                     'fazenda, no interior de Minas Gerais.',
        'melhor_epoca': 'Abril a outubro', 'preco_base': 2490,
        'hospedagem': 'Pousada parceira em São Roque de Minas',
        'saidas': [((2027, 5, 6), (2027, 5, 9), 14), ((2027, 6, 10), (2027, 6, 13), 14),
                   ((2027, 8, 5), (2027, 8, 8), 12)],
    },
    {
        'slug': 'canions-do-sul', 'nome': 'Cânions do Sul', 'regiao': 'Sul',
        'descricao': 'Paredões de centenas de metros entre a serra gaúcha e o litoral '
                     'catarinense: Itaimbezinho, Fortaleza e o Rio do Boi, nos parques nacionais '
                     'de Aparados da Serra e Serra Geral. Base em Cambará do Sul.',
        'melhor_epoca': 'Abril a setembro', 'preco_base': 3190,
        'hospedagem': 'Pousada parceira em Cambará do Sul',
        'saidas': [((2027, 4, 21), (2027, 4, 25), 12), ((2027, 6, 23), (2027, 6, 27), 12),
                   ((2027, 9, 8), (2027, 9, 12), 14)],
    },
]


class Command(BaseCommand):
    help = 'Cria um destino de exemplo para cada região do Brasil que ainda não tem.'

    @transaction.atomic
    def handle(self, *args, **opcoes):
        criados = 0
        for ex in EXEMPLOS:
            if Destino.objects.filter(slug=ex['slug']).exists():
                self.stdout.write('{}: já existe, nada a fazer.'.format(ex['nome']))
                continue
            destino = Destino.objects.create(
                slug=ex['slug'], nome=ex['nome'], pais='Brasil', regiao=ex['regiao'],
                descricao=ex['descricao'], melhor_epoca=ex['melhor_epoca'],
                preco_base=ex['preco_base'], destaque=True,
            )
            for ida, volta, vagas in ex['saidas']:
                Saida.objects.create(destino=destino, data_ida=date(*ida),
                                     data_volta=date(*volta), vagas=vagas)
            Hospedagem.objects.create(destino=destino, nome=ex['hospedagem'], pacote_completo=True)
            criados += 1
            self.stdout.write('{}: criado ({}).'.format(ex['nome'], ex['regiao']))

        if criados:
            # selo, subtítulo, estado, destaques, roteiro e FAQ vêm do conteudo.py
            call_command('importar_conteudo', stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS('{} destino(s) de exemplo criado(s).'.format(criados)))
