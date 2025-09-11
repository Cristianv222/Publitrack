# apps/context_processors.py
from django.conf import settings

def pwa_context(request):
    """
    Agrega configuración PWA al contexto de todos los templates
    """
    return {
        'PWA_APP_NAME': getattr(settings, 'PWA_APP_NAME', 'PublicTrack'),
        'PWA_APP_THEME_COLOR': getattr(settings, 'PWA_APP_THEME_COLOR', '#1976d2'),
        'PWA_APP_DESCRIPTION': getattr(settings, 'PWA_APP_DESCRIPTION', 'Sistema de gestión radial'),
    }