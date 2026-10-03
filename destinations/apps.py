from django.apps import AppConfig


class DestinationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'destinations'
    verbose_name = 'Destinos e pacotes'

    def ready(self):
        # foto/vídeo trocado ou registro apagado: o arquivo sem uso sai do disco/R2
        from soar.arquivos import conectar
        conectar()
