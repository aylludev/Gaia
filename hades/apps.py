from django.apps import AppConfig


class HadesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hades'

    def ready(self):
        """
        Importar signals cuando la aplicación esté lista.

        Este método se ejecuta cuando Django inicializa la aplicación,
        asegurando que los signals se registren correctamente.
        """
        import hades.signals  # noqa: F401
