"""Tipos de quarto e ícones que o dono escolhe no painel.

Os tipos de quarto são fixos (o orçamento da agência e a página da viagem
precisam saber quantas pessoas cabem em cada um); o preço por pessoa e quantos
quartos há em cada data são do dono.
"""

TIPOS = [
    {'chave': 'single', 'nome': 'Single', 'pessoas': '1 pessoa', 'capacidade': 1},
    {'chave': 'casal', 'nome': 'Casal', 'pessoas': '2 pessoas (cama de casal)', 'capacidade': 2},
    {'chave': 'duplo', 'nome': 'Duplo (Twin)', 'pessoas': '2 pessoas (camas separadas)',
     'capacidade': 2},
    {'chave': 'triplo', 'nome': 'Triplo', 'pessoas': '3 pessoas', 'capacidade': 3},
]
POR_CHAVE = {t['chave']: t for t in TIPOS}
ORDEM = {t['chave']: i for i, t in enumerate(TIPOS)}
ESCOLHAS = [(t['chave'], t['nome']) for t in TIPOS]

# Os ícones do sprite (templates/partials/_icones.html) que fazem sentido na
# faixa de serviços da viagem, com o nome que o dono vê no painel.
ICONES = [
    ('ic-onibus', 'Ônibus'),
    ('ic-aviao', 'Avião'),
    ('ic-barco', 'Barco'),
    ('ic-cama', 'Cama'),
    ('ic-hotel', 'Hotel'),
    ('ic-guia', 'Guia'),
    ('ic-grupo', 'Grupo'),
    ('ic-escudo', 'Seguro'),
    ('ic-camera', 'Câmera'),
    ('ic-coracao', 'Coração'),
    ('ic-talheres', 'Refeições'),
    ('ic-cafe', 'Café'),
    ('ic-ticket', 'Ingresso'),
    ('ic-mapa', 'Mapa'),
    ('ic-pin', 'Local'),
    ('ic-mala', 'Mala'),
    ('ic-mochila', 'Mochila'),
    ('ic-sol', 'Sol'),
    ('ic-lua', 'Noite'),
    ('ic-piscina', 'Piscina'),
    ('ic-wifi', 'Wi-Fi'),
    ('ic-ar', 'Ar-condicionado'),
    ('ic-relogio', 'Horário'),
    ('ic-calendario', 'Calendário'),
    ('ic-fone', 'Atendimento'),
    ('ic-estrela-c', 'Estrela'),
    ('ic-check', 'Confirmado'),
]
