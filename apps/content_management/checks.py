"""
Verificaciones del sistema para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Checks personalizados de Django
"""

import os
from django.core.checks import Error, Warning, Info, register, Tags
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# ==================== CHECKS DE CONFIGURACIÓN ====================

@register(Tags.compatibility)
def check_audio_storage_settings(app_configs, **kwargs):
    """
    Verifica la configuración de almacenamiento de archivos de audio
    """
    errors = []
    
    # Verificar MEDIA_ROOT
    if not hasattr(settings, 'MEDIA_ROOT') or not settings.MEDIA_ROOT:
        errors.append(
            Error(
                'MEDIA_ROOT no está configurado',
                hint='Agrega MEDIA_ROOT = os.path.join(BASE_DIR, "media") en settings.py',
                id='content_management.E001',
            )
        )
    elif not os.path.exists(settings.MEDIA_ROOT):
        errors.append(
            Warning(
                f'El directorio MEDIA_ROOT no existe: {settings.MEDIA_ROOT}',
                hint='Crea el directorio o ajusta la configuración',
                id='content_management.W001',
            )
        )
    elif not os.access(settings.MEDIA_ROOT, os.W_OK):
        errors.append(
            Error(
                f'No hay permisos de escritura en MEDIA_ROOT: {settings.MEDIA_ROOT}',
                hint='Verifica los permisos del directorio',
                id='content_management.E002',
            )
        )
    
    # Verificar MEDIA_URL
    if not hasattr(settings, 'MEDIA_URL') or not settings.MEDIA_URL:
        errors.append(
            Warning(
                'MEDIA_URL no está configurado',
                hint='Agrega MEDIA_URL = "/media/" en settings.py',
                id='content_management.W002',
            )
        )
    
    # Verificar directorio específico de audio
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio_spots')
        if not os.path.exists(audio_dir):
            try:
                os.makedirs(audio_dir, exist_ok=True)
                errors.append(
                    Info(
                        f'Directorio de audio creado: {audio_dir}',
                        id='content_management.I001',
                    )
                )
            except OSError:
                errors.append(
                    Warning(
                        f'No se pudo crear el directorio de audio: {audio_dir}',
                        hint='Crea el directorio manualmente o verifica permisos',
                        id='content_management.W003',
                    )
                )
    
    return errors

@register(Tags.compatibility)
def check_mutagen_library(app_configs, **kwargs):
    """
    Verifica que la librería mutagen esté disponible para procesar audio
    """
    errors = []
    
    try:
        import mutagen
        from mutagen.mp3 import MP3
        from mutagen.wave import WAVE
    except ImportError:
        errors.append(
            Error(
                'La librería mutagen no está instalada',
                hint='Instala mutagen con: pip install mutagen',
                id='content_management.E003',
            )
        )
    
    return errors

@register(Tags.security)
def check_file_upload_settings(app_configs, **kwargs):
    """
    Verifica configuraciones de seguridad para subida de archivos
    """
    errors = []
    
    # Verificar FILE_UPLOAD_MAX_MEMORY_SIZE
    max_memory = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440)  # 2.5MB por defecto
    if max_memory > 52428800:  # 50MB
        errors.append(
            Warning(
                f'FILE_UPLOAD_MAX_MEMORY_SIZE es muy alto: {max_memory} bytes',
                hint='Considera reducir el tamaño para evitar problemas de memoria',
                id='content_management.W004',
            )
        )
    
    # Verificar DATA_UPLOAD_MAX_MEMORY_SIZE
    max_data = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 2621440)
    if max_data > 104857600:  # 100MB
        errors.append(
            Warning(
                f'DATA_UPLOAD_MAX_MEMORY_SIZE es muy alto: {max_data} bytes',
                hint='Considera reducir el tamaño para evitar problemas de memoria',
                id='content_management.W005',
            )
        )
    
    # Verificar que ALLOWED_HOSTS esté configurado en producción
    if not settings.DEBUG and not settings.ALLOWED_HOSTS:
        errors.append(
            Warning(
                'ALLOWED_HOSTS está vacío en producción',
                hint='Configura ALLOWED_HOSTS para mayor seguridad',
                id='content_management.W006',
            )
        )
    
    return errors

# ==================== CHECKS DE BASE DE DATOS ====================

