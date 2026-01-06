"""
Señales para la aplicación Orders
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import OrdenToma, HistorialOrden
from apps.authentication.models import CustomUser
from .models import OrdenProduccion, HistorialOrdenProduccion


@receiver(pre_save, sender=OrdenToma)
def orden_pre_save(sender, instance, **kwargs):
    """Captura el estado anterior antes de guardar"""
    if instance.pk:
        try:
            instance._estado_anterior = OrdenToma.objects.get(pk=instance.pk)
        except OrdenToma.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=OrdenToma)
def orden_post_save(sender, instance, created, **kwargs):
    """Crea entrada en el historial después de guardar"""
    if not created:
        estado_anterior = getattr(instance, '_estado_anterior', None)
        if estado_anterior and estado_anterior.estado != instance.estado:
            accion_map = {
                'validado': 'validada',
                'en_produccion': 'produccion',
                'completado': 'completada',
                'cancelado': 'cancelada',
            }
            
            accion = accion_map.get(instance.estado, 'editada')
            
            HistorialOrden.objects.create(
                orden=instance,
                accion=accion,
                usuario=getattr(instance, 'validado_por', None) or getattr(instance, 'completado_por', None),
                descripcion=f'Orden cambió de estado: {estado_anterior.estado} → {instance.estado}',
                datos_anteriores={'estado': estado_anterior.estado},
                datos_nuevos={'estado': instance.estado}
            )

@receiver(pre_save, sender=OrdenProduccion)
def orden_produccion_pre_save(sender, instance, **kwargs):
    """Captura el estado anterior antes de guardar"""
    if instance.pk:
        try:
            instance._estado_anterior = OrdenProduccion.objects.get(pk=instance.pk)
        except OrdenProduccion.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None

@receiver(post_save, sender=OrdenProduccion)
def orden_produccion_post_save(sender, instance, created, **kwargs):
    """Crea entrada en el historial después de guardar"""
    if created:
        # Crear entrada de historial para creación
        HistorialOrdenProduccion.objects.create(
            orden_produccion=instance,
            accion='creada',
            usuario=instance.created_by,
            descripcion=f'Orden de producción creada automáticamente desde orden de toma {instance.orden_toma.codigo}'
        )
    else:
        estado_anterior = getattr(instance, '_estado_anterior', None)
        if estado_anterior and estado_anterior.estado != instance.estado:
            accion_map = {
                'en_produccion': 'iniciada',
                'completado': 'completada',
                'validado': 'validada',
                'cancelado': 'cancelada',
            }
            
            accion = accion_map.get(instance.estado, 'editada')
            
            HistorialOrdenProduccion.objects.create(
                orden_produccion=instance,
                accion=accion,
                usuario=getattr(instance, 'validado_por', None) or getattr(instance, 'completado_por', None) or instance.created_by,
                descripcion=f'Orden cambió de estado: {estado_anterior.estado} → {instance.estado}',
                datos_anteriores={'estado': estado_anterior.estado},
                datos_nuevos={'estado': instance.estado}
            )

# Señal para crear automáticamente orden de producción cuando se valida orden de toma

@receiver(post_save, sender=OrdenToma)
def crear_orden_produccion_al_validar(sender, instance, created, **kwargs):
    """Señal como respaldo - la lógica principal está en la vista de subir archivo"""
    if not created and instance.estado == 'validado':
        # Verificar si ya existe una orden de producción para esta orden de toma
        if not OrdenProduccion.objects.filter(orden_toma=instance).exists():
            try:
                orden_produccion = OrdenProduccion.objects.create(
                    orden_toma=instance,
                    created_by=instance.validado_por or instance.created_by,
                    estado='pendiente',
                    nombre_cliente=instance.nombre_cliente,
                    ruc_dni_cliente=instance.ruc_dni_cliente,
                    empresa_cliente=instance.empresa_cliente,
                    proyecto_campania=instance.proyecto_campania or 'Proyecto por definir',
                    titulo_material=instance.titulo_material or 'Material por definir',
                    descripcion_breve=instance.descripcion_breve or 'Descripción por completar',
                    # Checkboxes
                    requiere_tomas=instance.incluye_tomas,
                    requiere_audio=instance.incluye_audio,
                    requiere_logo=instance.incluye_logo,
                    
                    equipo_asignado=instance.equipo_asignado or 'Equipo por asignar',
                    recursos_necesarios=instance.recursos_necesarios or '',
                    fecha_inicio_planeada=instance.fecha_produccion_inicio or timezone.now().date(),
                    fecha_fin_planeada=instance.fecha_produccion_fin or (timezone.now() + timezone.timedelta(days=7)).date(),
                    tipo_produccion='video'
                )
                
                print(f"✅ [SEÑAL] Orden de producción creada automáticamente: {orden_produccion.codigo}")
                
            except Exception as e:
                print(f"❌ [SEÑAL] Error al crear orden de producción automática: {e}")