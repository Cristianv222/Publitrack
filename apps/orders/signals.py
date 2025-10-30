# apps/orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import OrdenToma, HistorialOrden

User = get_user_model()

@receiver(post_save, sender=User)
def crear_orden_toma_automatica(sender, instance, created, **kwargs):
    """
    Crea automáticamente una orden de toma cuando se crea un nuevo cliente
    """
    # Solo crear orden si es un cliente nuevo
    if created and instance.rol == 'cliente':
        try:
            # Crear orden de toma automáticamente
            orden_toma = OrdenToma.objects.create(
                cliente=instance,
                descripcion=f'Orden de toma automática para el cliente {instance.empresa or instance.get_full_name()}',
                tipo_toma='voz',
                duracion_estimada=30,
                estado='generada',
                prioridad='normal',
                created_by=instance,  # Esto se ajustará en save_model del admin
            )
            
            # Crear entrada en el historial
            HistorialOrden.objects.create(
                orden_toma=orden_toma,
                accion='creada',
                usuario=instance,  # Esto se ajustará en save_model del admin
                descripcion=f'Orden de toma creada automáticamente para el cliente {instance.empresa}'
            )
            
            print(f"✅ Orden de toma creada automáticamente: {orden_toma.codigo} para cliente: {instance.empresa}")
            
        except Exception as e:
            print(f"❌ Error al crear orden de toma automática: {e}")

@receiver(post_save, sender=OrdenToma)
def crear_historial_orden(sender, instance, created, **kwargs):
    """
    Crea entrada en el historial cuando se crea o modifica una orden
    """
    if created:
        try:
            HistorialOrden.objects.create(
                orden_toma=instance,
                accion='creada',
                usuario=instance.created_by,
                descripcion=f'Orden de toma creada para el cliente {instance.cliente.empresa}',
                datos_nuevos={
                    'codigo': instance.codigo,
                    'estado': instance.estado,
                    'tipo_toma': instance.tipo_toma,
                    'cliente': instance.cliente.empresa,
                }
            )
        except Exception as e:
            print(f"❌ Error al crear historial de orden: {e}")