"""
Señales personalizadas para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Señales adicionales para automatización
"""

import os
import hashlib
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import CuñaPublicitaria, ArchivoAudio, CategoriaPublicitaria

User = get_user_model()

# ==================== SEÑALES DE ARCHIVOS DE AUDIO ====================

@receiver(post_save, sender=ArchivoAudio)
def generar_hash_archivo(sender, instance, created, **kwargs):
    """
    Genera hash SHA256 del archivo de audio después de guardarlo
    """
    if created and instance.archivo and not instance.hash_archivo:
        try:
            # Leer archivo y generar hash
            with instance.archivo.open('rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                
                instance.hash_archivo = file_hash.hexdigest()
                instance.save(update_fields=['hash_archivo'])
                
        except Exception as e:
            print(f"Error generando hash para {instance.nombre_original}: {e}")

@receiver(pre_delete, sender=ArchivoAudio)
def verificar_archivos_en_uso(sender, instance, **kwargs):
    """
    Verifica que el archivo no esté siendo usado antes de eliminarlo
    """
    if instance.cuñas.exists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied(
            f"No se puede eliminar el archivo '{instance.nombre_original}' "
            f"porque está siendo usado en {instance.cuñas.count()} cuña(s)."
        )

@receiver(post_delete, sender=ArchivoAudio)
def eliminar_archivo_fisico(sender, instance, **kwargs):
    """
    Elimina el archivo físico cuando se elimina el registro de la base de datos
    """
    if instance.archivo:
        try:
            if os.path.isfile(instance.archivo.path):
                os.remove(instance.archivo.path)
        except Exception as e:
            print(f"Error eliminando archivo físico {instance.archivo.path}: {e}")

# ==================== SEÑALES DE CUÑAS PUBLICITARIAS ====================

@receiver(post_save, sender=CuñaPublicitaria)
def crear_cuenta_por_cobrar(sender, instance, created, **kwargs):
    """
    Crea automáticamente cuenta por cobrar cuando se aprueba una cuña
    """
    if not created and instance.estado == 'aprobada':
        # Verificar si ya tiene cuenta por cobrar
        if not hasattr(instance, 'cuenta_por_cobrar'):
            try:
                from apps.financial_management.models import CuentaPorCobrar
                from datetime import timedelta
                
                # Generar número de factura
                año_mes = timezone.now().strftime('%Y%m')
                contador = CuentaPorCobrar.objects.filter(
                    numero_factura__startswith=f'FAC{año_mes}'
                ).count() + 1
                numero_factura = f'FAC{año_mes}{contador:04d}'
                
                # Crear cuenta por cobrar
                CuentaPorCobrar.objects.create(
                    cuña_publicitaria=instance,
                    numero_factura=numero_factura,
                    cliente=instance.cliente,
                    vendedor=instance.vendedor_asignado,
                    monto_total=instance.precio_total,
                    monto_pendiente=instance.precio_total,
                    fecha_emision=timezone.now().date(),
                    fecha_vencimiento=timezone.now().date() + timedelta(days=30),
                    dias_credito=30
                )
                
            except ImportError:
                # El módulo financiero aún no está disponible
                pass
            except Exception as e:
                print(f"Error creando cuenta por cobrar para cuña {instance.codigo}: {e}")

@receiver(post_save, sender=CuñaPublicitaria)
def calcular_comision_vendedor(sender, instance, created, **kwargs):
    """
    Calcula comisión del vendedor cuando se aprueba una cuña
    """
    if not created and instance.estado == 'aprobada' and instance.vendedor_asignado:
        try:
            from apps.sales_management.models import ComisionVendedor, TipoComision
            
            # Verificar si ya tiene comisión calculada
            if not ComisionVendedor.objects.filter(
                vendedor__user=instance.vendedor_asignado,
                cuña_publicitaria=instance
            ).exists():
                
                # Buscar tipo de comisión aplicable
                tipo_comision = TipoComision.objects.filter(
                    is_active=True,
                    monto_minimo__lte=instance.precio_total
                ).first()
                
                if tipo_comision:
                    # Calcular comisión
                    if tipo_comision.es_porcentaje:
                        monto_comision = instance.precio_total * (tipo_comision.valor / 100)
                    else:
                        monto_comision = tipo_comision.valor
                    
                    # Crear registro de comisión
                    ComisionVendedor.objects.create(
                        vendedor=instance.vendedor_asignado.perfil_vendedor,
                        cuña_publicitaria=instance,
                        tipo_comision=tipo_comision,
                        monto_venta=instance.precio_total,
                        porcentaje_aplicado=tipo_comision.valor if tipo_comision.es_porcentaje else 0,
                        monto_comision_base=monto_comision,
                        monto_final=monto_comision,
                        estado='calculada'
                    )
                    
        except ImportError:
            # El módulo de ventas aún no está disponible
            pass
        except Exception as e:
            print(f"Error calculando comisión para cuña {instance.codigo}: {e}")

@receiver(post_save, sender=CuñaPublicitaria)
def crear_programacion_transmision(sender, instance, created, **kwargs):
    """
    Crea programación automática cuando se activa una cuña
    """
    if not created and instance.estado == 'activa':
        try:
            from apps.transmission_control.models import ProgramacionTransmision, FranjaHoraria
            from datetime import datetime, time, timedelta
            
            # Verificar si ya tiene programaciones
            if not instance.programaciones.exists():
                
                # Obtener franja horaria por defecto (por ejemplo, mañana)
                franja = FranjaHoraria.objects.filter(
                    is_active=True,
                    tipo='mañana'
                ).first()
                
                if franja:
                    # Crear programaciones para cada día de la campaña
                    fecha_actual = instance.fecha_inicio
                    
                    while fecha_actual <= instance.fecha_fin:
                        # Verificar si la franja está activa para este día
                        if fecha_actual.weekday() + 1 in franja.dias_activos:
                            
                            # Crear programaciones según repeticiones por día
                            for i in range(instance.repeticiones_dia):
                                # Calcular hora basada en la franja y repetición
                                hora_base = franja.hora_inicio
                                minutos_intervalo = (franja.hora_fin.hour - franja.hora_inicio.hour) * 60 // instance.repeticiones_dia
                                hora_programada = time(
                                    hour=hora_base.hour,
                                    minute=hora_base.minute + (i * minutos_intervalo)
                                )
                                
                                ProgramacionTransmision.objects.create(
                                    cuña_publicitaria=instance,
                                    franja_horaria=franja,
                                    fecha_programada=fecha_actual,
                                    hora_programada=hora_programada,
                                    operador_programacion=instance.created_by,
                                    prioridad=2  # Normal
                                )
                        
                        fecha_actual += timedelta(days=1)
                        
        except ImportError:
            # El módulo de transmisión aún no está disponible
            pass
        except Exception as e:
            print(f"Error creando programaciones para cuña {instance.codigo}: {e}")

@receiver(post_save, sender=CuñaPublicitaria)
def crear_notificacion_vencimiento(sender, instance, **kwargs):
    """
    Programa notificación de vencimiento para cuñas activas
    """
    if instance.estado == 'activa' and instance.notificar_vencimiento:
        try:
            from apps.notifications.models import Notificacion, TipoNotificacion
            from datetime import timedelta
            
            # Buscar tipo de notificación de vencimiento
            tipo_notif = TipoNotificacion.objects.filter(
                codigo='CUÑA_VENCIMIENTO',
                is_active=True
            ).first()
            
            if tipo_notif:
                # Calcular fecha de notificación
                fecha_notificacion = instance.fecha_fin - timedelta(days=instance.dias_aviso_vencimiento)
                
                # Solo crear si la notificación es futura
                if fecha_notificacion > timezone.now().date():
                    
                    # Crear variables para el template
                    variables = {
                        'codigo_cuña': instance.codigo,
                        'titulo_cuña': instance.titulo,
                        'dias_restantes': instance.dias_aviso_vencimiento,
                        'fecha_fin': instance.fecha_fin.strftime('%d/%m/%Y'),
                        'cliente': instance.cliente.get_full_name(),
                    }
                    
                    titulo, mensaje = tipo_notif.generar_mensaje(variables)
                    
                    # Crear notificaciones para vendedor y cliente
                    usuarios_notificar = [instance.vendedor_asignado, instance.cliente]
                    
                    for usuario in usuarios_notificar:
                        if usuario:
                            Notificacion.objects.get_or_create(
                                tipo_notificacion=tipo_notif,
                                usuario=usuario,
                                objeto_relacionado=instance,
                                defaults={
                                    'titulo': titulo,
                                    'mensaje': mensaje,
                                    'fecha_programada': timezone.make_aware(
                                        datetime.combine(fecha_notificacion, time(9, 0))
                                    ),
                                    'prioridad': 'alta' if instance.dias_aviso_vencimiento <= 3 else 'normal',
                                    'canales': ['app', 'email']
                                }
                            )
                            
        except ImportError:
            # El módulo de notificaciones aún no está disponible
            pass
        except Exception as e:
            print(f"Error programando notificación para cuña {instance.codigo}: {e}")

# ==================== SEÑALES DE CATEGORIAS ====================

@receiver(pre_delete, sender=CategoriaPublicitaria)
def verificar_categoria_en_uso(sender, instance, **kwargs):
    """
    Verifica que la categoría no tenga cuñas asociadas antes de eliminar
    """
    if instance.cuñas.exists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied(
            f"No se puede eliminar la categoría '{instance.nombre}' "
            f"porque tiene {instance.cuñas.count()} cuña(s) asociada(s)."
        )

# ==================== SEÑALES DE USUARIO ====================

@receiver(post_save, sender=User)
def crear_preferencias_notificacion(sender, instance, created, **kwargs):
    """
    Crea preferencias de notificación por defecto para nuevos usuarios
    """
    if created:
        try:
            from apps.notifications.models import PreferenciasNotificacion
            
            # Crear preferencias por defecto
            PreferenciasNotificacion.objects.get_or_create(
                usuario=instance,
                defaults={
                    'notificaciones_habilitadas': True,
                    'app_habilitado': True,
                    'email_habilitado': True,
                    'sms_habilitado': False,
                    'push_habilitado': True,
                    'notif_financieras': True,
                    'notif_comerciales': True,
                    'notif_operativas': True,
                    'notif_tecnicas': False,
                    'notif_administrativas': True,
                    'notif_sistema': True,
                }
            )
            
        except ImportError:
            # El módulo de notificaciones aún no está disponible
            pass
        except Exception as e:
            print(f"Error creando preferencias para usuario {instance.username}: {e}")

# ==================== UTILIDADES DE SEÑALES ====================

def desconectar_señales():
    """
    Desconecta todas las señales definidas en este módulo
    Útil para tests o casos especiales
    """
    signals_to_disconnect = [
        (post_save, generar_hash_archivo, ArchivoAudio),
        (pre_delete, verificar_archivos_en_uso, ArchivoAudio),
        (post_delete, eliminar_archivo_fisico, ArchivoAudio),
        (post_save, crear_cuenta_por_cobrar, CuñaPublicitaria),
        (post_save, calcular_comision_vendedor, CuñaPublicitaria),
        (post_save, crear_programacion_transmision, CuñaPublicitaria),
        (post_save, crear_notificacion_vencimiento, CuñaPublicitaria),
        (post_save, actualizar_semaforo_cuña, CuñaPublicitaria),
        (pre_delete, verificar_categoria_en_uso, CategoriaPublicitaria),
        (post_save, crear_preferencias_notificacion, User),
    ]
    
    for signal, handler, sender in signals_to_disconnect:
        try:
            signal.disconnect(handler, sender=sender)
        except Exception as e:
            print(f"Error desconectando señal {handler.__name__}: {e}")

def reconectar_señales():
    """
    Reconecta todas las señales definidas en este módulo
    """
    # Las señales se reconectan automáticamente al importar este módulo
    # Esta función existe por consistencia en la API
    pass

def validar_integridad_archivos():
    """
    Valida la integridad de todos los archivos de audio
    Útil para tareas de mantenimiento
    """
    from .models import ArchivoAudio
    
    archivos_problema = []
    
    for archivo in ArchivoAudio.objects.all():
        try:
            # Verificar que el archivo físico existe
            if not os.path.isfile(archivo.archivo.path):
                archivos_problema.append({
                    'id': archivo.id,
                    'nombre': archivo.nombre_original,
                    'problema': 'Archivo físico no existe'
                })
                continue
            
            # Verificar hash si existe
            if archivo.hash_archivo:
                with archivo.archivo.open('rb') as f:
                    file_hash = hashlib.sha256()
                    for chunk in iter(lambda: f.read(4096), b""):
                        file_hash.update(chunk)
                    
                    if file_hash.hexdigest() != archivo.hash_archivo:
                        archivos_problema.append({
                            'id': archivo.id,
                            'nombre': archivo.nombre_original,
                            'problema': 'Hash no coincide - archivo modificado'
                        })
                        
        except Exception as e:
            archivos_problema.append({
                'id': archivo.id,
                'nombre': archivo.nombre_original,
                'problema': f'Error al validar: {str(e)}'
            })
    
    return archivos_problema

def regenerar_hashes_archivos():
    """
    Regenera los hashes de todos los archivos de audio
    Útil después de migración o problemas de integridad
    """
    from .models import ArchivoAudio
    
    archivos_procesados = 0
    archivos_error = []
    
    for archivo in ArchivoAudio.objects.filter(hash_archivo__isnull=True):
        try:
            if archivo.archivo and os.path.isfile(archivo.archivo.path):
                with archivo.archivo.open('rb') as f:
                    file_hash = hashlib.sha256()
                    for chunk in iter(lambda: f.read(4096), b""):
                        file_hash.update(chunk)
                    
                    archivo.hash_archivo = file_hash.hexdigest()
                    archivo.save(update_fields=['hash_archivo'])
                    archivos_procesados += 1
                    
        except Exception as e:
            archivos_error.append({
                'id': archivo.id,
                'nombre': archivo.nombre_original,
                'error': str(e)
            })
    
    return {
        'procesados': archivos_procesados,
        'errores': archivos_error
    }

def limpiar_archivos_huerfanos():
    """
    Elimina archivos físicos que no tienen registro en la base de datos
    ¡USAR CON PRECAUCIÓN!
    """
    from django.conf import settings
    
    if not hasattr(settings, 'MEDIA_ROOT'):
        return {'error': 'MEDIA_ROOT no configurado'}
    
    audio_path = os.path.join(settings.MEDIA_ROOT, 'audio_spots')
    
    if not os.path.exists(audio_path):
        return {'error': 'Directorio de audio no existe'}
    
    archivos_eliminados = []
    archivos_conservados = []
    
    # Obtener lista de archivos en base de datos
    from .models import ArchivoAudio
    archivos_db = set()
    
    for archivo in ArchivoAudio.objects.all():
        if archivo.archivo:
            archivos_db.add(os.path.basename(archivo.archivo.path))
    
    # Recorrer archivos físicos
    for root, dirs, files in os.walk(audio_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Verificar si el archivo está en la base de datos
            if file not in archivos_db:
                try:
                    os.remove(file_path)
                    archivos_eliminados.append(file)
                except Exception as e:
                    print(f"Error eliminando {file}: {e}")
            else:
                archivos_conservados.append(file)
    
    return {
        'eliminados': len(archivos_eliminados),
        'conservados': len(archivos_conservados),
        'archivos_eliminados': archivos_eliminados
    }