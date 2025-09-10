"""
Configuración de la aplicación Content Management
Sistema PubliTrack - Gestión de contenido publicitario
"""

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ContentManagementConfig(AppConfig):
    """Configuración de la aplicación de gestión de contenido"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.content_management'
    verbose_name = 'Gestión de Contenido Publicitario'
    
    def ready(self):
        """
        Código que se ejecuta cuando la aplicación está lista
        """
        # Importar señales para que se registren automáticamente (usando importación relativa)
        try:
            from . import signals
            logger.info("Señales de content_management cargadas correctamente")
        except ImportError as e:
            logger.info(f"Archivo signals.py no encontrado o no se pudo importar: {e}")
        except Exception as e:
            logger.warning(f"Error al cargar señales: {e}")
        
        # Importar tasks de Celery si está disponible (usando importación relativa)
        try:
            from . import tasks
            logger.info("Tasks de Celery cargadas correctamente")
        except ImportError as e:
            logger.info(f"Archivo tasks.py no encontrado o Celery no disponible: {e}")
        except Exception as e:
            logger.warning(f"Error al cargar tasks de Celery: {e}")
        
        # Registrar checks del sistema de forma segura
        try:
            from django.core.checks import register
            from .checks import check_audio_storage_settings
            
            register(check_audio_storage_settings, 'content_management')
            logger.info("Verificaciones del sistema registradas correctamente")
        except ImportError as e:
            logger.info(f"Archivo checks.py no encontrado: {e}")
        except Exception as e:
            logger.warning(f"Error al registrar verificaciones del sistema: {e}")
        
        # Registrar verificaciones adicionales si existen
        try:
            from django.core.checks import register
            from .checks import check_groups_and_permissions
            
            register(check_groups_and_permissions, 'content_management')
            logger.info("Verificaciones de grupos y permisos registradas")
        except (ImportError, AttributeError) as e:
            logger.info(f"Verificaciones adicionales no disponibles: {e}")
        except Exception as e:
            logger.warning(f"Error al registrar verificaciones adicionales: {e}")
        
        logger.info("Configuración de Content Management completada")