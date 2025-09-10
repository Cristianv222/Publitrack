"""
Tareas programadas para el módulo de Control de Transmisiones
Sistema PubliTrack - Automatización de transmisiones y mantenimiento
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db.models import Q, Count
from django.core.cache import cache
from datetime import datetime, timedelta
import json

from .models import (
    ConfiguracionTransmision,
    ProgramacionTransmision,
    TransmisionActual,
    LogTransmision,
    EventoSistema,
    obtener_transmision_actual,
    verificar_sistema_listo_para_transmitir
)
from apps.content_management.models import CuñaPublicitaria

logger = get_task_logger(__name__)


# ==================== TAREAS PRINCIPALES ====================

@shared_task(bind=True, max_retries=3)
def procesar_transmisiones_programadas(self):
    """
    Tarea principal que procesa y ejecuta transmisiones programadas
    Debe ejecutarse cada minuto
    """
    try:
        logger.info("Iniciando procesamiento de transmisiones programadas")
        
        # Verificar que el sistema esté listo
        sistema_listo, mensaje = verificar_sistema_listo_para_transmitir()
        if not sistema_listo:
            logger.warning(f"Sistema no listo para transmitir: {mensaje}")
            return {'status': 'sistema_no_listo', 'mensaje': mensaje}
        
        ahora = timezone.now()
        transmisiones_creadas = 0
        
        # Buscar programaciones que deben ejecutarse ahora
        programaciones_activas = ProgramacionTransmision.objects.filter(
            estado='activa',
            proxima_reproduccion__lte=ahora + timedelta(minutes=1),  # 1 minuto de ventana
            proxima_reproduccion__gte=ahora - timedelta(minutes=5)   # No más de 5 minutos tarde
        ).select_related('cuña', 'cuña__archivo_audio')
        
        for programacion in programaciones_activas:
            if programacion.puede_reproducir_ahora():
                # Verificar que la cuña esté disponible
                if not programacion.cuña.esta_activa:
                    logger.warning(f"Cuña {programacion.cuña.codigo} no está activa, saltando programación {programacion.codigo}")
                    continue
                
                # Verificar que no haya conflictos
                if hay_conflicto_transmision(programacion):
                    logger.warning(f"Conflicto detectado para programación {programacion.codigo}, postponiendo")
                    continue
                
                # Crear transmisión
                transmision = crear_transmision_desde_programacion(programacion)
                if transmision:
                    transmisiones_creadas += 1
                    logger.info(f"Transmisión creada: {transmision.session_id}")
        
        # Actualizar cache de próximas transmisiones
        cache.delete('proximas_transmisiones')
        
        logger.info(f"Procesamiento completado. Transmisiones creadas: {transmisiones_creadas}")
        
        return {
            'status': 'completado',
            'transmisiones_creadas': transmisiones_creadas,
            'timestamp': ahora.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error en procesamiento de transmisiones: {exc}")
        
        # Crear evento del sistema
        EventoSistema.objects.create(
            tipo_evento='error_critico',
            descripcion=f'Error en tarea de procesamiento: {str(exc)}',
            resuelto=False
        )
        
        # Reintentar la tarea
        raise self.retry(exc=exc, countdown=60)  # Reintentar en 1 minuto


@shared_task
def monitorear_transmisiones_activas():
    """
    Monitorea transmisiones activas y detecta problemas
    Debe ejecutarse cada 30 segundos
    """
    try:
        logger.info("Monitoreando transmisiones activas")
        
        ahora = timezone.now()
        problemas_detectados = 0
        
        # Buscar transmisiones que deberían haber terminado
        transmisiones_colgadas = TransmisionActual.objects.filter(
            estado='transmitiendo',
            fin_programado__lt=ahora - timedelta(minutes=2)  # 2 minutos de gracia
        )
        
        for transmision in transmisiones_colgadas:
            logger.warning(f"Transmisión colgada detectada: {transmision.session_id}")
            
            transmision.finalizar_transmision(None, 'error')
            transmision.reportar_error("Transmisión finalizada automáticamente por timeout")
            problemas_detectados += 1
        
        # Buscar transmisiones que deberían haber empezado
        transmisiones_retrasadas = TransmisionActual.objects.filter(
            estado='preparando',
            inicio_programado__lt=ahora - timedelta(minutes=5)  # 5 minutos de retraso
        )
        
        for transmision in transmisiones_retrasadas:
            logger.warning(f"Transmisión retrasada detectada: {transmision.session_id}")
            
            # Intentar iniciar o cancelar
            if transmision.cuña.esta_activa:
                transmision.iniciar_transmision()
                logger.info(f"Transmisión retrasada iniciada: {transmision.session_id}")
            else:
                transmision.finalizar_transmision(None, 'cancelada')
                logger.info(f"Transmisión retrasada cancelada: {transmision.session_id}")
            
            problemas_detectados += 1
        
        return {
            'status': 'completado',
            'problemas_detectados': problemas_detectados,
            'timestamp': ahora.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error en monitoreo de transmisiones: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


@shared_task
def actualizar_proximas_reproducciones():
    """
    Actualiza las próximas reproducciones de todas las programaciones activas
    Debe ejecutarse cada hora
    """
    try:
        logger.info("Actualizando próximas reproducciones")
        
        programaciones_activas = ProgramacionTransmision.objects.filter(
            estado='activa'
        )
        
        actualizadas = 0
        for programacion in programaciones_activas:
            programacion.calcular_proxima_reproduccion()
            actualizadas += 1
        
        logger.info(f"Próximas reproducciones actualizadas: {actualizadas}")
        
        return {
            'status': 'completado',
            'programaciones_actualizadas': actualizadas
        }
        
    except Exception as exc:
        logger.error(f"Error actualizando próximas reproducciones: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


# ==================== TAREAS DE MANTENIMIENTO ====================

@shared_task
def limpiar_logs_antiguos():
    """
    Limpia logs antiguos del sistema
    Debe ejecutarse diariamente
    """
    try:
        logger.info("Iniciando limpieza de logs antiguos")
        
        # Eliminar logs más antiguos de 90 días
        fecha_limite = timezone.now() - timedelta(days=90)
        
        logs_eliminados = LogTransmision.objects.filter(
            timestamp__lt=fecha_limite
        ).count()
        
        LogTransmision.objects.filter(timestamp__lt=fecha_limite).delete()
        
        # Eliminar eventos del sistema más antiguos de 180 días
        fecha_limite_eventos = timezone.now() - timedelta(days=180)
        
        eventos_eliminados = EventoSistema.objects.filter(
            timestamp__lt=fecha_limite_eventos,
            resuelto=True
        ).count()
        
        EventoSistema.objects.filter(
            timestamp__lt=fecha_limite_eventos,
            resuelto=True
        ).delete()
        
        logger.info(f"Limpieza completada. Logs: {logs_eliminados}, Eventos: {eventos_eliminados}")
        
        return {
            'status': 'completado',
            'logs_eliminados': logs_eliminados,
            'eventos_eliminados': eventos_eliminados
        }
        
    except Exception as exc:
        logger.error(f"Error en limpieza de logs: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


@shared_task
def limpiar_transmisiones_antiguas():
    """
    Limpia transmisiones completadas antiguas
    Debe ejecutarse semanalmente
    """
    try:
        logger.info("Iniciando limpieza de transmisiones antiguas")
        
        # Eliminar transmisiones completadas más antiguas de 30 días
        fecha_limite = timezone.now() - timedelta(days=30)
        
        transmisiones_eliminadas = TransmisionActual.objects.filter(
            estado__in=['completada', 'cancelada'],
            created_at__lt=fecha_limite
        ).count()
        
        TransmisionActual.objects.filter(
            estado__in=['completada', 'cancelada'],
            created_at__lt=fecha_limite
        ).delete()
        
        logger.info(f"Transmisiones antiguas eliminadas: {transmisiones_eliminadas}")
        
        return {
            'status': 'completado',
            'transmisiones_eliminadas': transmisiones_eliminadas
        }
        
    except Exception as exc:
        logger.error(f"Error en limpieza de transmisiones: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


@shared_task
def verificar_salud_sistema():
    """
    Verifica la salud general del sistema de transmisiones
    Debe ejecutarse cada 15 minutos
    """
    try:
        logger.info("Verificando salud del sistema")
        
        from .signals import verificar_salud_sistema as verificar_salud
        
        salud_ok = verificar_salud()
        
        # Actualizar cache con estado del sistema
        cache.set('sistema_transmision_salud', {
            'salud_ok': salud_ok,
            'timestamp': timezone.now().isoformat(),
            'ultima_verificacion': timezone.now()
        }, timeout=900)  # 15 minutos
        
        return {
            'status': 'completado',
            'salud_ok': salud_ok,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error en verificación de salud: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


# ==================== TAREAS DE NOTIFICACIONES ====================

@shared_task
def procesar_notificaciones_vencimiento():
    """
    Procesa notificaciones de cuñas próximas a vencer
    Debe ejecutarse diariamente
    """
    try:
        logger.info("Procesando notificaciones de vencimiento")
        
        # Buscar cuñas que requieren notificación de vencimiento
        cuñas_por_vencer = CuñaPublicitaria.objects.filter(
            notificar_vencimiento=True,
            estado='activa'
        )
        
        notificaciones_enviadas = 0
        
        for cuña in cuñas_por_vencer:
            if cuña.requiere_notificacion_vencimiento:
                # Enviar notificación (implementar según sistema de notificaciones)
                enviar_notificacion_vencimiento.delay(cuña.id)
                notificaciones_enviadas += 1
        
        logger.info(f"Notificaciones de vencimiento procesadas: {notificaciones_enviadas}")
        
        return {
            'status': 'completado',
            'notificaciones_enviadas': notificaciones_enviadas
        }
        
    except Exception as exc:
        logger.error(f"Error procesando notificaciones: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


@shared_task
def enviar_notificacion_vencimiento(cuña_id):
    """
    Envía notificación específica de vencimiento
    """
    try:
        cuña = CuñaPublicitaria.objects.get(id=cuña_id)
        
        # Aquí implementar envío de notificación
        # Por email, SMS, etc.
        
        logger.info(f"Notificación de vencimiento enviada para cuña {cuña.codigo}")
        
        return {'status': 'completado', 'cuña': cuña.codigo}
        
    except CuñaPublicitaria.DoesNotExist:
        logger.error(f"Cuña {cuña_id} no encontrada para notificación")
        return {'status': 'error', 'mensaje': 'Cuña no encontrada'}
    
    except Exception as exc:
        logger.error(f"Error enviando notificación: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


# ==================== TAREAS DE ESTADÍSTICAS ====================

@shared_task
def generar_estadisticas_diarias():
    """
    Genera estadísticas diarias del sistema
    Debe ejecutarse al final de cada día
    """
    try:
        logger.info("Generando estadísticas diarias")
        
        ayer = timezone.now().date() - timedelta(days=1)
        inicio_dia = datetime.combine(ayer, datetime.min.time())
        fin_dia = datetime.combine(ayer, datetime.max.time())
        
        if timezone.is_naive(inicio_dia):
            inicio_dia = timezone.make_aware(inicio_dia)
        if timezone.is_naive(fin_dia):
            fin_dia = timezone.make_aware(fin_dia)
        
        # Obtener transmisiones del día
        transmisiones_dia = TransmisionActual.objects.filter(
            inicio_programado__range=[inicio_dia, fin_dia]
        )
        
        estadisticas = {
            'fecha': ayer.isoformat(),
            'total_transmisiones': transmisiones_dia.count(),
            'completadas': transmisiones_dia.filter(estado='completada').count(),
            'con_error': transmisiones_dia.filter(estado='error').count(),
            'canceladas': transmisiones_dia.filter(estado='cancelada').count(),
            'tiempo_total_transmitido': sum([
                t.duracion_segundos or 0 
                for t in transmisiones_dia.filter(duracion_segundos__isnull=False)
            ]),
        }
        
        # Cuñas más transmitidas del día
        cuñas_populares = LogTransmision.objects.filter(
            timestamp__range=[inicio_dia, fin_dia],
            accion='iniciada',
            cuña__isnull=False
        ).values(
            'cuña__codigo',
            'cuña__titulo'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:5]
        
        estadisticas['cuñas_populares'] = list(cuñas_populares)
        
        # Guardar en cache o base de datos
        cache.set(f'estadisticas_diarias_{ayer.isoformat()}', estadisticas, timeout=86400*7)  # 7 días
        
        logger.info(f"Estadísticas diarias generadas para {ayer}")
        
        return {
            'status': 'completado',
            'fecha': ayer.isoformat(),
            'estadisticas': estadisticas
        }
        
    except Exception as exc:
        logger.error(f"Error generando estadísticas diarias: {exc}")
        return {'status': 'error', 'mensaje': str(exc)}


# ==================== FUNCIONES DE UTILIDAD ====================

def crear_transmision_desde_programacion(programacion):
    """
    Crea una nueva transmisión a partir de una programación
    """
    try:
        # Verificar que no haya transmisión activa de la misma cuña
        transmision_existente = TransmisionActual.objects.filter(
            cuña=programacion.cuña,
            estado__in=['preparando', 'transmitiendo']
        ).first()
        
        if transmision_existente:
            logger.warning(f"Ya existe transmisión activa para cuña {programacion.cuña.codigo}")
            return None
        
        # Calcular tiempos
        ahora = timezone.now()
        inicio_programado = programacion.proxima_reproduccion or ahora
        
        duracion = programacion.cuña.archivo_audio.duracion_segundos if programacion.cuña.archivo_audio else programacion.cuña.duracion_planeada
        fin_programado = inicio_programado + timedelta(seconds=duracion)
        
        # Crear transmisión
        transmision = TransmisionActual.objects.create(
            programacion=programacion,
            cuña=programacion.cuña,
            inicio_programado=inicio_programado,
            fin_programado=fin_programado,
            duracion_segundos=duracion
        )
        
        # Iniciar automáticamente si es el momento
        if inicio_programado <= ahora + timedelta(seconds=30):  # 30 segundos de ventana
            transmision.iniciar_transmision()
        
        return transmision
        
    except Exception as exc:
        logger.error(f"Error creando transmisión: {exc}")
        return None


def hay_conflicto_transmision(programacion):
    """
    Verifica si hay conflictos de tiempo con otras transmisiones
    """
    configuracion = ConfiguracionTransmision.get_configuracion_activa()
    if not configuracion or configuracion.permitir_solapamiento:
        return False
    
    # Verificar transmisiones activas en el período
    inicio = programacion.proxima_reproduccion
    if not inicio:
        return False
    
    duracion = programacion.cuña.archivo_audio.duracion_segundos if programacion.cuña.archivo_audio else programacion.cuña.duracion_planeada
    fin = inicio + timedelta(seconds=duracion)
    
    conflictos = TransmisionActual.objects.filter(
        Q(inicio_programado__lt=fin) & Q(fin_programado__gt=inicio),
        estado__in=['preparando', 'transmitiendo']
    ).exclude(programacion=programacion)
    
    return conflictos.exists()


# ==================== CONFIGURACIÓN DE TAREAS PERIÓDICAS ====================

# Para usar con Celery Beat, agregar en settings.py:
"""
CELERY_BEAT_SCHEDULE = {
    'procesar-transmisiones': {
        'task': 'apps.transmission_control.tasks.procesar_transmisiones_programadas',
        'schedule': 60.0,  # Cada minuto
    },
    'monitorear-transmisiones': {
        'task': 'apps.transmission_control.tasks.monitorear_transmisiones_activas',
        'schedule': 30.0,  # Cada 30 segundos
    },
    'actualizar-proximas': {
        'task': 'apps.transmission_control.tasks.actualizar_proximas_reproducciones',
        'schedule': 3600.0,  # Cada hora
    },
    'verificar-salud': {
        'task': 'apps.transmission_control.tasks.verificar_salud_sistema',
        'schedule': 900.0,  # Cada 15 minutos
    },
    'limpiar-logs': {
        'task': 'apps.transmission_control.tasks.limpiar_logs_antiguos',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2 AM
    },
    'estadisticas-diarias': {
        'task': 'apps.transmission_control.tasks.generar_estadisticas_diarias',
        'schedule': crontab(hour=23, minute=55),  # Diario a las 11:55 PM
    },
    'notificaciones-vencimiento': {
        'task': 'apps.transmission_control.tasks.procesar_notificaciones_vencimiento',
        'schedule': crontab(hour=9, minute=0),  # Diario a las 9 AM
    },
}
"""