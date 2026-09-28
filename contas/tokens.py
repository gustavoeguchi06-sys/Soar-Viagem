"""Token do link de confirmação de e-mail.

Antes a confirmação usava o `default_token_generator`, o mesmo da troca de
senha. Resultado: o link do e-mail de confirmação também abria a tela de
"nova senha" (/senha/nova/<uid>/<token>/) e trocava a senha da conta, por até
24 horas ou até o primeiro login. Quem pegasse aquele e-mail (encaminhado, ou
aberto pelo antivírus de um e-mail corporativo) tomava a conta.

Aqui o token tem outro `key_salt`, então um não serve no lugar do outro, e
leva `is_active` no hash: depois que a conta é ativada, o link morre.
"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AtivacaoTokenGenerator(PasswordResetTokenGenerator):
    key_salt = 'contas.tokens.AtivacaoTokenGenerator'

    def _make_hash_value(self, user, timestamp):
        return '{}{}'.format(super()._make_hash_value(user, timestamp), user.is_active)


token_ativacao = AtivacaoTokenGenerator()
