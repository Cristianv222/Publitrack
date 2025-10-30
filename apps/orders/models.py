"""
Modelos para el módulo de Órdenes de Toma
Sistema PubliTrack - Gestión de órdenes ligadas a clientes
"""

import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError


class OrdenToma(models.Model):
    """
    Orden de toma generada automáticamente al crear un cliente
    Similar a CuñaPublicitaria pero para órdenes de toma
    """
    
    ESTADO_CHOICES = [
        ('generado', 'Generado'),
        ('validado', 'Validado'),
        ('en_produccion', 'En Producción'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    # Código único
    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único de la orden (generado automáticamente)'
    )
    
    # Relación con cliente
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'cliente'},
        related_name='ordenes_toma',
        verbose_name='Cliente'
    )
    
    # Información del cliente copiada al momento de crear la orden
    nombre_cliente = models.CharField('Nombre del Cliente', max_length=255)
    ruc_dni_cliente = models.CharField('RUC/DNI del Cliente', max_length=20)
    empresa_cliente = models.CharField('Empresa', max_length=200, blank=True, null=True)
    ciudad_cliente = models.CharField('Ciudad', max_length=100, blank=True, null=True)
    direccion_cliente = models.TextField('Dirección', blank=True, null=True)
    telefono_cliente = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    email_cliente = models.EmailField('Email', blank=True, null=True)
    
    # Detalles de la orden
    detalle_productos = models.TextField(
        'Detalle de Productos/Servicios',
        help_text='Descripción de los productos o servicios solicitados'
    )
    
    cantidad = models.PositiveIntegerField(
        'Cantidad',
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    total = models.DecimalField(
        'Total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Monto total de la orden'
    )
    
    # Estado y prioridad
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='generado',
        help_text='Estado actual de la orden'
    )
    
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='normal',
        help_text='Prioridad de la orden'
    )
    
    # Observaciones
    observaciones = models.TextField(
        'Observaciones',
        blank=True,
        help_text='Observaciones adicionales sobre la orden'
    )
    
    # Vendedor asignado
    vendedor_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'rol': 'vendedor'},
        related_name='ordenes_vendidas',
        verbose_name='Vendedor Asignado'
    )
    
    # Fechas
    fecha_orden = models.DateTimeField(
        'Fecha de Orden',
        default=timezone.now
    )
    
    fecha_validacion = models.DateTimeField(
        'Fecha de Validación',
        null=True,
        blank=True
    )
    
    fecha_completado = models.DateTimeField(
        'Fecha de Completado',
        null=True,
        blank=True
    )
    
    # Usuario que valida/completa
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_validadas',
        verbose_name='Validado por'
    )
    
    completado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_completadas',
        verbose_name='Completado por'
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordenes_creadas',
        verbose_name='Creada por'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Orden de Toma'
        verbose_name_plural = 'Órdenes de Toma'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estado', 'fecha_orden']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['vendedor_asignado', 'estado']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre_cliente}"
    
    def save(self, *args, **kwargs):
        """Override save para generar código automáticamente"""
        if not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Copiar información del cliente si no está presente
        if self.cliente and not self.nombre_cliente:
            self.copiar_datos_cliente()
        
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        """Genera un código único para la orden"""
        año = timezone.now().year
        mes = timezone.now().month
        
        count = OrdenToma.objects.filter(
            created_at__year=año,
            created_at__month=mes
        ).count() + 1
        
        return f"OT{año}{mes:02d}{count:04d}"
    
    def copiar_datos_cliente(self):
        """Copia los datos del cliente a la orden"""
        if self.cliente:
            self.nombre_cliente = self.cliente.get_full_name() or self.cliente.username
            self.ruc_dni_cliente = self.cliente.ruc_dni or ''
            self.empresa_cliente = self.cliente.empresa or ''
            self.ciudad_cliente = self.cliente.ciudad or ''
            self.direccion_cliente = self.cliente.direccion_exacta or self.cliente.direccion or ''
            self.telefono_cliente = self.cliente.telefono or ''
            self.email_cliente = self.cliente.email or ''
            self.vendedor_asignado = self.cliente.vendedor_asignado
    
    def validar(self, user):
        """Valida la orden y cambia estado a validado"""
        self.estado = 'validado'
        self.validado_por = user
        self.fecha_validacion = timezone.now()
        self.save()
    
    def enviar_a_produccion(self):
        """Cambia el estado a en producción"""
        if self.estado == 'validado':
            self.estado = 'en_produccion'
            self.save()
    
    def completar(self, user):
        """Completa la orden"""
        self.estado = 'completado'
        self.completado_por = user
        self.fecha_completado = timezone.now()
        self.save()
    
    def cancelar(self):
        """Cancela la orden"""
        self.estado = 'cancelado'
        self.save()
    
    def get_absolute_url(self):
        return reverse('custom_admin:order_detail_api', kwargs={'order_id': self.pk})
    
    @property
    def dias_desde_creacion(self):
        """Calcula los días desde la creación"""
        return (timezone.now() - self.created_at).days
    
    @property
    def semaforo_estado(self):
        """Determina color de semáforo basado en estado y tiempo"""
        if self.estado == 'completado':
            return 'verde'
        elif self.estado == 'cancelado':
            return 'gris'
        elif self.dias_desde_creacion > 7:
            return 'rojo'
        elif self.dias_desde_creacion > 3:
            return 'amarillo'
        else:
            return 'verde'


class HistorialOrden(models.Model):
    """
    Historial de cambios de las órdenes de toma
    """
    
    ACCION_CHOICES = [
        ('creada', 'Creada'),
        ('editada', 'Editada'),
        ('validada', 'Validada'),
        ('produccion', 'Enviada a Producción'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    orden = models.ForeignKey(
        OrdenToma,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Orden'
    )
    
    accion = models.CharField(
        'Acción',
        max_length=20,
        choices=ACCION_CHOICES
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Usuario'
    )
    
    descripcion = models.TextField(
        'Descripción',
        help_text='Descripción detallada del cambio realizado'
    )
    
    datos_anteriores = models.JSONField(
        'Datos Anteriores',
        null=True,
        blank=True,
        help_text='Estado anterior de los campos modificados'
    )
    
    datos_nuevos = models.JSONField(
        'Datos Nuevos',
        null=True,
        blank=True,
        help_text='Nuevo estado de los campos modificados'
    )
    
    fecha = models.DateTimeField('Fecha', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Historial de Orden'
        verbose_name_plural = 'Historial de Órdenes'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.orden.codigo} - {self.get_accion_display()} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


# ==================== SEÑALES ====================

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_orden_toma_al_crear_cliente(sender, instance, created, **kwargs):
    """
    Señal que crea automáticamente una OrdenToma cuando se crea un cliente
    """
    if created and instance.rol == 'cliente':
        # Crear la orden de toma automáticamente
        orden = OrdenToma.objects.create(
            cliente=instance,
            detalle_productos=f'Orden de toma automática para {instance.get_full_name()}',
            cantidad=1,
            total=Decimal('0.00'),
            created_by=instance,
        )
        
        # Registrar en historial
        HistorialOrden.objects.create(
            orden=orden,
            accion='creada',
            usuario=instance,
            descripcion=f'Orden de toma creada automáticamente al registrar cliente',
            datos_nuevos={
                'codigo': orden.codigo,
                'cliente': instance.get_full_name(),
                'estado': orden.estado,
            }
        )


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
