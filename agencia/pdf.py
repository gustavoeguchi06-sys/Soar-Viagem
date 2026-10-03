"""O PDF do orçamento que vai por e-mail para o cliente da agência.

Feito com o ReportLab, em Helvetica: cobre todo o português, mas não símbolos
como a seta "→" do roteiro. `_texto` troca esses símbolos antes de escrever, em
vez de deixar um quadradinho preto no PDF.
"""
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.utils.formats import number_format
from django.utils.html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from destinations.conteudo import montar_viagem

from .models import AVISO

VERDE = colors.HexColor('#146c43')
CINZA = colors.HexColor('#5b6660')
LINHA = colors.HexColor('#dfe5e1')
AVISO_FUNDO = colors.HexColor('#fdf3e1')
AVISO_BORDA = colors.HexColor('#d97706')

LOGO = Path(settings.BASE_DIR) / 'static' / 'img' / 'logo-soar.png'

TROCAS = {'→': '-', '←': '-', '–': '-', '—': '-', '•': '-', '“': '"', '”': '"',
          '‘': "'", '’': "'", '…': '...'}


def _sem_simbolos(valor):
    """Só os caracteres que a Helvetica tem; a seta do roteiro vira hífen."""
    texto = ''.join(TROCAS.get(c, c) for c in str(valor or ''))
    return texto.encode('cp1252', 'ignore').decode('cp1252')


def _texto(valor):
    """Texto seguro para o Paragraph: sem HTML e só com caracteres da Helvetica."""
    return escape(_sem_simbolos(valor))


def _reais(valor):
    return 'R$ ' + number_format(valor, decimal_pos=2, force_grouping=True)


def _estilos():
    base = getSampleStyleSheet()
    return {
        'titulo': ParagraphStyle('titulo', parent=base['Title'], fontName='Helvetica-Bold',
                                 fontSize=18, leading=22, textColor=VERDE, alignment=0,
                                 spaceAfter=2),
        'sub': ParagraphStyle('sub', parent=base['Normal'], fontSize=9, textColor=CINZA),
        'secao': ParagraphStyle('secao', parent=base['Heading2'], fontName='Helvetica-Bold',
                                fontSize=11.5, textColor=VERDE, spaceBefore=9, spaceAfter=4,
                                keepWithNext=1),
        'normal': ParagraphStyle('normal', parent=base['Normal'], fontSize=9.5, leading=13),
        'rotulo': ParagraphStyle('rotulo', parent=base['Normal'], fontSize=9, leading=12,
                                 textColor=CINZA),
        'codigo': ParagraphStyle('codigo', parent=base['Normal'], fontSize=9, textColor=CINZA,
                                 alignment=TA_RIGHT),
        'aviso': ParagraphStyle('aviso', parent=base['Normal'], fontSize=9, leading=12.5),
        'item': ParagraphStyle('item', parent=base['Normal'], fontSize=9.5, leading=13,
                               leftIndent=8),
        'dia': ParagraphStyle('dia', parent=base['Normal'], fontSize=9.5, leading=13,
                              spaceBefore=6),
    }


def _ficha(linhas, estilos):
    """Tabela de duas colunas: rótulo à esquerda, valor à direita."""
    dados = [[Paragraph(_texto(rotulo), estilos['rotulo']), Paragraph(valor, estilos['normal'])]
             for rotulo, valor in linhas if valor]
    tabela = Table(dados, colWidths=[42 * mm, None])
    tabela.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, -2), 0.4, LINHA),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return tabela


def gerar_pdf(orcamento):
    """Devolve os bytes do PDF do orçamento."""
    destino = orcamento.destino
    agencia = orcamento.agencia
    viagem = montar_viagem(destino, [])
    e = _estilos()
    local = timezone.localtime

    corpo = []
    topo = [Paragraph('Orçamento de viagem', e['titulo']),
            Paragraph(_texto('{} - emitido em {}'.format(
                orcamento.codigo, local(orcamento.criado_em).strftime('%d/%m/%Y às %H:%M'))),
                e['sub'])]
    if LOGO.exists():
        cabecalho = Table([[topo, Image(str(LOGO), width=34 * mm, height=17 * mm,
                                        kind='proportional')]], colWidths=[None, 40 * mm])
        cabecalho.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                       ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                       ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
        corpo.append(cabecalho)
    else:
        corpo += topo

    corpo.append(Paragraph('Viagem', e['secao']))
    preco = orcamento.valor / orcamento.pessoas if orcamento.valor is not None else None
    if orcamento.valor is None:
        valor = 'Sob consulta'
    else:
        valor = '<b>{}</b>'.format(_texto(_reais(orcamento.valor)))
        if orcamento.idades_criancas:
            valor += _texto(' + crianças sob consulta')
    corpo.append(_ficha([
        ('Destino', '<b>{}</b>'.format(_texto(
            ' - '.join(filter(None, [destino.nome, viagem['estado']]))))),
        ('Saída', _texto(orcamento.saida_texto or 'A combinar')),
        ('Duração', _texto('{} / {}'.format(viagem['dias'], viagem['noites']))),
        ('Acomodação', _texto(orcamento.get_acomodacao_display())),
        ('Adultos', _texto(orcamento.pessoas)),
        ('Crianças (CHD)', _texto(orcamento.criancas_texto)),
        ('Preço por adulto', _texto(_reais(preco)) if preco is not None else 'Sob consulta'),
        ('Valor total', valor),
        ('Válido até', '<b>{}</b>'.format(_texto(
            local(orcamento.valido_ate).strftime('%d/%m/%Y às %H:%M')))),
    ], e))

    # o aviso logo abaixo do valor e da validade, onde o cliente olha
    corpo.append(Spacer(1, 10))
    aviso = Table([[[Paragraph('<b>IMPORTANTE:</b> ' + _texto(AVISO[0]), e['aviso']),
                     Spacer(1, 4), Paragraph(_texto(AVISO[1]), e['aviso'])]]])
    aviso.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AVISO_FUNDO),
        ('LINEBEFORE', (0, 0), (0, -1), 3, AVISO_BORDA),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    corpo.append(aviso)

    corpo.append(Paragraph('Cliente', e['secao']))
    corpo.append(_ficha([
        ('Responsável', '<b>{}</b>'.format(_texto(orcamento.cliente_nome))),
        ('E-mail', _texto(orcamento.cliente_email)),
        ('WhatsApp', _texto(orcamento.cliente_telefone)),
    ], e))

    corpo.append(Paragraph('Agência de viagens', e['secao']))
    usuario = agencia.usuario
    corpo.append(_ficha([
        ('Agência', '<b>{}</b>'.format(_texto(agencia.razao_social))),
        ('CNPJ', _texto(agencia.cnpj_formatado)),
        ('Agente', _texto(usuario.get_full_name() or usuario.username)),
        ('E-mail', _texto(usuario.email)),
        ('WhatsApp', _texto(agencia.whatsapp)),
    ], e))

    corpo += _pacote(destino, viagem, e)

    def rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(CINZA)
        canvas.drawString(18 * mm, 9 * mm, _sem_simbolos(
            'Orçamento {} - {} - Soar Operadora'.format(orcamento.codigo, destino.nome)))
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, 'Página {}'.format(doc.page))
        canvas.restoreState()

    saida = BytesIO()
    SimpleDocTemplate(saida, pagesize=A4, title='Orçamento {}'.format(orcamento.codigo),
                      author='Soar Operadora', leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=14 * mm, bottomMargin=16 * mm).build(
        corpo, onFirstPage=rodape, onLaterPages=rodape)
    return saida.getvalue()


