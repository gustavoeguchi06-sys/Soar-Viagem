from django.apps import AppConfig


class ContasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contas'
    verbose_name = 'Contas de viajante'

    def ready(self):
        """Liga o registro de entradas e tentativas falhas.

        É aqui e não na view porque o admin em /painel/ tem tela de login
        própria: o sinal pega os dois caminhos de uma vez.
        """
        from django.contrib.auth import signals

        from soar.seguranca import registrar_login_falho, registrar_login_ok

        signals.user_login_failed.connect(
            registrar_login_falho, dispatch_uid='soar_login_falho')
        signals.user_logged_in.connect(
            registrar_login_ok, dispatch_uid='soar_login_ok')
