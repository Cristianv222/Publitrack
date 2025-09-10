"""
Configuración de la aplicación Control de Transmisiones
Sistema PubliTrack - Gestión y programación de transmisiones de publicidad radial
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TransmissionControlConfig(AppConfig):
    """
    Configuración de la aplicación de Control de Transmisiones
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.transmission_control'
    verbose_name = _('Control de Transmisiones')
    
    def ready(self):
        """
        Código que se ejecuta cuando la aplicación está lista
        """
        # Importar señales para que se registren
        try:
            from . import signals
            signals.conectar_señales()
        except ImportError:
            pass
        
        # Inicializar sistema de transmisiones
        try:
            from .signals import inicializar_sistema_transmision
            inicializar_sistema_transmision()
        except Exception as e:
            # Log del error pero no fallar la aplicación
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error inicializando sistema de transmisiones: {e}")
        
        # Registrar tareas de Celery si está disponible
        try:
            from . import tasks
        except ImportError:
            pass
        
        # Configurar cache predeterminado para transmisiones
        try:
            from django.core.cache import cache
            from django.conf import settings
            
            # Verificar que el cache esté configurado
            if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
                # Limpiar cache al iniciar
                cache.delete_many([
                    'configuracion_transmision_activa',
                    'transmision_actual',
                    'proximas_transmisiones',
                    'estadisticas_tiempo_real'
                ])
        except Exception:
            pass