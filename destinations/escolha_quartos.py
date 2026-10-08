"""Escolha de quartos no card da viagem: quantos quartos e quantas pessoas de cada tipo.

Usada pelo orçamento da agência (agencia.forms.OrcamentoViagemForm) e pelo
"Saiba mais" do visitante (destinations.forms.InteresseForm). Para cada tipo
de quarto da viagem há os campos quartos_<tipo> e pessoas_<tipo> (o Single
não tem pessoas: é 1 por quarto). Dá para escolher vários tipos e vários
quartos de cada um; cada quarto leva de 1 pessoa até a lotação dele (Duplo
até 2, Triplo até 3), nunca mais. Os botões − e + e o total da tela são do
static/js/viagem.js.

O resultado fica em `quartos_escolhidos`:
[{"tipo": "duplo", "quartos": 2, "pessoas": 3, "preco": "3588.00"}, ...]
(preco é o preço por pessoa do tipo, ou None quando é sob consulta).
"""
from django import forms

MAX_ADULTOS = 60


class EscolhaDeQuartos:
    """Mistura para um Form: chame `criar_campos_de_quartos` no __init__ e
    `conferir_quartos` no clean."""

    def criar_campos_de_quartos(self, destino, iniciais=None):
        from .conteudo import _acomodacoes
        self._acomodacoes = _acomodacoes(destino)
        self.quartos_escolhidos = []
        # só para mostrar o erro do conjunto ("escolha pelo menos um quarto") embaixo dos quartos
        self.fields['escolha_quartos'] = forms.CharField(required=False, widget=forms.HiddenInput)
        # iniciais: a escolha que já existe (ex.: a do visitante, no orçamento da agência)
        marcados = {q['tipo']: q for q in iniciais or []}
        for a in self._acomodacoes:
            if a.get('sem_quarto'):
                # bate-volta: só quantas pessoas
                pessoas = marcados.get(a['chave'], {}).get('pessoas', 0) if marcados else \
                    (1 if a['padrao'] else 0)
                self.fields['pessoas_' + a['chave']] = forms.IntegerField(
                    label='Pessoas', required=False, min_value=0, max_value=MAX_ADULTOS,
                    initial=pessoas,
                    widget=forms.NumberInput(attrs={'min': 0, 'max': MAX_ADULTOS,
                                                    'inputmode': 'numeric'}))
                continue
            if marcados:
                q = marcados.get(a['chave'], {})
                um_quarto, pessoas = q.get('quartos', 0), q.get('pessoas', 0)
            else:
                # sem nada escolhido ainda, já vem 1 quarto do tipo padrão (casal), lotado
                um_quarto = 1 if a['padrao'] else 0
                pessoas = um_quarto * a['capacidade']
            self.fields['quartos_' + a['chave']] = forms.IntegerField(
                label='Quartos', required=False, min_value=0, max_value=MAX_ADULTOS,
                initial=um_quarto,
                widget=forms.NumberInput(attrs={'min': 0, 'max': MAX_ADULTOS,
                                                'inputmode': 'numeric'}))
            if a['capacidade'] > 1:
                self.fields['pessoas_' + a['chave']] = forms.IntegerField(
                    label='Pessoas', required=False, min_value=0, max_value=MAX_ADULTOS,
                    initial=pessoas,
                    widget=forms.NumberInput(attrs={'min': 0, 'max': MAX_ADULTOS,
                                                    'inputmode': 'numeric'}))

    @property
    def quartos_campos(self):
        """Uma linha por tipo de quarto da viagem, com os campos de quartos e pessoas."""
        return [{'a': a,
                 'quartos': None if a.get('sem_quarto') else self['quartos_' + a['chave']],
                 'pessoas': self['pessoas_' + a['chave']]
                 if a.get('sem_quarto') or a['capacidade'] > 1 else None}
                for a in self._acomodacoes]

    def conferir_quartos(self, dados, saida=None, obrigatorio=True):
        """Confere a escolha (lotação, quartos da data) e guarda em `quartos_escolhidos`.

        obrigatorio=False: pode não escolher nenhum quarto (o visitante que só
        quer informação).
        """
        escolhidos = []
        for a in self._acomodacoes:
            chave, lotacao, nome = a['chave'], a['capacidade'], a['nome']
            preco = str(a['valor']) if a['valor'] is not None else None
            if a.get('sem_quarto'):
                pessoas = dados.get('pessoas_' + chave) or 0
                if pessoas:
                    escolhidos.append({'tipo': chave, 'quartos': 0, 'pessoas': pessoas,
                                       'preco': preco})
                continue
            quartos = dados.get('quartos_' + chave) or 0
            # Single: uma pessoa por quarto, sem campo de pessoas
            pessoas = (dados.get('pessoas_' + chave) or 0) if lotacao > 1 else quartos
            if not quartos:
                if pessoas:
                    self.add_error('pessoas_' + chave, 'Escolha quantos quartos antes das pessoas.')
                continue
            # o tipo que o dono marcou com 0 nesta data acabou; com número, é o limite
            disponiveis = getattr(saida, 'quartos_' + chave, None) if saida else None
            if disponiveis == 0:
                self.add_error('quartos_' + chave, 'Esse quarto está esgotado nesta data.')
            elif disponiveis is not None and quartos > disponiveis:
                self.add_error('quartos_' + chave, 'Nesta data há só {} quarto{} {}.'.format(
                    disponiveis, 's' if disponiveis != 1 else '', nome))
            if pessoas < quartos:
                self.add_error('pessoas_' + chave, 'Cada quarto precisa de pelo menos 1 pessoa: '
                               'com {0} quartos, no mínimo {0} pessoas.'.format(quartos))
            elif pessoas > quartos * lotacao:
                self.add_error('pessoas_' + chave, 'O {} leva até {} pessoas por quarto: com {} '
                               'quarto{}, no máximo {}.'.format(
                                   nome, lotacao, quartos, 's' if quartos != 1 else '',
                                   quartos * lotacao))
            escolhidos.append({'tipo': chave, 'quartos': quartos, 'pessoas': pessoas,
                               'preco': str(a['valor']) if a['valor'] is not None else None})

        if not escolhidos:
            if obrigatorio:
                self.add_error('escolha_quartos', 'Escolha pelo menos um quarto.')
        elif sum(q['pessoas'] for q in escolhidos) > MAX_ADULTOS:
            self.add_error('escolha_quartos',
                           'No máximo {} adultos por pedido.'.format(MAX_ADULTOS))
        else:
            self.quartos_escolhidos = escolhidos


def texto_dos_quartos(quartos):
    """[{"tipo": "duplo", "quartos": 2, "pessoas": 3}] -> '2 quartos Duplo (Twin), 3 pessoas'

    Bate-volta (sem quarto): 'Bate-volta (1 dia), 3 pessoas'.
    """
    from .quartos import POR_CHAVE
    partes = []
    for q in quartos or []:
        tipo = POR_CHAVE.get(q.get('tipo'))
        if tipo is None:
            continue
        if tipo.get('sem_quarto'):
            partes.append('{}, {} pessoa{}'.format(tipo['nome'], q['pessoas'],
                                                   's' if q['pessoas'] != 1 else ''))
            continue
        partes.append('{} quarto{} {}, {} pessoa{}'.format(
            q['quartos'], 's' if q['quartos'] != 1 else '', tipo['nome'],
            q['pessoas'], 's' if q['pessoas'] != 1 else ''))
    return '; '.join(partes)
