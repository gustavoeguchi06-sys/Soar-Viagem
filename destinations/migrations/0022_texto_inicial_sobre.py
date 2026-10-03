"""Texto inicial da página "Sobre a Soar", para ela não estrear vazia.

Só o que já é verdade no próprio site (operadora B2B, viagens em grupo pelo
Brasil, agências parceiras, Soar 60+). Nada de data de fundação nem números:
isso o dono escreve no painel.
"""
from django.db import migrations

HISTORIA = (
    'A Soar Paradiso é uma operadora de turismo especializada em viagens em grupo por '
    'destinos de natureza do Brasil, como Jalapão, Lençóis Maranhenses, Bonito e Serra da '
    'Canastra.\n\n'
    'Trabalhamos ao lado de agências de viagens parceiras: a agência atende o viajante, e a '
    'Soar cuida de toda a viagem, do roteiro dia a dia à hospedagem, ao transporte e aos '
    'passeios, com guias que conhecem cada destino.\n\n'
    'Também temos o Soar 60+, com saídas de ritmo tranquilo para quem quer conhecer o Brasil '
    'com conforto, segurança e companhia.'
)

DIFERENCIAIS = [
    ('ic-mapa', 'Roteiros completos',
     'Transporte, hospedagem e passeios organizados do começo ao fim da viagem.'),
    ('ic-guia', 'Guias que conhecem o destino',
     'Quem acompanha o grupo conhece cada trilha, cachoeira e comunidade do caminho.'),
    ('ic-escudo', 'Segurança em primeiro lugar',
     'Seguro viagem incluso e roteiros ajustados ao clima e ao ritmo do grupo.'),
    ('ic-grupo', 'Atendimento pelas agências parceiras',
     'Você reserva com uma agência de confiança perto de você, com a Soar por trás da viagem.'),
]


def criar(apps, schema_editor):
    PaginaSobre = apps.get_model('destinations', 'PaginaSobre')
    DiferencialSobre = apps.get_model('destinations', 'DiferencialSobre')
    if PaginaSobre.objects.exists():
        return
    pagina = PaginaSobre.objects.create(historia=HISTORIA)
    DiferencialSobre.objects.bulk_create([
        DiferencialSobre(pagina=pagina, icone=icone, titulo=titulo, texto=texto, ordem=i)
        for i, (icone, titulo, texto) in enumerate(DIFERENCIAIS)])


class Migration(migrations.Migration):

    dependencies = [
        ('destinations', '0021_pagina_sobre'),
    ]

    operations = [
        migrations.RunPython(criar, migrations.RunPython.noop),
    ]
