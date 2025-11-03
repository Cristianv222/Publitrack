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
        ('pendiente', 'Pendiente'),
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
        default='pendiente',
        help_text='Estado actual de la orden'
    )
    
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='normal',
        help_text='Prioridad de la orden'
    )
    
    # Campos adicionales para completar la toma
    proyecto_campania = models.CharField(
        'Proyecto/Campaña',
        max_length=255,
        blank=True,
        null=True,
        help_text='Nombre del proyecto o campaña'
    )
    
    titulo_material = models.CharField(
        'Título del Material',
        max_length=255,
        blank=True,
        null=True,
        help_text='Título del material a producir'
    )
    
    descripcion_breve = models.TextField(
        'Descripción Breve',
        blank=True,
        null=True,
        help_text='Descripción breve del trabajo a realizar'
    )
    
    locaciones = models.TextField(
        'Locaciones',
        blank=True,
        null=True,
        help_text='Locaciones donde se realizará la toma'
    )
    
    fecha_produccion_inicio = models.DateField(
        'Fecha Inicio Producción',
        blank=True,
        null=True
    )
    
    fecha_produccion_fin = models.DateField(
        'Fecha Fin Producción',
        blank=True,
        null=True
    )
    
    hora_inicio = models.TimeField(
        'Hora Inicio',
        blank=True,
        null=True
    )
    
    hora_fin = models.TimeField(
        'Hora Fin',
        blank=True,
        null=True
    )
    
    equipo_asignado = models.TextField(
        'Equipo Asignado',
        blank=True,
        null=True,
        help_text='Equipo técnico asignado para la producción'
    )
    
    recursos_necesarios = models.TextField(
        'Recursos Necesarios',
        blank=True,
        null=True,
        help_text='Recursos adicionales necesarios'
    )
    
    observaciones_completado = models.TextField(
        'Observaciones de Completado',
        blank=True,
        null=True,
        help_text='Observaciones al completar la toma'
    )
    
    # Observaciones generales
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
        """Método save corregido para evitar bucles infinitos"""
        # Si es nuevo y no tiene código, generar uno
        if not self.pk and not self.codigo:
            self.codigo = self.generar_codigo()
    
        # ✅ COPIAR INFORMACIÓN DEL CLIENTE SIEMPRE QUE HAYA CLIENTE
        if self.cliente:
            self.copiar_datos_cliente()
    
        # Llamar al save original una sola vez
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        """Genera código único basado en el próximo ID"""
        try:
            # Obtener el último ID para generar el siguiente
            ultima_orden = OrdenToma.objects.order_by('-id').first()
            if ultima_orden:
                siguiente_numero = ultima_orden.id + 1
            else:
                siguiente_numero = 1
            
            return f"OT{siguiente_numero:06d}"
        except Exception:
            # Fallback si hay algún error
            import time
            return f"OT{int(time.time())}"
    
    def copiar_datos_cliente(self):
        if self.cliente:
            print(f"📋 Copiando datos del cliente: {self.cliente.username}")
        
            # Información personal
            self.nombre_cliente = self.cliente.get_full_name() or self.cliente.username
            self.ruc_dni_cliente = self.cliente.ruc_dni or ''
            self.empresa_cliente = self.cliente.empresa or ''
        
        # Información de contacto y ubicación
            self.ciudad_cliente = self.cliente.ciudad or ''
            self.direccion_cliente = self.cliente.direccion_exacta or self.cliente.direccion or ''
            self.telefono_cliente = self.cliente.telefono or ''
            self.email_cliente = self.cliente.email or ''
        
        # Vendedor asignado
            self.vendedor_asignado = self.cliente.vendedor_asignado
        
            print(f"✅ Datos copiados: {self.nombre_cliente} - {self.empresa_cliente} - {self.ruc_dni_cliente}")
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
    
    def completar(self, user, datos_produccion=None):
        self.estado = 'completado'
        self.completado_por = user
        self.fecha_completado = timezone.now()
    
        # ✅ GUARDAR DATOS DE PRODUCCIÓN SI SE PROVEEN
        if datos_produccion:
            self.proyecto_campania = datos_produccion.get('proyecto_campania', self.proyecto_campania)
            self.titulo_material = datos_produccion.get('titulo_material', self.titulo_material)
            self.descripcion_breve = datos_produccion.get('descripcion_breve', self.descripcion_breve)
            self.locaciones = datos_produccion.get('locaciones', self.locaciones)
            self.fecha_produccion_inicio = datos_produccion.get('fecha_produccion_inicio', self.fecha_produccion_inicio)
            self.fecha_produccion_fin = datos_produccion.get('fecha_produccion_fin', self.fecha_produccion_fin)
            self.hora_inicio = datos_produccion.get('hora_inicio', self.hora_inicio)
            self.hora_fin = datos_produccion.get('hora_fin', self.hora_fin)
            self.equipo_asignado = datos_produccion.get('equipo_asignado', self.equipo_asignado)
            self.recursos_necesarios = datos_produccion.get('recursos_necesarios', self.recursos_necesarios)
            self.observaciones_completado = datos_produccion.get('observaciones_completado', self.observaciones_completado)
    
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