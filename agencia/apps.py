from django.apps import AppConfig

# Marca na sessão que o agente aprovado acabou de entrar. O pop-up de aviso vai
# na próxima página que ele abrir, e a marca só sai quando o pop-up chega de
# fato na tela (agencia/middleware.py): um pedido do navegador que não mostra
# nada (ícone do site, imagem que não existe) não gasta o aviso.
AVISO_PENDENTE = 'aviso_agente_pendente'


def marcar_aviso_no_login(sender, request, user, **kwargs):
    agencia = getattr(user, 'agente', None)
    if request is not None and agencia is not None and agencia.aprovado:
        request.session[AVISO_PENDENTE] = True


class AgenciaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agencia'
    verbose_name = 'Agências parceiras'

    def ready(self):
        from django.contrib.auth import signals

        signals.user_logged_in.connect(marcar_aviso_no_login, dispatch_uid='soar_aviso_agente')