@register(Tags.database)
def check_content_management_data(app_configs, **kwargs):
    """
    Verifica la integridad de datos del módulo
    """
    errors = []
    
    try:
        from .models import CuñaPublicitaria, ArchivoAudio, CategoriaPublicitaria
        
        # Verificar cuñas sin categoría
        cuñas_sin_categoria = CuñaPublicitaria.objects.filter(categoria__isnull=True).count()
        if cuñas_sin_categoria > 0:
            errors.append(
                Warning(
                    f'{cuñas_sin_categoria} cuñas sin categoría asignada',
                    hint='Asigna categorías a todas las cuñas para mejor organización',
                    id='content_management.W007',
                )
            )
        
        # Verificar cuñas sin vendedor
        cuñas_sin_vendedor = CuñaPublicitaria.objects.filter(vendedor_asignado__isnull=True).count()
        if cuñas_sin_vendedor > 0:
            errors.append(
                Warning(
                    f'{cuñas_sin_vendedor} cuñas sin vendedor asignado',
                    hint='Asigna vendedores a todas las cuñas',
                    id='content_management.W008',
                )
            )
        
        # Verificar archivos de audio sin archivo físico
        from django.db.models import Q
        archivos_huerfanos = 0
        for archivo in ArchivoAudio.objects.all():
            if not archivo.archivo or not os.path.exists(archivo.archivo.path):
                archivos_huerfanos += 1
        
        if archivos_huerfanos > 0:
            errors.append(
                Warning(
                    f'{archivos_huerfanos} archivos de audio sin archivo físico',
                    hint='Ejecuta la tarea de limpieza de archivos huérfanos',
                    id='content_management.W009',
                )
            )
        
        # Verificar cuñas con fechas inconsistentes
        cuñas_fechas_malas = CuñaPublicitaria.objects.filter(
            fecha_fin__lte=models.F('fecha_inicio')
        ).count()
        
        if cuñas_fechas_malas > 0:
            errors.append(
                Error(
                    f'{cuñas_fechas_malas} cuñas con fechas de fin anteriores a fecha de inicio',
                    hint='Corrige las fechas en estas cuñas',
                    id='content_management.E004',
                )
            )
        
    except Exception as e:
        errors.append(
            Error(
                f'Error verificando datos del módulo: {str(e)}',
                hint='Verifica que las migraciones estén aplicadas correctamente',
                id='content_management.E005',
            )
        )
    
    return errors

# ==================== CHECKS DE RENDIMIENTO ====================

@register(Tags.database)
def check_database_indexes(app_configs, **kwargs):
    """
    Verifica que los índices de base de datos estén optimizados
    """
    errors = []
    
    try:
        from django.db import connection
        from .models import CuñaPublicitaria
        
        # Verificar si hay muchas cuñas sin índices apropiados
        total_cuñas = CuñaPublicitaria.objects.count()
        
        if total_cuñas > 10000:
            errors.append(
                Info(
                    f'Base de datos tiene {total_cuñas} cuñas',
                    hint='Considera agregar índices adicionales para mejor rendimiento',
                    id='content_management.I002',
                )
            )
        
        # Verificar índices específicos según la base de datos
        if 'postgresql' in settings.DATABASES['default']['ENGINE']:
            with connection.cursor() as cursor:
                # Verificar índices en PostgreSQL
                cursor.execute("""
                    SELECT schemaname, tablename, indexname 
                    FROM pg_indexes 
                    WHERE tablename LIKE 'content_management_%'
                """)
                indices = cursor.fetchall()
                
                if len(indices) < 5:  # Debería haber al menos 5 índices
                    errors.append(
                        Warning(
                            'Pocos índices encontrados en las tablas del módulo',
                            hint='Verifica que las migraciones de índices estén aplicadas',
                            id='content_management.W010',
                        )
                    )
        
    except Exception as e:
        errors.append(
            Warning(
                f'No se pudo verificar índices de base de datos: {str(e)}',
                hint='Esto es normal si no tienes acceso a metadatos de la DB',
                id='content_management.W011',
            )
        )
    
    return errors

# ==================== CHECKS DE INTEGRACIONES ====================

