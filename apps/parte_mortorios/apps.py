from django.apps import AppConfig

class ParteMortoriosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.parte_mortorios'
    verbose_name = 'Parte Mortorios'

    def ready(self):
        import apps.parte_mortorios.signals