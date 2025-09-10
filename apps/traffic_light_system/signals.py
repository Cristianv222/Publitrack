"""
Señales del Sistema de Semáforos
Sistema PubliTrack - Automatización de actualizaciones de estado
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from apps.content_management.models import CuñaPublicitaria
from .models import EstadoSemaforo, HistorialEstadoSemaforo
from .utils.status_calculator import StatusCalculator
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CuñaPublicitaria)
def actualizar_estado_semaforo_cuña(sender, instance, created, **kwargs):
    """
    Actualiza el estado del semáforo cuando se crea o modifica una cuña
    AUTOMÁTICO - Se ejecuta inmediatamente al guardar
    """
    try:
        # Solo procesar si la cuña tiene fechas válidas
        if not instance.fecha_inicio or not instance.fecha_fin:
            return
        
        # Obtener o crear calculadora
        calculator = StatusCalculator()
        
        # Actualizar estado inmediatamente
        estado_actualizado = calculator.actualizar_estado_cuña(instance, crear_historial=True)
        
        # Si el estado requiere alerta, procesarla inmediatamente en background
        if estado_actualizado.requiere_alerta and not estado_actualizado.alerta_enviada:
            # Usar Celery si está disponible, sino procesar directamente
            try:
                from .tasks import procesar_alerta_individual
                procesar_alerta_individual.delay(estado_actualizado.id)
                logger.info(f"Alerta programada para cuña {instance.codigo}")
            except ImportError:
                # Si no hay Celery, procesar directamente
                from .utils.status_calculator import AlertasManager
                manager = AlertasManager()
                manager._crear_alerta_para_estado(estado_actualizado)
                logger.info(f"Alerta creada directamente para cuña {instance.codigo}")
        
        logger.info(f"Estado de semáforo actualizado para cuña {instance.codigo}")
        
    except Exception as e:
        logger.error(f"Error actualizando estado de semáforo para cuña {instance.codigo}: {str(e)}")


@receiver(pre_save, sender=CuñaPublicitaria)
def capturar_estado_anterior_cuña(sender, instance, **kwargs):
    """
    Captura el estado anterior de la cuña para detectar cambios relevantes
    """
    if instance.pk:
        try:
            instance._estado_anterior_semaforo = CuñaPublicitaria.objects.get(pk=instance.pk)
        except CuñaPublicitaria.DoesNotExist:
            instance._estado_anterior_semaforo = None
    else:
        instance._estado_anterior_semaforo = None


@receiver(post_save, sender=CuñaPublicitaria)
def detectar_cambios_relevantes_cuña(sender, instance, created, **kwargs):
    """
    Detecta cambios relevantes en la cuña que requieren recálculo especial
    """
    if created:
        return  # Ya se maneja en actualizar_estado_semaforo_cuña
    
    try:
        estado_anterior = getattr(instance, '_estado_anterior_semaforo', None)
        if not estado_anterior:
            return
        
        # Detectar cambios que requieren atención especial
        cambios_importantes = []
        
        # Cambio de estado de la cuña
        if estado_anterior.estado != instance.estado:
            cambios_importantes.append(f"Estado: {estado_anterior.estado} → {instance.estado}")
        
        # Cambio de fechas
        if estado_anterior.fecha_inicio != instance.fecha_inicio:
            cambios_importantes.append(f"Fecha inicio: {estado_anterior.fecha_inicio} → {instance.fecha_inicio}")
        
        if estado_anterior.fecha_fin != instance.fecha_fin:
            cambios_importantes.append(f"Fecha fin: {estado_anterior.fecha_fin} → {instance.fecha_fin}")
        
        # Cambio de cliente o vendedor
        if estado_anterior.cliente_id != instance.cliente_id:
            cambios_importantes.append("Cambio de cliente")
        
        if estado_anterior.vendedor_asignado_id != instance.vendedor_asignado_id:
            cambios_importantes.append("Cambio de vendedor")
        
        # Si hay cambios importantes, crear entrada en historial
        if cambios_importantes:
            # Verificar si existe estado de semáforo
            try:
                estado_semaforo = EstadoSemaforo.objects.get(cuña=instance)
                
                # Agregar entrada al historial con información del cambio
                HistorialEstadoSemaforo.objects.create(
                    cuña=instance,
                    color_anterior=estado_semaforo.color_anterior,
                    color_nuevo=estado_semaforo.color_actual,
                    prioridad_anterior=estado_semaforo.prioridad,
                    prioridad_nueva=estado_semaforo.prioridad,
                    razon_cambio=f"Cambios en cuña: {', '.join(cambios_importantes)}",
                    dias_restantes=estado_semaforo.dias_restantes,
                    porcentaje_tiempo=estado_semaforo.porcentaje_tiempo_transcurrido,
                    configuracion_utilizada=estado_semaforo.configuracion_utilizada,
                    usuario_trigger=getattr(instance, '_user_modificador', None),
                    alerta_generada=estado_semaforo.requiere_alerta
                )
                
                logger.info(f"Historial actualizado para cuña {instance.codigo}: {cambios_importantes}")
                
            except EstadoSemaforo.DoesNotExist:
                # Si no existe estado, se creará en la otra señal
                pass
                
    except Exception as e:
        logger.error(f"Error detectando cambios en cuña {instance.codigo}: {str(e)}")


@receiver(post_delete, sender=CuñaPublicitaria)
def limpiar_estado_semaforo_cuña_eliminada(sender, instance, **kwargs):
    """
    Limpia los datos relacionados cuando se elimina una cuña
    """
    try:
        # El estado de semáforo se elimina automáticamente por CASCADE
        # Pero podemos hacer limpieza adicional si es necesario
        
        logger.info(f"Estados de semáforo eliminados para cuña {instance.codigo}")
        
    except Exception as e:
        logger.error(f"Error limpiando estados para cuña eliminada {instance.codigo}: {str(e)}")


@receiver(post_save, sender='traffic_light_system.ConfiguracionSemaforo')
def configuracion_semaforo_activada(sender, instance, created, **kwargs):
    """
    Recalcula todos los estados cuando se activa una nueva configuración
    """
    try:
        # Solo procesar si se activó la configuración
        if instance.is_active:
            logger.info(f"Configuración de semáforo activada: {instance.nombre}")
            
            # Nota: No recalculamos automáticamente aquí para evitar operaciones pesadas
            # El recálculo se debe hacer manualmente desde el admin o vistas
            
    except Exception as e:
        logger.error(f"Error procesando activación de configuración {instance.nombre}: {str(e)}")


@receiver(post_save, sender='traffic_light_system.EstadoSemaforo')
def generar_alerta_automatica(sender, instance, created, **kwargs):
    """
    Genera alertas automáticas cuando cambia un estado que las requiere
    """
    try:
        # Solo si requiere alerta y no se ha enviado
        if instance.requiere_alerta and not instance.alerta_enviada:
            
            # Importar aquí para evitar importaciones circulares
            from .utils.status_calculator import AlertasManager
            from .models import AlertaSemaforo
            
            # Verificar si ya existe alerta reciente para esta cuña
            alerta_existente = AlertaSemaforo.objects.filter(
                cuña=instance.cuña,
                estado__in=['pendiente', 'enviada'],
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).exists()
            
            if not alerta_existente:
                manager = AlertasManager()
                alerta = manager._crear_alerta_para_estado(instance)
                
                logger.info(f"Alerta automática generada para cuña {instance.cuña.codigo}")
            
    except Exception as e:
        logger.error(f"Error generando alerta automática para cuña {instance.cuña.codigo}: {str(e)}")


# Señal personalizada para recálculo masivo
from django.dispatch import Signal

# Señal que se emite cuando se completa un recálculo masivo
recalculo_masivo_completado = Signal()

@receiver(recalculo_masivo_completado)
def notificar_recalculo_masivo(sender, **kwargs):
    """
    Maneja la notificación cuando se completa un recálculo masivo
    """
    try:
        estadisticas = kwargs.get('estadisticas', {})
        configuracion = kwargs.get('configuracion', None)
        
        logger.info(
            f"Recálculo masivo completado - "
            f"Configuración: {configuracion.nombre if configuracion else 'N/A'}, "
            f"Estadísticas: {estadisticas}"
        )
        
        # Aquí se podrían agregar más acciones como:
        # - Enviar notificaciones a administradores
        # - Actualizar métricas en cache
        # - Generar reportes automáticos
        
    except Exception as e:
        logger.error(f"Error procesando notificación de recálculo masivo: {str(e)}")


# Señal para limpieza automática de datos antiguos
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

def limpiar_datos_antiguos():
    """
    Función para limpiar datos antiguos del sistema
    """
    try:
        from .models import HistorialEstadoSemaforo, AlertaSemaforo, ResumenEstadosSemaforo
        
        # Fecha límite para limpieza (6 meses atrás)
        fecha_limite = timezone.now() - timedelta(days=180)
        
        # Limpiar historial antiguo (mantener solo últimos 6 meses)
        historial_eliminado = HistorialEstadoSemaforo.objects.filter(
            fecha_cambio__lt=fecha_limite
        ).count()
        
        if historial_eliminado > 1000:  # Solo si hay muchos registros
            HistorialEstadoSemaforo.objects.filter(
                fecha_cambio__lt=fecha_limite
            ).delete()
            
            logger.info(f"Limpieza automática: {historial_eliminado} registros de historial eliminados")
        
        # Limpiar alertas antiguas procesadas
        alertas_eliminadas = AlertaSemaforo.objects.filter(
            estado__in=['enviada', 'ignorada'],
            created_at__lt=fecha_limite
        ).count()
        
        if alertas_eliminadas > 500:  # Solo si hay muchas alertas
            AlertaSemafero.objects.filter(
                estado__in=['enviada', 'ignorada'],
                created_at__lt=fecha_limite
            ).delete()
            
            logger.info(f"Limpieza automática: {alertas_eliminadas} alertas eliminadas")
        
        # Limpiar resúmenes diarios antiguos (mantener solo últimos 2 años)
        fecha_limite_resumenes = timezone.now() - timedelta(days=730)
        resumenes_eliminados = ResumenEstadosSemaforo.objects.filter(
            periodo='dia',
            fecha__lt=fecha_limite_resumenes.date()
        ).count()
        
        if resumenes_eliminados > 100:
            ResumenEstadosSemaforo.objects.filter(
                periodo='dia',
                fecha__lt=fecha_limite_resumenes.date()
            ).delete()
            
            logger.info(f"Limpieza automática: {resumenes_eliminados} resúmenes diarios eliminados")
            
    except Exception as e:
        logger.error(f"Error en limpieza automática de datos: {str(e)}")