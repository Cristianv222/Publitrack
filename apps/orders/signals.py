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