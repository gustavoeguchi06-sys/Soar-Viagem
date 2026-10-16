"""O que um hotel pode oferecer: a faixa de ícones embaixo da foto da hospedagem.

Cada hospedagem marca as suas no painel (Hospedagens > abrir o hotel). Para
oferecer uma nova, é só acrescentar aqui (e o desenho em partials/_icones.html).
"""

# (chave guardada no banco, nome que aparece, ícone)
ESCOLHAS = [
    ('ar', 'Ar-condicionado', 'ic-ar'),
    ('wifi', 'Wi-Fi', 'ic-wifi'),
    ('piscina', 'Piscina', 'ic-piscina'),
    ('cafe', 'Café da manhã', 'ic-cafe'),
    ('restaurante', 'Restaurante', 'ic-talheres'),
    ('estacionamento', 'Estacionamento', 'ic-estacionamento'),
    ('tv', 'TV no quarto', 'ic-tv'),
    ('frigobar', 'Frigobar', 'ic-frigobar'),
    ('recepcao', 'Recepção 24h', 'ic-relogio'),
    ('academia', 'Academia', 'ic-academia'),
    ('acessivel', 'Acessibilidade', 'ic-acessivel'),
    ('natureza', 'Junto à natureza', 'ic-folha'),
]

POR_CHAVE = {chave: {'nome': nome, 'icone': icone} for chave, nome, icone in ESCOLHAS}

# o que a página mostrava para todo hotel antes de cada um escolher as suas
ANTIGAS = ['ar', 'wifi', 'piscina', 'cafe']


def da_hospedagem(chaves):
    """[{'nome', 'icone'}] na ordem do catálogo, ignorando chave que saiu dele."""
    marcadas = set(chaves or [])
    return [POR_CHAVE[c] for c, _, _ in ESCOLHAS if c in marcadas]
