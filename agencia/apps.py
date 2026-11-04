from django.apps import AppConfig

# Guarda na sessão qual aviso o agente já fechou no X (ver
# agencia/context_processors.py). Um login novo é uma sessão nova: o pop-up
# volta a aparecer.
AVISO_FECHADO = 'aviso_agente_fechado'


class AgenciaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agencia'
    verbose_name = 'Agências parceiras'
