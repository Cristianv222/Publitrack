"""
Tareas asíncronas para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Tareas de Celery para procesamiento en background
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta, date
from decimal import Decimal
import os
import logging

logger = logging.getLogger(__name__)

# ==================== TAREAS DE NOTIFICACIONES ====================

@shared_task(bind=True, max_retries=3)
def verificar_cuñas_por_vencer(self):
    """
    Tarea periódica para verificar cuñas próximas a vencer
    Se ejecuta diariamente
    """
    try:
        from .models import CuñaPublicitaria
        from apps.notifications.models import crear_notificacion_vencimiento_cuña
        
        hoy = timezone.now().date()
        
        # Buscar cuñas activas que requieren notificación
        cuñas_por_vencer = CuñaPublicitaria.objects.filter(
            estado__in=['activa', 'aprobada'],
            notificar_vencimiento=True,
            fecha_fin__gt=hoy
        )
        
        notificaciones_enviadas = 0
        
        for cuña in cuñas_por_vencer:
            dias_restantes = (cuña.fecha_fin - hoy).days
            
            # Verificar si debe enviar notificación
            if dias_restantes <= cuña.dias_aviso_vencimiento:
                try:
                    crear_notificacion_vencimiento_cuña(cuña)
                    notificaciones_enviadas += 1
                except Exception as e:
                    logger.error(f"Error enviando notificación para cuña {cuña.codigo}: {e}")
        
        logger.info(f"Verificación de vencimientos completada. {notificaciones_enviadas} notificaciones enviadas.")
        return f"Procesadas {cuñas_por_vencer.count()} cuñas, {notificaciones_enviadas} notificaciones enviadas"
        
    except Exception as exc:
        logger.error(f"Error en verificar_cuñas_por_vencer: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def finalizar_cuñas_vencidas(self):
    """
    Tarea para finalizar automáticamente cuñas vencidas
    Se ejecuta diariamente
    """
    try:
        from .models import CuñaPublicitaria, HistorialCuña
        
        hoy = timezone.now().date()
        
        # Buscar cuñas activas que ya vencieron
        cuñas_vencidas = CuñaPublicitaria.objects.filter(
            estado='activa',
            fecha_fin__lt=hoy
        )
        
        cuñas_finalizadas = 0
        
        for cuña in cuñas_vencidas:
            try:
                cuña.finalizar()
                
                # Crear entrada en historial
                HistorialCuña.objects.create(
                    cuña=cuña,
                    accion='finalizada',
                    usuario=None,  # Sistema automático
                    descripcion=f'Cuña finalizada automáticamente por vencimiento el {hoy}'
                )
                
                cuñas_finalizadas += 1
                
            except Exception as e:
                logger.error(f"Error finalizando cuña {cuña.codigo}: {e}")
        
        logger.info(f"Finalización automática completada. {cuñas_finalizadas} cuñas finalizadas.")
        return f"Finalizadas {cuñas_finalizadas} cuñas vencidas"
        
    except Exception as exc:
        logger.error(f"Error en finalizar_cuñas_vencidas: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True)
def enviar_resumen_diario_vendedores(self):
    """
    Envía resumen diario a vendedores con sus cuñas activas
    """
    try:
        from django.contrib.auth import get_user_model
        from .models import CuñaPublicitaria
        from django.template.loader import render_to_string
        from django.core.mail import send_mail
        
        User = get_user_model()
        hoy = timezone.now().date()
        
        vendedores = User.objects.filter(groups__name='Vendedores', is_active=True)
        emails_enviados = 0
        
        for vendedor in vendedores:
            # Obtener estadísticas del vendedor
            cuñas_activas = CuñaPublicitaria.objects.filter(
                vendedor_asignado=vendedor,
                estado='activa'
            ).count()
            
            cuñas_por_vencer = CuñaPublicitaria.objects.filter(
                vendedor_asignado=vendedor,
                estado='activa',
                fecha_fin__lte=hoy + timedelta(days=7)
            )
            
            cuñas_pendientes = CuñaPublicitaria.objects.filter(
                vendedor_asignado=vendedor,
                estado='pendiente_revision'
            ).count()
            
            # Solo enviar si hay información relevante
            if cuñas_activas > 0 or cuñas_pendientes > 0 or cuñas_por_vencer.exists():
                context = {
                    'vendedor': vendedor,
                    'fecha': hoy,
                    'cuñas_activas': cuñas_activas,
                    'cuñas_pendientes': cuñas_pendientes,
                    'cuñas_por_vencer': cuñas_por_vencer,
                }
                
                try:
                    # Renderizar email
                    subject = f'PubliTrack - Resumen diario {hoy.strftime("%d/%m/%Y")}'
                    message = render_to_string('content/emails/resumen_diario_vendedor.html', context)
                    
                    send_mail(
                        subject=subject,
                        message='',
                        html_message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[vendedor.email],
                        fail_silently=False
                    )
                    
                    emails_enviados += 1
                    
                except Exception as e:
                    logger.error(f"Error enviando resumen a {vendedor.email}: {e}")
        
        return f"Resúmenes enviados a {emails_enviados} vendedores"
        
    except Exception as exc:
        logger.error(f"Error en enviar_resumen_diario_vendedores: {exc}")
        raise self.retry(exc=exc, countdown=300)

# ==================== TAREAS DE PROCESAMIENTO DE ARCHIVOS ====================

@shared_task(bind=True, max_retries=2)
def procesar_metadatos_audio(self, archivo_id):
    """
    Procesa metadatos de archivo de audio en background
    """
    try:
        from .models import ArchivoAudio
        
        archivo = ArchivoAudio.objects.get(id=archivo_id)
        
        if archivo.archivo and not archivo.duracion_segundos:
            archivo.extraer_metadatos()
            logger.info(f"Metadatos procesados para archivo {archivo.nombre_original}")
            
        return f"Metadatos procesados para {archivo.nombre_original}"
        
    except ArchivoAudio.DoesNotExist:
        logger.error(f"Archivo con ID {archivo_id} no encontrado")
        return f"Archivo {archivo_id} no encontrado"
        
    except Exception as exc:
        logger.error(f"Error procesando metadatos del archivo {archivo_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True)
def limpiar_archivos_temporales(self):
    """
    Limpia archivos temporales y huérfanos del sistema
    """
    try:
        from .signals import limpiar_archivos_huerfanos, validar_integridad_archivos
        
        # Validar integridad de archivos
        archivos_problema = validar_integridad_archivos()
        
        # Limpiar archivos huérfanos
        resultado_limpieza = limpiar_archivos_huerfanos()
        
        logger.info(f"Limpieza completada. Archivos eliminados: {resultado_limpieza.get('eliminados', 0)}")
        
        return {
            'archivos_problema': len(archivos_problema),
            'archivos_eliminados': resultado_limpieza.get('eliminados', 0),
            'archivos_conservados': resultado_limpieza.get('conservados', 0)
        }
        
    except Exception as exc:
        logger.error(f"Error en limpiar_archivos_temporales: {exc}")
        raise self.retry(exc=exc, countdown=300)

@shared_task(bind=True)
def generar_hash_archivos_faltantes(self):
    """
    Genera hashes para archivos que no los tienen
    """
    try:
        from .signals import regenerar_hashes_archivos
        
        resultado = regenerar_hashes_archivos()
        
        logger.info(f"Hashes generados: {resultado['procesados']}, Errores: {len(resultado['errores'])}")
        
        return resultado
        
    except Exception as exc:
        logger.error(f"Error en generar_hash_archivos_faltantes: {exc}")
        raise self.retry(exc=exc, countdown=60)

# ==================== TAREAS DE REPORTES ====================

@shared_task(bind=True)
def generar_reporte_mensual_cuñas(self, año, mes):
    """
    Genera reporte mensual de cuñas publicitarias
    """
    try:
        from .models import CuñaPublicitaria
        from django.db.models import Count, Sum, Avg
        from datetime import date
        import json
        
        inicio_mes = date(año, mes, 1)
        if mes == 12:
            fin_mes = date(año + 1, 1, 1) - timedelta(days=1)
        else:
            fin_mes = date(año, mes + 1, 1) - timedelta(days=1)
        
        # Estadísticas del mes
        cuñas_mes = CuñaPublicitaria.objects.filter(
            created_at__date__range=[inicio_mes, fin_mes]
        )
        
        estadisticas = {
            'periodo': f"{año}-{mes:02d}",
            'total_cuñas': cuñas_mes.count(),
            'cuñas_por_estado': dict(cuñas_mes.values('estado').annotate(count=Count('id')).values_list('estado', 'count')),
            'ingresos_totales': cuñas_mes.aggregate(total=Sum('precio_total'))['total'] or 0,
            'duracion_promedio': cuñas_mes.aggregate(promedio=Avg('duracion_planeada'))['promedio'] or 0,
            'precio_promedio': cuñas_mes.aggregate(promedio=Avg('precio_total'))['promedio'] or 0,
        }
        
        # Estadísticas por vendedor
        stats_vendedores = cuñas_mes.values(
            'vendedor_asignado__first_name',
            'vendedor_asignado__last_name'
        ).annotate(
            count=Count('id'),
            ingresos=Sum('precio_total')
        ).order_by('-count')
        
        estadisticas['vendedores'] = list(stats_vendedores)
        
        # Estadísticas por categoría
        stats_categorias = cuñas_mes.values(
            'categoria__nombre'
        ).annotate(
            count=Count('id'),
            ingresos=Sum('precio_total')
        ).order_by('-count')
        
        estadisticas['categorias'] = list(stats_categorias)
        
        logger.info(f"Reporte mensual generado para {año}-{mes:02d}")
        
        # Aquí podrías guardar el reporte en un modelo o enviarlo por email
        return estadisticas
        
    except Exception as exc:
        logger.error(f"Error generando reporte mensual: {exc}")
        raise self.retry(exc=exc, countdown=300)

@shared_task(bind=True)
def actualizar_estadisticas_dashboard(self):
    """
    Actualiza estadísticas del dashboard en cache
    """
    try:
        from django.core.cache import cache
        from .models import CuñaPublicitaria, ArchivoAudio, CategoriaPublicitaria
        from django.db.models import Count, Sum
        
        hoy = timezone.now().date()
        
        # Calcular estadísticas
        stats = {
            'total_cuñas': CuñaPublicitaria.objects.count(),
            'cuñas_activas': CuñaPublicitaria.objects.filter(estado='activa').count(),
            'cuñas_pendientes': CuñaPublicitaria.objects.filter(estado='pendiente_revision').count(),
            'cuñas_por_vencer_7d': CuñaPublicitaria.objects.filter(
                fecha_fin__lte=hoy + timedelta(days=7),
                estado='activa'
            ).count(),
            'total_archivos_audio': ArchivoAudio.objects.count(),
            'total_categorias': CategoriaPublicitaria.objects.filter(is_active=True).count(),
            'ingresos_mes_actual': CuñaPublicitaria.objects.filter(
                created_at__month=hoy.month,
                created_at__year=hoy.year,
                estado__in=['aprobada', 'activa', 'finalizada']
            ).aggregate(total=Sum('precio_total'))['total'] or 0,
            'ultima_actualizacion': timezone.now().isoformat(),
        }
        
        # Guardar en cache por 1 hora
        cache.set('dashboard_stats', stats, 3600)
        
        logger.info("Estadísticas de dashboard actualizadas en cache")
        
        return stats
        
    except Exception as exc:
        logger.error(f"Error actualizando estadísticas dashboard: {exc}")
        raise self.retry(exc=exc, countdown=60)

# ==================== TAREAS DE MANTENIMIENTO ====================

@shared_task(bind=True)
def backup_datos_criticos(self):
    """
    Realiza backup de datos críticos del sistema
    """
    try:
        from django.core.management import call_command
        from django.conf import settings
        import os
        from datetime import datetime
        
        # Crear directorio de backup si no existe
        backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/publictrack_backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nombre del archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'publictrack_backup_{timestamp}.json')
        
        # Ejecutar comando de backup
        with open(backup_file, 'w') as f:
            call_command('dumpdata', 
                        'content_management', 
                        'financial_management', 
                        'sales_management',
                        stdout=f, 
                        indent=2)
        
        # Comprimir archivo
        import gzip
        with open(backup_file, 'rb') as f_in:
            with gzip.open(f'{backup_file}.gz', 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Eliminar archivo sin comprimir
        os.remove(backup_file)
        
        logger.info(f"Backup creado: {backup_file}.gz")
        
        return f"Backup completado: {backup_file}.gz"
        
    except Exception as exc:
        logger.error(f"Error en backup_datos_criticos: {exc}")
        raise self.retry(exc=exc, countdown=300)

@shared_task(bind=True)
def limpiar_logs_antiguos(self):
    """
    Limpia logs y registros antiguos del sistema
    """
    try:
        from .models import HistorialCuña
        
        # Eliminar historial más antiguo de 2 años
        fecha_limite = timezone.now() - timedelta(days=730)
        
        historiales_eliminados = HistorialCuña.objects.filter(
            fecha__lt=fecha_limite
        ).delete()[0]
        
        logger.info(f"Limpieza completada. {historiales_eliminados} registros de historial eliminados")
        
        # Aquí puedes agregar más limpieza de logs si es necesario
        
        return f"Eliminados {historiales_eliminados} registros antiguos"
        
    except Exception as exc:
        logger.error(f"Error en limpiar_logs_antiguos: {exc}")
        raise self.retry(exc=exc, countdown=300)

# ==================== CONFIGURACIÓN DE TAREAS PERIÓDICAS ====================

# Para usar con Celery Beat, agrega esto a tu settings.py:
"""
CELERY_BEAT_SCHEDULE = {
    'verificar-cuñas-por-vencer': {
        'task': 'apps.content_management.tasks.verificar_cuñas_por_vencer',
        'schedule': crontab(hour=9, minute=0),  # Diario a las 9:00 AM
    },
    'finalizar-cuñas-vencidas': {
        'task': 'apps.content_management.tasks.finalizar_cuñas_vencidas',
        'schedule': crontab(hour=1, minute=0),  # Diario a la 1:00 AM
    },
    'enviar-resumen-diario-vendedores': {
        'task': 'apps.content_management.tasks.enviar_resumen_diario_vendedores',
        'schedule': crontab(hour=8, minute=0),  # Diario a las 8:00 AM
    },
    'actualizar-estadisticas-dashboard': {
        'task': 'apps.content_management.tasks.actualizar_estadisticas_dashboard',
        'schedule': crontab(minute='*/30'),  # Cada 30 minutos
    },
    'limpiar-archivos-temporales': {
        'task': 'apps.content_management.tasks.limpiar_archivos_temporales',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Lunes a las 2:00 AM
    },
    'backup-datos-criticos': {
        'task': 'apps.content_management.tasks.backup_datos_criticos',
        'schedule': crontab(hour=3, minute=0),  # Diario a las 3:00 AM
    },
    'limpiar-logs-antiguos': {
        'task': 'apps.content_management.tasks.limpiar_logs_antiguos',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),  # Primer día del mes a las 4:00 AM
    },
}
"""