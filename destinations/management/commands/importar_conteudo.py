# -*- coding: utf-8 -*-
"""Traz para o painel os textos que hoje moram no código.

    python manage.py importar_conteudo

A página de viagem sabe se virar sem nada cadastrado: o que falta ela pega de
`destinations/conteudo.py`. O problema é que, assim, o dono do site abre o
Jalapão no painel e vê os campos vazios — não dá para editar o que está no
código. Este comando copia esse conteúdo para o banco uma vez; a partir daí
tudo é editável pelo /painel/.

Não sobrescreve nada que já esteja preenchido (a não ser com --forcar), então
pode rodar de novo sem medo.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from destinations.conteudo import FAQ, INCLUSO, INFORMACOES, POR_DESTINO
from destinations.models import Destino, DestaqueViagem, DiaRoteiro, PerguntaFrequente

CAMPOS_SIMPLES = ['selo', 'subtitulo', 'regiao', 'estado', 'periodo', 'mes_ano',
                  'dias', 'noites', 'proxima_saida', 'hospedagem_sub']


class Command(BaseCommand):
    help = 'Copia o conteúdo editorial do código para o banco, para o dono editar no painel.'

    def add_arguments(self, parser):
        parser.add_argument('--forcar', action='store_true',
                            help='Sobrescreve o que já estiver preenchido no painel.')

    @transaction.atomic
    def handle(self, *args, **opcoes):
        forcar = opcoes['forcar']
        tocados = 0

        for destino in Destino.objects.all():
            cfg = POR_DESTINO.get(destino.slug, {})
            mudou = []

            for campo in CAMPOS_SIMPLES:
                valor = cfg.get(campo)
                if valor and (forcar or not getattr(destino, campo)):
                    setattr(destino, campo, valor)
                    mudou.append(campo)

            if cfg.get('vagas') and (forcar or destino.vagas is None):
                destino.vagas = cfg['vagas']
                mudou.append('vagas')

            if cfg.get('preco_base') and (forcar or destino.preco_base is None):
                destino.preco_base = cfg['preco_base']
                mudou.append('preco_base')

            # as duas listas são iguais para todos os destinos hoje
            if forcar or not destino.incluso:
                destino.incluso = '\n'.join(INCLUSO)
                mudou.append('incluso')
            if forcar or not destino.informacoes:
                destino.informacoes = '\n'.join(INFORMACOES)
                mudou.append('informacoes')

            if mudou:
                destino.save()

            mudou += self._destaques(destino, cfg, forcar)
            mudou += self._roteiro(destino, cfg, forcar)
            mudou += self._faq(destino, forcar)

            if mudou:
                tocados += 1
                self.stdout.write('{}: {}'.format(destino.nome, ', '.join(mudou)))

        if tocados:
            self.stdout.write(self.style.SUCCESS(
                '\n{} destino(s) atualizados — agora dá para editar tudo em /painel/.'.format(
                    tocados)))
        else:
            self.stdout.write('Nada a fazer: o conteúdo já está no painel.')

    def _destaques(self, destino, cfg, forcar):
        textos = cfg.get('destaques')
        if not textos:
            return []
        if destino.destaques_viagem.exists():
            if not forcar:
                return []
            destino.destaques_viagem.all().delete()
        DestaqueViagem.objects.bulk_create([
            DestaqueViagem(destino=destino, ordem=i, texto=texto)
            for i, texto in enumerate(textos)
        ])
        return ['destaques']

    def _roteiro(self, destino, cfg, forcar):
        dias = cfg.get('roteiro')
        if not dias:
            return []
        if destino.roteiro.exists():
            if not forcar:
                return []
            destino.roteiro.all().delete()
        DiaRoteiro.objects.bulk_create([
            DiaRoteiro(destino=destino, ordem=i, titulo=dia['titulo'],
                       resumo=dia['resumo'], detalhe=dia.get('detalhe', ''))
            for i, dia in enumerate(dias)
        ])
        return ['roteiro']

    def _faq(self, destino, forcar):
        if destino.perguntas.exists():
            if not forcar:
                return []
            destino.perguntas.all().delete()
        PerguntaFrequente.objects.bulk_create([
            PerguntaFrequente(destino=destino, ordem=i,
                              pergunta=item['pergunta'], resposta=item['resposta'])
            for i, item in enumerate(FAQ)
        ])
        return ['faq']
