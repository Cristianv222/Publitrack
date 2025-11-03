"""
Señales para la aplicación Orders
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import OrdenToma, HistorialOrden


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_orden_toma_al_crear_cliente(sender, instance, created, **kwargs):
    """
    Señal que crea automáticamente una OrdenToma cuando se crea un cliente
    """
    # Solo ejecutar si es un cliente nuevo y tiene rol 'cliente'
    if created and instance.rol == 'cliente':
        print(f"🔔 SEÑAL EJECUTADA: Creando orden para cliente {instance.username}")
        
        try:
            # Verificar si ya existe una orden para este cliente (evitar duplicados)
            if OrdenToma.objects.filter(cliente=instance).exists():
                print(f"⚠️ El cliente {instance.username} ya tiene una orden existente")
                return
            
            # Crear la orden de toma automáticamente
            orden = OrdenToma.objects.create(
                cliente=instance,
                detalle_productos=f'Orden de toma automática para {instance.get_full_name() or instance.username}',
                cantidad=1,
                total=Decimal('0.00'),
                created_by=instance,
                estado='pendiente'
            )
            
            print(f"✅ Orden creada exitosamente: {orden.codigo} para cliente {instance.username}")
            
            # Registrar en historial
            HistorialOrden.objects.create(
                orden=orden,
                accion='creada',
                usuario=instance,
                descripcion='Orden de toma creada automáticamente al registrar cliente',
                datos_nuevos={
                    'codigo': orden.codigo,
                    'cliente': instance.get_full_name() or instance.username,
                    'estado': orden.estado,
                }
            )
            
        except Exception as e:
            print(f"❌ ERROR al crear orden: {str(e)}")
            import traceback
            traceback.print_exc()


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