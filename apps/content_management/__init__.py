"""
Módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Gestión integral de cuñas publicitarias y archivos de audio

Este módulo proporciona:
- Gestión de cuñas publicitarias con ciclo de vida completo
- Manejo de archivos de audio con extracción automática de metadatos
- Categorización y tipos de contrato flexibles
- Historial automático de cambios
- Integración con sistemas de notificaciones, finanzas y ventas
"""

default_app_config = 'apps.content_management.apps.ContentManagementConfig'

# Versión del módulo
__version__ = '1.0.0'

# Información del módulo
__author__ = 'PubliTrack Development Team'
__email__ = 'dev@publitrack.com'
__description__ = 'Sistema de gestión de contenido publicitario para radio'

# Exportar modelos principales para facilitar importación
from .models import (
    CategoriaPublicitaria,
    TipoContrato,
    ArchivoAudio,
    CuñaPublicitaria,
    HistorialCuña
)

# Exportar formularios principales
from .forms import (
    CategoriaPublicitariaForm,
    TipoContratoForm,
    ArchivoAudioForm,
    CuñaPublicitariaForm,
    CuñaFiltroForm
)

# Configuración del módulo
MODULE_CONFIG = {
    'name': 'content_management',
    'verbose_name': 'Gestión de Contenido Publicitario',
    'version': __version__,
    'description': __description__,
    'dependencies': [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
    ],
    'optional_dependencies': [
        'apps.notifications',
        'apps.financial_management',
        'apps.sales_management',
        'apps.transmission_control',
        'apps.traffic_light_system',
        'celery',
        'mutagen',
    ]
}

# Estado del módulo
def get_module_status():
    """
    Retorna el estado actual del módulo y sus dependencias
    """
    import importlib
    
    status = {
        'module': 'content_management',
        'version': __version__,
        'loaded': True,
        'dependencies': {},
        'optional_dependencies': {}
    }
    
    # Verificar dependencias requeridas
    for dep in MODULE_CONFIG['dependencies']:
        try:
            importlib.import_module(dep)
            status['dependencies'][dep] = True
        except ImportError:
            status['dependencies'][dep] = False
    
    # Verificar dependencias opcionales
    for dep in MODULE_CONFIG['optional_dependencies']:
        try:
            importlib.import_module(dep)
            status['optional_dependencies'][dep] = True
        except ImportError:
            status['optional_dependencies'][dep] = False
    
    return status