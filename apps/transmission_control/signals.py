"""
Señales para el módulo de Control de Transmisiones
Sistema PubliTrack - Automatización de eventos y validaciones
"""

from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.signals import user_logged_in, user_logged_out
from datetime import timedelta

from .models import (
    ConfiguracionTransmision,
    ProgramacionTransmision,
    TransmisionActual,
    LogTransmision,
    EventoSistema
)
from apps.content_management.models import CuñaPublicitaria


# ==================== SEÑALES DE CONFIGURACIÓN ====================

@receiver(post_save, sender=ConfiguracionTransmision)
def configuracion_actualizada(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando se actualiza la configuración del sistema
    """
    # Limpiar cache de configuración
    cache.delete('configuracion_transmision_activa')
    
    # Crear evento del sistema
    EventoSistema.objects.create(
        tipo_evento='cambio_configuracion',
        descripcion=f'Configuración {"creada" if created else "actualizada"}: {instance.nombre_configuracion}',
        usuario=getattr(instance, '_user_modificador', None),
        configuracion_despues={
            'modo_operacion': instance.modo_operacion,
            'estado_sistema': instance.estado_sistema,
            'hora_inicio': instance.hora_inicio_transmision.strftime('%H:%M'),
            'hora_fin': instance.hora_fin_transmision.strftime('%H:%M'),
            'intervalo_minimo': instance.intervalo_minimo_segundos,
        }
    )
    
    # Si se desactiva una configuración, verificar que haya otra activa
    if not instance.is_active:
        activas = ConfiguracionTransmision.objects.filter(is_active=True).count()
        if activas == 0:
            # Crear evento de advertencia
            EventoSistema.objects.create(
                tipo_evento='error_critico',
                descripcion='No hay configuraciones activas en el sistema',
                resuelto=False
            )


# ==================== SEÑALES DE PROGRAMACIÓN ====================

@receiver(post_save, sender=ProgramacionTransmision)
def programacion_actualizada(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando se crea o actualiza una programación
    """
    # Log del evento
    LogTransmision.log_evento(
        accion='programacion_modificada',
        descripcion=f'Programación {"creada" if created else "actualizada"}: {instance.codigo}',
        programacion=instance,
        cuña=instance.cuña,
        usuario=getattr(instance, '_user_modificador', instance.created_by),
        datos={
            'created': created,
            'estado': instance.estado,
            'tipo_programacion': instance.tipo_programacion,
            'repeticiones_por_dia': instance.repeticiones_por_dia,
        }
    )
    
    # Si se activa la programación, verificar conflictos
    if instance.estado == 'activa':
        verificar_conflictos_programacion(instance)
    
    # Actualizar cache de próximas transmisiones
    cache.delete('proximas_transmisiones')


@receiver(pre_save, sender=ProgramacionTransmision)
def programacion_pre_save(sender, instance, **kwargs):
    """
    Se ejecuta antes de guardar una programación
    """
    # Capturar estado anterior para comparación
    if instance.pk:
        try:
            instance._estado_anterior = ProgramacionTransmision.objects.get(pk=instance.pk)
        except ProgramacionTransmision.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


def verificar_conflictos_programacion(programacion):
    """
    Verifica si hay conflictos con otras programaciones activas
    """
    # Buscar programaciones que se solapen en tiempo
    conflictos = ProgramacionTransmision.objects.filter(
        estado='activa',
        cuña=programacion.cuña
    ).exclude(pk=programacion.pk)
    
    if conflictos.exists():
        # Crear log de advertencia
        LogTransmision.log_evento(
            accion='programacion_modificada',
            descripcion=f'Posible conflicto detectado en programación {programacion.codigo}',
            programacion=programacion,
            nivel='warning',
            datos={'conflictos_detectados': list(conflictos.values_list('codigo', flat=True))}
        )


# ==================== SEÑALES DE TRANSMISIÓN ====================

@receiver(post_save, sender=TransmisionActual)
def transmision_actualizada(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando se actualiza una transmisión
    """
    if created:
        # Nueva transmisión creada
        LogTransmision.log_evento(
            accion='programada',
            descripcion=f'Nueva transmisión programada: {instance.cuña.titulo}',
            transmision=instance,
            cuña=instance.cuña,
            programacion=instance.programacion,
            datos={
                'inicio_programado': instance.inicio_programado.isoformat(),
                'duracion_estimada': instance.cuña.duracion_planeada,
            }
        )
        
        # Actualizar estadísticas de la programación
        if instance.programacion:
            instance.programacion.total_reproducciones_programadas += 1
            instance.programacion.save(update_fields=['total_reproducciones_programadas'])
    
    else:
        # Transmisión actualizada - verificar cambios importantes
        estado_anterior = getattr(instance, '_estado_anterior', None)
        if estado_anterior and estado_anterior.estado != instance.estado:
            # Cambio de estado
            LogTransmision.log_evento(
                accion=instance.estado,
                descripcion=f'Transmisión cambió de estado: {estado_anterior.estado} → {instance.estado}',
                transmision=instance,
                cuña=instance.cuña,
                datos={
                    'estado_anterior': estado_anterior.estado,
                    'estado_nuevo': instance.estado,
                }
            )
            
            # Acciones específicas según el nuevo estado
            if instance.estado == 'error':
                manejar_error_transmision(instance)
            elif instance.estado == 'completada':
                manejar_transmision_completada(instance)
    
    # Actualizar cache de transmisión actual
    if instance.estado == 'transmitiendo':
        cache.set('transmision_actual', instance, timeout=300)  # 5 minutos
    elif instance.estado in ['completada', 'error', 'cancelada']:
        cache.delete('transmision_actual')


@receiver(pre_save, sender=TransmisionActual)
def transmision_pre_save(sender, instance, **kwargs):
    """
    Se ejecuta antes de guardar una transmisión
    """
    # Capturar estado anterior
    if instance.pk:
        try:
            instance._estado_anterior = TransmisionActual.objects.get(pk=instance.pk)
        except TransmisionActual.DoesNotExist:
            instance._estado_anterior = None


def manejar_error_transmision(transmision):
    """
    Maneja cuando una transmisión tiene error
    """
    # Crear evento del sistema
    EventoSistema.objects.create(
        tipo_evento='error_critico',
        descripcion=f'Error en transmisión: {transmision.cuña.titulo}',
        usuario=None,
        datos_sistema={
            'session_id': str(transmision.session_id),
            'cuña_codigo': transmision.cuña.codigo,
            'errores': transmision.errores_detectados,
        },
        resuelto=False
    )
    
    # Notificar automáticamente si está configurado
    configuracion = ConfiguracionTransmision.get_configuracion_activa()
    if configuracion and configuracion.notificar_errores:
        # Aquí se podría enviar notificación por email/SMS
        pass


def manejar_transmision_completada(transmision):
    """
    Maneja cuando una transmisión se completa exitosamente
    """
    # Actualizar estadísticas del cliente
    if transmision.cuña.cliente:
        # Aquí se podrían actualizar métricas del cliente
        pass
    
    # Verificar si hay próximas transmisiones programadas
    proximas = TransmisionActual.objects.filter(
        estado='preparando',
        inicio_programado__gt=timezone.now()
    ).order_by('inicio_programado')[:5]
    
    if not proximas.exists():
        # No hay más transmisiones programadas
        LogTransmision.log_evento(
            accion='sistema_pausado',
            descripcion='No hay más transmisiones programadas',
            nivel='info'
        )


# ==================== SEÑALES DE CUÑAS ====================

@receiver(post_save, sender=CuñaPublicitaria)
def cuña_actualizada(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando se actualiza una cuña publicitaria
    """
    if not created:
        # Verificar si el cambio afecta transmisiones activas
        estado_anterior = getattr(instance, '_estado_anterior', None)
        
        if estado_anterior and estado_anterior.estado != instance.estado:
            # La cuña cambió de estado
            if instance.estado not in ['activa', 'aprobada']:
                # Cuña ya no está disponible para transmisión
                cancelar_transmisiones_cuña(instance)
            
            # Log del cambio
            LogTransmision.log_evento(
                accion='cuña_estado_cambiado',
                descripcion=f'Cuña {instance.codigo} cambió estado: {estado_anterior.estado} → {instance.estado}',
                cuña=instance,
                nivel='warning' if instance.estado not in ['activa', 'aprobada'] else 'info',
                datos={
                    'estado_anterior': estado_anterior.estado,
                    'estado_nuevo': instance.estado,
                }
            )


def cancelar_transmisiones_cuña(cuña):
    """
    Cancela todas las transmisiones futuras de una cuña
    """
    # Cancelar programaciones activas
    programaciones = ProgramacionTransmision.objects.filter(
        cuña=cuña,
        estado='activa'
    )
    
    for programacion in programaciones:
        programacion.estado = 'cancelada'
        programacion.proxima_reproduccion = None
        programacion.save()
        
        LogTransmision.log_evento(
            accion='cancelada',
            descripcion=f'Programación cancelada automáticamente por cambio de estado de cuña',
            programacion=programacion,
            cuña=cuña,
            nivel='warning'
        )
    
    # Cancelar transmisiones futuras
    transmisiones_futuras = TransmisionActual.objects.filter(
        cuña=cuña,
        estado='preparando',
        inicio_programado__gt=timezone.now()
    )
    
    for transmision in transmisiones_futuras:
        transmision.estado = 'cancelada'
        transmision.save()


# ==================== SEÑALES DE USUARIO ====================

@receiver(user_logged_in)
def usuario_ingresado(sender, request, user, **kwargs):
    """
    Se ejecuta cuando un usuario inicia sesión
    """
    # Solo registrar si tiene permisos de transmisión
    if user.can_manage_content():
        LogTransmision.log_evento(
            accion='sistema_iniciado',
            descripcion=f'Usuario {user.username} accedió al sistema de transmisiones',
            usuario=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )


@receiver(user_logged_out)
def usuario_salio(sender, request, user, **kwargs):
    """
    Se ejecuta cuando un usuario cierra sesión
    """
    if user and user.can_manage_content():
        LogTransmision.log_evento(
            accion='sistema_pausado',
            descripcion=f'Usuario {user.username} salió del sistema de transmisiones',
            usuario=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')  # ← AGREGAR ESTA LÍNEA
        )

# ==================== SEÑALES DE LOGS ====================

@receiver(post_save, sender=LogTransmision)
def log_creado(sender, instance, created, **kwargs):
    """
    Se ejecuta cuando se crea un nuevo log
    """
    if created:
        # Verificar si es un error crítico que requiere atención inmediata
        if instance.nivel == 'critical':
            # Crear evento del sistema
            EventoSistema.objects.create(
                tipo_evento='error_critico',
                descripcion=f'Error crítico detectado: {instance.descripcion}',
                usuario=instance.usuario,
                datos_sistema={
                    'log_id': instance.id,
                    'accion': instance.accion,
                    'datos': instance.datos,
                },
                resuelto=False
            )
        
        # Limpiar logs antiguos automáticamente (mantener solo últimos 10000)
        if LogTransmision.objects.count() > 10000:
            ids_antiguos = LogTransmision.objects.order_by('-timestamp')[10000:].values_list('id', flat=True)
            LogTransmision.objects.filter(id__in=ids_antiguos).delete()


# ==================== FUNCIONES DE UTILIDAD ====================

def inicializar_sistema_transmision():
    """
    Inicializa el sistema de transmisiones al arrancar
    """
    # Verificar configuración activa
    configuracion = ConfiguracionTransmision.get_configuracion_activa()
    if not configuracion:
        EventoSistema.objects.create(
            tipo_evento='error_critico',
            descripcion='Sistema iniciado sin configuración activa',
            resuelto=False
        )
        return False
    
    # Limpiar transmisiones huérfanas (sin programación o con errores)
    huerfanas = TransmisionActual.objects.filter(
        estado__in=['preparando', 'transmitiendo'],
        programacion__isnull=True
    )
    
    for transmision in huerfanas:
        transmision.estado = 'cancelada'
        transmision.save()
    
    # Verificar transmisiones que deberían haber terminado
    ahora = timezone.now()
    transmisiones_colgadas = TransmisionActual.objects.filter(
        estado='transmitiendo',
        fin_programado__lt=ahora - timedelta(minutes=5)  # 5 minutos de gracia
    )
    
    for transmision in transmisiones_colgadas:
        transmision.finalizar_transmision(None, 'error')
        LogTransmision.log_evento(
            accion='error',
            descripcion='Transmisión finalizada automáticamente por timeout',
            transmision=transmision,
            nivel='error'
        )
    
    # Crear evento de inicio del sistema
    EventoSistema.objects.create(
        tipo_evento='inicio_sistema',
        descripcion='Sistema de transmisiones inicializado correctamente',
        datos_sistema={
            'configuracion_activa': configuracion.nombre_configuracion,
            'transmisiones_activas': TransmisionActual.objects.filter(estado='transmitiendo').count(),
            'programaciones_activas': ProgramacionTransmision.objects.filter(estado='activa').count(),
        }
    )
    
    return True


def verificar_salud_sistema():
    """
    Verifica la salud general del sistema de transmisiones
    """
    problemas = []
    
    # Verificar configuración
    configuracion = ConfiguracionTransmision.get_configuracion_activa()
    if not configuracion:
        problemas.append('No hay configuración activa')
    elif not configuracion.puede_transmitir():
        problemas.append('Sistema no puede transmitir según configuración')
    
    # Verificar errores recientes
    errores_recientes = LogTransmision.objects.filter(
        nivel__in=['error', 'critical'],
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if errores_recientes > 5:
        problemas.append(f'Muchos errores recientes: {errores_recientes}')
    
    # Verificar transmisiones colgadas
    transmisiones_colgadas = TransmisionActual.objects.filter(
        estado='transmitiendo',
        fin_programado__lt=timezone.now() - timedelta(minutes=10)
    ).count()
    
    if transmisiones_colgadas > 0:
        problemas.append(f'Transmisiones colgadas: {transmisiones_colgadas}')
    
    # Crear evento si hay problemas
    if problemas:
        EventoSistema.objects.create(
            tipo_evento='error_critico',
            descripcion=f'Problemas detectados en verificación de salud: {", ".join(problemas)}',
            datos_sistema={'problemas': problemas},
            resuelto=False
        )
        return False
    
    return True


# ==================== INICIALIZACIÓN ====================

# Función para conectar señales al arrancar la aplicación
def conectar_señales():
    """
    Conecta todas las señales del módulo
    """
    # Las señales ya están conectadas por los decoradores @receiver
    # Esta función se puede usar para inicializaciones adicionales
    pass