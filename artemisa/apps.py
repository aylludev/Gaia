from django.apps import AppConfig


class ArtemisaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'artemisa'

    # Importar las señales aquí para asegurarse de que se registren al iniciar la aplicación
    # Esto asegura que las señales estén listas para escuchar eventos de la base de datos
    def ready(self):
        import artemisa.signals