@register(Tags.compatibility)
def check_module_integrations(app_configs, **kwargs):
    """
    Verifica la disponibilidad de otros módulos del sistema
    """
    errors = []
    
    # Verificar módulo de notificaciones
    try:
        import apps.notifications
    except ImportError:
        errors.append(
            Info(
                'Módulo de notificaciones no disponible',
                hint='Las notificaciones automáticas no funcionarán hasta que se instale',
                id='content_management.I003',
            )
        )
    
    # Verificar módulo financiero
    try:
        import apps.financial_management
    except ImportError:
        errors.append(
            Info(
                'Módulo financiero no disponible',
                hint='Las cuentas por cobrar automáticas no funcionarán',
                id='content_management.I004',
            )
        )
    
    # Verificar módulo de ventas
    try:
        import apps.sales_management
    except ImportError:
        errors.append(
            Info(
                'Módulo de ventas no disponible',
                hint='Las comisiones automáticas no funcionarán',
                id='content_management.I005',
            )
        )
    
    # Verificar módulo de transmisión
    try:
        import apps.transmission_control
    except ImportError:
        errors.append(
            Info(
                'Módulo de transmisión no disponible',
                hint='La programación automática de transmisiones no funcionará',
                id='content_management.I006',
            )
        )
    
    # Verificar Celery para tareas asíncronas
    try:
        import celery
        from django.conf import settings
        
        if not hasattr(settings, 'CELERY_BROKER_URL'):
            errors.append(
                Warning(
                    'Celery no configurado',
                    hint='Las tareas en background no funcionarán sin Celery',
                    id='content_management.W012',
                )
            )
    except ImportError:
        errors.append(
            Info(
                'Celery no instalado',
                hint='Las tareas asíncronas no estarán disponibles',
                id='content_management.I007',
            )
        )
    
    return errors

# ==================== CHECKS DE GRUPOS Y PERMISOS ====================

@register(Tags.security)
def check_user_groups_and_permissions(app_configs, **kwargs):
    """
    Verifica que los grupos de usuarios y permisos estén configurados
    """
    errors = []
    
    try:
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Grupos requeridos
        grupos_requeridos = ['Administradores', 'Vendedores', 'Clientes', 'Supervisores', 'Operadores']
        
        for grupo_nombre in grupos_requeridos:
            try:
                Group.objects.get(name=grupo_nombre)
            except Group.DoesNotExist:
                errors.append(
                    Warning(
                        f'Grupo "{grupo_nombre}" no existe',
                        hint=f'Crea el grupo {grupo_nombre} en el admin de Django',
                        id='content_management.W013',
                    )
                )
        
        # Verificar permisos específicos del módulo
        content_type = ContentType.objects.get_for_model('content_management', 'cuñapublicitaria')
        permisos_importantes = ['add_cuñapublicitaria', 'change_cuñapublicitaria', 'view_cuñapublicitaria']
        
        for permiso_code in permisos_importantes:
            try:
                Permission.objects.get(content_type=content_type, codename=permiso_code)
            except Permission.DoesNotExist:
                errors.append(
                    Error(
                        f'Permiso "{permiso_code}" no existe',
                        hint='Ejecuta las migraciones para crear los permisos automáticamente',
                        id='content_management.E006',
                    )
                )
        
    except Exception as e:
        errors.append(
            Warning(
                f'Error verificando grupos y permisos: {str(e)}',
                hint='Verifica que las migraciones de auth estén aplicadas',
                id='content_management.W014',
            )
        )
    
    return errors

# ==================== FUNCIÓN PRINCIPAL DE VERIFICACIÓN ====================

def run_all_checks():
    """
    Ejecuta todos los checks del módulo y retorna un resumen
    """
    from django.core.management.base import BaseCommand
    from django.core.checks import run_checks
    
    # Ejecutar checks específicos del módulo
    issues = run_checks(
        app_configs=None,
        tags=['content_management'],
        include_deployment_checks=False
    )
    
    # Categorizar issues
    errors = [issue for issue in issues if issue.level >= 40]  # ERROR
    warnings = [issue for issue in issues if 30 <= issue.level < 40]  # WARNING
    infos = [issue for issue in issues if issue.level < 30]  # INFO
    
    return {
        'total_issues': len(issues),
        'errors': len(errors),
        'warnings': len(warnings),
        'infos': len(infos),
        'details': {
            'errors': [str(e) for e in errors],
            'warnings': [str(w) for w in warnings],
            'infos': [str(i) for i in infos],
        }
    }