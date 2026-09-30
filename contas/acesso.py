"""Quem pode entrar no site.

O site não tem mais conta de cliente (pessoa física): quem reserva é a agência
parceira. Login só para as agências e para a equipe da Soar (o painel do dono).
"""

MENSAGEM_SEM_ACESSO = ('O acesso é exclusivo das agências parceiras e da equipe da Soar. '
                       'Para viajar com a gente, fale com a sua agência de viagens.')


def pode_entrar(usuario):
    return usuario.is_staff or hasattr(usuario, 'agente')