def _lista(itens, e):
    return [Paragraph('- ' + _texto(item), e['item']) for item in itens if item]


def _pacote(destino, viagem, e):
    """Tudo o que a página da viagem mostra sobre o pacote, menos fotos e avaliações."""
    partes = [Paragraph('Sobre a viagem', e['secao'])]
    # o subtítulo costuma ser o começo da descrição: não repete
    if viagem['subtitulo'] and not (destino.descricao or '').startswith(viagem['subtitulo']):
        partes.append(Paragraph('<b>{}</b>'.format(_texto(viagem['subtitulo'])), e['normal']))
    if destino.descricao:
        partes += [Spacer(1, 3), Paragraph(_texto(destino.descricao), e['normal'])]
    servicos = ' | '.join('{} {}'.format(s['titulo'], s['sub']) for s in viagem['servicos'])
    if servicos:
        partes += [Spacer(1, 4), Paragraph(_texto(servicos), e['rotulo'])]

    # "E muito mais" é chamada da vitrine, não um destaque de verdade
    destaques = [d for d in viagem['destaques'] if d.strip().lower() != 'e muito mais']
    if destaques:
        partes.append(Paragraph('Destaques da viagem', e['secao']))
        partes += _lista(destaques, e)

    if viagem['roteiro']:
        dias = []
        for dia in viagem['roteiro']:
            bloco = [Paragraph('<b>{}</b>'.format(_texto(dia.get('titulo'))), e['dia'])]
            if dia.get('resumo'):
                bloco.append(Paragraph(_texto(dia['resumo']), e['normal']))
            topicos = dia.get('topicos') or ([dia['detalhe']] if dia.get('detalhe') else [])
            bloco += _lista(topicos, e)
            dias.append(bloco)
        partes += _com_titulo(Paragraph('Roteiro dia a dia', e['secao']), dias)

    if viagem['incluso']:
        partes.append(Paragraph('O pacote inclui', e['secao']))
        partes += _lista(viagem['incluso'], e)
    if viagem['nao_incluso']:
        partes.append(Paragraph('Não incluso', e['secao']))
        partes += _lista(viagem['nao_incluso'], e)

    hospedagem = viagem['hospedagem']
    partes.append(Paragraph('Hospedagem', e['secao']))
    partes.append(Paragraph('<b>{}</b>'.format(_texto(hospedagem['nome'])), e['normal']))
    if hospedagem['sub']:
        partes.append(Paragraph(_texto(hospedagem['sub']), e['normal']))
    comodidades = ', '.join(c['nome'] for c in hospedagem['comodidades'])
    if comodidades:
        partes.append(Paragraph(_texto('Comodidades: ' + comodidades), e['rotulo']))

    if viagem['informacoes']:
        partes.append(Paragraph('Informações importantes', e['secao']))
        partes += _lista(viagem['informacoes'], e)

    if viagem['faq']:
        partes += _com_titulo(Paragraph('Perguntas frequentes', e['secao']), [
            [Paragraph('<b>{}</b>'.format(_texto(item['pergunta'])), e['dia']),
             Paragraph(_texto(item['resposta']), e['normal'])]
            for item in viagem['faq']])
    return partes


def _com_titulo(titulo, blocos):
    """Cada bloco fica inteiro numa página, e o título vai junto com o primeiro.

    O keepWithNext do título não segura um KeepTogether logo depois; sem isto,
    o título podia ficar sozinho no pé da página.
    """
    return [KeepTogether([titulo] + blocos[0])] + [KeepTogether(b) for b in blocos[1:]]
