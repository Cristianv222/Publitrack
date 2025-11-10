"""
Modelos para el módulo de Órdenes de Toma
Sistema PubliTrack - Gestión de órdenes ligadas a clientes
"""
import os 
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.authentication.models import CustomUser
from django.core.validators import FileExtensionValidator 

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
    
        # ✅ CORREGIDO: Siempre copiar datos del cliente si hay un cliente asignado
        # y la orden es nueva (no tiene PK) o no tiene datos del cliente
        if self.cliente and (not self.pk or not self.nombre_cliente or self.nombre_cliente.strip() == ''):
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
        """Copia los datos del cliente a la orden - VERSIÓN CORREGIDA"""
        if self.cliente:
            print(f"🔍 COPIANDO DATOS DEL CLIENTE:")
            print(f"   - Orden ID: {self.id if self.id else 'Nueva'}")
            print(f"   - Cliente ID: {self.cliente.id}")
            print(f"   - Cliente username: {self.cliente.username}")
        
            try:
                # ✅ AHORA CustomUser ESTÁ IMPORTADO
                cliente_fresco = CustomUser.objects.get(pk=self.cliente.pk)
                print(f"   - Cliente datos en BD:")
                print(f"     * Nombre completo: '{cliente_fresco.get_full_name()}'")
                print(f"     * RUC/DNI: '{cliente_fresco.ruc_dni}'")
                print(f"     * Empresa: '{cliente_fresco.empresa}'")
                print(f"     * Ciudad: '{cliente_fresco.ciudad}'")
                print(f"     * Dirección: '{cliente_fresco.direccion_exacta}'")
                print(f"     * Teléfono: '{cliente_fresco.telefono}'")
                print(f"     * Email: '{cliente_fresco.email}'")
            
            # Usar los datos frescos del cliente
                self.nombre_cliente = cliente_fresco.get_full_name() or cliente_fresco.username or 'N/A'
                self.ruc_dni_cliente = cliente_fresco.ruc_dni or 'N/A'
                self.empresa_cliente = cliente_fresco.empresa or 'N/A'
                self.ciudad_cliente = cliente_fresco.ciudad or 'N/A'
                self.direccion_cliente = cliente_fresco.direccion_exacta or cliente_fresco.direccion or 'N/A'
                self.telefono_cliente = cliente_fresco.telefono or 'N/A'
                self.email_cliente = cliente_fresco.email or 'N/A'
                self.vendedor_asignado = cliente_fresco.vendedor_asignado
            
                print(f"✅ DATOS COPIADOS A LA ORDEN:")
                print(f"   - Nombre: '{self.nombre_cliente}'")
                print(f"   - RUC/DNI: '{self.ruc_dni_cliente}'")
                print(f"   - Empresa: '{self.empresa_cliente}'")
                print(f"   - Ciudad: '{self.ciudad_cliente}'")
                print(f"   - Dirección: '{self.direccion_cliente}'")
                print(f"   - Teléfono: '{self.telefono_cliente}'")
            
            except CustomUser.DoesNotExist:
                print(f"❌ Cliente no encontrado en BD: {self.cliente.pk}")
                # Usar datos del objeto en memoria como fallback
                self.nombre_cliente = self.cliente.get_full_name() or self.cliente.username or 'N/A'
                self.ruc_dni_cliente = self.cliente.ruc_dni or 'N/A'
                self.empresa_cliente = self.cliente.empresa or 'N/A'
                self.ciudad_cliente = self.cliente.ciudad or 'N/A'
                self.direccion_cliente = self.cliente.direccion_exacta or self.cliente.direccion or 'N/A'
                self.telefono_cliente = self.cliente.telefono or 'N/A'
                self.email_cliente = self.cliente.email or 'N/A'
                self.vendedor_asignado = self.cliente.vendedor_asignado
        else:
            print("❌ No hay cliente asignado para copiar datos")
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

    def generar_orden_impresion(self, plantilla_id=None, user=None):
        """Genera una orden para imprimir similar a los contratos"""
        # Obtener plantilla
        if plantilla_id:
            plantilla = PlantillaOrden.objects.get(id=plantilla_id)
        else:
            plantilla = PlantillaOrden.objects.filter(
                is_default=True, is_active=True
            ).first()
            if not plantilla:
                plantilla = PlantillaOrden.objects.filter(is_active=True).first()
        
        if not plantilla:
            raise ValueError("No hay plantillas de orden disponibles")
        
        # Crear orden generada
        orden_generada = OrdenGenerada.objects.create(
            orden_toma=self,
            plantilla_usada=plantilla,
            generado_por=user or self.created_by,
            estado='borrador'
        )
        
        # Generar el PDF
        if orden_generada.generar_orden_pdf():
            return orden_generada
        else:
            orden_generada.delete()
            raise ValueError("Error al generar la orden PDF")
    
    def completar_y_generar_orden(self, user, datos_completado):
        """Completa la orden y genera la orden para imprimir"""
        # Actualizar campos de completado
        self.proyecto_campania = datos_completado.get('proyecto_campania')
        self.titulo_material = datos_completado.get('titulo_material')
        self.descripcion_breve = datos_completado.get('descripcion_breve')
        self.locaciones = datos_completado.get('locaciones')
        self.fecha_produccion_inicio = datos_completado.get('fecha_produccion_inicio')
        self.fecha_produccion_fin = datos_completado.get('fecha_produccion_fin')
        self.hora_inicio = datos_completado.get('hora_inicio')
        self.hora_fin = datos_completado.get('hora_fin')
        self.equipo_asignado = datos_completado.get('equipo_asignado')
        self.recursos_necesarios = datos_completado.get('recursos_necesarios')
        self.observaciones_completado = datos_completado.get('observaciones_completado')
        
        # Cambiar estado a completado
        self.estado = 'completado'
        self.completado_por = user
        self.fecha_completado = timezone.now()
        self.save()
        
        # Generar orden para imprimir
        return self.generar_orden_impresion(user=user)


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

# ==================== FUNCIONES PARA ÓRDENES ====================

def orden_template_path(instance, filename):
    """Genera la ruta de subida para plantillas de orden"""
    ext = filename.split('.')[-1].lower()
    unique_filename = f"template_orden_{uuid.uuid4().hex}.{ext}"
    return f"orden_templates/{unique_filename}"

def orden_output_path(instance, filename):
    """Genera la ruta para órdenes PDF generadas"""
    ext = filename.split('.')[-1].lower()
    unique_filename = f"orden_{instance.numero_orden}_{uuid.uuid4().hex[:8]}.{ext}"
    return f"staticfiles/ordenes/{unique_filename}"

def orden_validada_path(instance, filename):
    """Ruta para órdenes validadas subidas"""
    ext = filename.split('.')[-1].lower()
    base = f"orden_validada_{instance.numero_orden}_{instance.id if instance.id else 'tmp'}.{ext}"
    return os.path.join('ordenes_validadas', base)

# ==================== MODELOS DE PLANTILLAS DE ORDEN ====================

class PlantillaOrden(models.Model):
    """
    Plantillas para órdenes de toma en formato Word
    """
    
    TIPO_ORDEN_CHOICES = [
        ('toma_video', 'Toma de Video'),
        ('produccion_audio', 'Producción de Audio'),
        ('edicion_video', 'Edición de Video'),
        ('produccion_completa', 'Producción Completa'),
        ('otro', 'Otro'),
    ]
    
    nombre = models.CharField(
        'Nombre de la Plantilla',
        max_length=200,
        help_text='Nombre descriptivo (ej: Orden Toma Video 2025)'
    )
    
    tipo_orden = models.CharField(
        'Tipo de Orden',
        max_length=50,
        choices=TIPO_ORDEN_CHOICES,
        default='toma_video',
        help_text='Tipo de orden que representa esta plantilla'
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción de cuándo usar esta plantilla'
    )
    
    archivo_plantilla = models.FileField(
        'Archivo de Plantilla (.docx)',
        upload_to=orden_template_path,
        validators=[FileExtensionValidator(allowed_extensions=['docx'])],
        help_text='Archivo Word con marcadores: {{NOMBRE_CLIENTE}}, {{RUC_DNI}}, etc.'
    )
    
    variables_disponibles = models.JSONField(
        'Variables Disponibles',
        default=dict,
        blank=True,
        help_text='Variables que se reemplazan en la plantilla'
    )
    
    instrucciones = models.TextField(
        'Instrucciones de Uso',
        blank=True,
        help_text='Instrucciones sobre cómo usar esta plantilla'
    )
    
    version = models.CharField(
        'Versión',
        max_length=20,
        default='1.0',
        help_text='Versión de la plantilla'
    )
    
    is_active = models.BooleanField(
        'Activa',
        default=True,
        help_text='Si la plantilla está activa'
    )
    
    is_default = models.BooleanField(
        'Plantilla por Defecto',
        default=False,
        help_text='Si es la plantilla predeterminada'
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='plantillas_orden_creadas',
        verbose_name='Creada por'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Plantilla de Orden'
        verbose_name_plural = 'Plantillas de Orden'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.nombre} (v{self.version})"
    
    def save(self, *args, **kwargs):
        """Override save para generar variables disponibles"""
        if not self.variables_disponibles:
            self.variables_disponibles = {
                'NUMERO_ORDEN': 'Número único de la orden',
                'NOMBRE_CLIENTE': 'Nombre o Razón Social del Cliente',
                'RUC_DNI': 'RUC o Cédula del Cliente',
                'EMPRESA_CLIENTE': 'Empresa del Cliente',
                'CIUDAD_CLIENTE': 'Ciudad del Cliente',
                'DIRECCION_CLIENTE': 'Dirección del Cliente',
                'TELEFONO_CLIENTE': 'Teléfono del Cliente',
                'EMAIL_CLIENTE': 'Email del Cliente',
                'DETALLE_PRODUCTOS': 'Detalle de productos/servicios',
                'CANTIDAD': 'Cantidad',
                'TOTAL_NUMEROS': 'Total en números',
                'TOTAL_LETRAS': 'Total en letras',
                'PROYECTO_CAMPANIA': 'Proyecto/Campaña',
                'TITULO_MATERIAL': 'Título del Material',
                'DESCRIPCION_BREVE': 'Descripción breve del trabajo',
                'LOCACIONES': 'Locaciones de producción',
                'FECHA_INICIO_PRODUCCION': 'Fecha inicio producción',
                'FECHA_FIN_PRODUCCION': 'Fecha fin producción',
                'HORA_INICIO': 'Hora de inicio',
                'HORA_FIN': 'Hora de fin',
                'EQUIPO_ASIGNADO': 'Equipo asignado',
                'RECURSOS_NECESARIOS': 'Recursos necesarios',
                'OBSERVACIONES_COMPLETADO': 'Observaciones al completar',
                'FECHA_ORDEN': 'Fecha de la orden',
                'FECHA_ACTUAL': 'Fecha actual de generación',
            }
        
        # Si se marca como default, desmarcar las demás
        if self.is_default:
            PlantillaOrden.objects.filter(
                tipo_orden=self.tipo_orden,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('orders:plantilla_orden_detail', kwargs={'pk': self.pk})


class OrdenGenerada(models.Model):
    """
    Órdenes generadas a partir de plantillas
    """
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('generada', 'Generada'),
        ('impresa', 'Impresa'),
        ('validada', 'Validada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    numero_orden = models.CharField('Número de Orden', max_length=50, unique=True)
    orden_toma = models.ForeignKey(
        'OrdenToma', 
        on_delete=models.CASCADE, 
        related_name='ordenes_generadas',
        verbose_name='Orden de Toma'
    )
    plantilla_usada = models.ForeignKey(
        'PlantillaOrden', on_delete=models.SET_NULL, null=True,
        related_name='ordenes_generadas', verbose_name='Plantilla Utilizada'
    )
    
    # Archivos
    archivo_orden_pdf = models.FileField(
        'Orden en PDF', upload_to=orden_output_path, blank=True, null=True
    )
    archivo_orden_validada = models.FileField(
        'Orden Validada (Subida)',
        upload_to=orden_validada_path,
        blank=True, null=True,
        help_text='PDF subido manualmente después de validar'
    )
    orden_produccion = models.ForeignKey(
        'OrdenProduccion',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ordenes_generadas_produccion',  # Diferente related_name
        verbose_name='Orden de Producción'
    )
    # Estado
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='borrador')
    datos_generacion = models.JSONField('Datos de Generación', default=dict)
    
    # Fechas
    fecha_generacion = models.DateTimeField('Fecha de Generación', auto_now_add=True)
    fecha_impresion = models.DateTimeField('Fecha de Impresión', null=True, blank=True)
    fecha_validacion = models.DateTimeField('Fecha de Validación', null=True, blank=True)
    
    # Usuarios
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='ordenes_generadas_por', verbose_name='Generado por'
    )
    impreso_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ordenes_impresas_por', verbose_name='Impreso por'
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ordenes_validadas_por', verbose_name='Validado por'
    )
    
    observaciones = models.TextField('Observaciones', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Orden Generada'
        verbose_name_plural = 'Órdenes Generadas'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"Orden {self.numero_orden} - {self.orden_toma.nombre_cliente}"

    def save(self, *args, **kwargs):
        if not self.numero_orden:
            self.numero_orden = self.generar_numero_orden()
        super().save(*args, **kwargs)

    def generar_numero_orden(self):
        año = timezone.now().year
        mes = timezone.now().month
        for intento in range(1, 100):
            count = OrdenGenerada.objects.filter(
                fecha_generacion__year=año,
                fecha_generacion__month=mes
            ).count() + intento
            numero = f"ORD{año}{mes:02d}{count:04d}"
            if not OrdenGenerada.objects.filter(numero_orden=numero).exists():
                return numero
        raise Exception("No se pudo generar un número de orden único")

    def generar_orden_pdf(self):
        """Genera el PDF de la orden - VERSIÓN CORREGIDA"""
        try:
            from docxtpl import DocxTemplate
            from io import BytesIO
            import os
            import subprocess
            from django.core.files.base import ContentFile
            import tempfile

            if not self.plantilla_usada or not self.plantilla_usada.archivo_plantilla:
                raise ValueError("No hay plantilla asignada o la plantilla no tiene archivo")

            # Verificar que el archivo de plantilla existe
            if not os.path.exists(self.plantilla_usada.archivo_plantilla.path):
                raise ValueError("El archivo de plantilla no existe en la ruta especificada")

            print(f"📄 Usando plantilla: {self.plantilla_usada.archivo_plantilla.path}")

            # Cargar plantilla
            doc = DocxTemplate(self.plantilla_usada.archivo_plantilla.path)
            orden_toma = self.orden_toma

            # Preparar contexto con valores por defecto
            context = {
                'NUMERO_ORDEN': self.numero_orden,
                'NOMBRE_CLIENTE': orden_toma.nombre_cliente or '',
                'RUC_DNI': orden_toma.ruc_dni_cliente or '',
                'EMPRESA_CLIENTE': orden_toma.empresa_cliente or '',
                'CIUDAD_CLIENTE': orden_toma.ciudad_cliente or '',
                'DIRECCION_CLIENTE': orden_toma.direccion_cliente or '',
                'TELEFONO_CLIENTE': orden_toma.telefono_cliente or '',
                'EMAIL_CLIENTE': orden_toma.email_cliente or '',
                'DETALLE_PRODUCTOS': orden_toma.detalle_productos or '',
                'CANTIDAD': str(orden_toma.cantidad),
                'TOTAL_NUMEROS': f"{orden_toma.total:.2f}",
                'TOTAL_LETRAS': numero_a_letras(orden_toma.total),
                'PROYECTO_CAMPANIA': orden_toma.proyecto_campania or '',
                'TITULO_MATERIAL': orden_toma.titulo_material or '',
                'DESCRIPCION_BREVE': orden_toma.descripcion_breve or '',
                'LOCACIONES': orden_toma.locaciones or '',
                'FECHA_INICIO_PRODUCCION': orden_toma.fecha_produccion_inicio.strftime('%d de %B del %Y') if orden_toma.fecha_produccion_inicio else '',
                'FECHA_FIN_PRODUCCION': orden_toma.fecha_produccion_fin.strftime('%d de %B del %Y') if orden_toma.fecha_produccion_fin else '',
                'HORA_INICIO': orden_toma.hora_inicio.strftime('%H:%M') if orden_toma.hora_inicio else '',
                'HORA_FIN': orden_toma.hora_fin.strftime('%H:%M') if orden_toma.hora_fin else '',
                'EQUIPO_ASIGNADO': orden_toma.equipo_asignado or '',
                'RECURSOS_NECESARIOS': orden_toma.recursos_necesarios or '',
                'OBSERVACIONES_COMPLETADO': orden_toma.observaciones_completado or '',
                'FECHA_ORDEN': orden_toma.fecha_orden.strftime('%d de %B del %Y') if orden_toma.fecha_orden else '',
                'FECHA_ACTUAL': timezone.now().strftime('%d de %B del %Y'),
            }

            print(f"📋 Contexto preparado para {self.numero_orden}")

            # Guardar datos de generación
            self.datos_generacion = context
            self.save()

            # Renderizar documento
            doc.render(context)
            
            # Guardar temporalmente el documento Word
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_docx:
                doc.save(tmp_docx.name)
                temp_docx_path = tmp_docx.name

            print(f"💾 DOCX guardado en: {temp_docx_path}")

            # Convertir a PDF usando LibreOffice
            temp_pdf_path = temp_docx_path.replace('.docx', '.pdf')
            
            try:
                # Intentar conversión con LibreOffice
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', os.path.dirname(temp_docx_path),
                    temp_docx_path
                ]
                
                print(f"🔄 Ejecutando: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    print(f"❌ Error en LibreOffice: {result.stderr}")
                    raise Exception(f"Error en conversión PDF: {result.stderr}")
                    
                print(f"✅ PDF generado en: {temp_pdf_path}")

            except Exception as e:
                print(f"❌ Error en conversión: {e}")
                # Fallback: si no hay LibreOffice, guardar el DOCX directamente
                temp_pdf_path = temp_docx_path
                print("⚠️ Usando DOCX como fallback")

            # Leer el archivo generado y guardarlo en el modelo
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                pdf_filename = f"orden_{self.numero_orden}.pdf"
                self.archivo_orden_pdf.save(pdf_filename, ContentFile(pdf_content), save=False)

            # Limpiar archivos temporales
            try:
                if os.path.exists(temp_docx_path):
                    os.remove(temp_docx_path)
                if temp_pdf_path != temp_docx_path and os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
            except Exception as e:
                print(f"⚠️ Error limpiando temporales: {e}")

            self.estado = 'generada'
            self.save()
            
            print(f"✅ Orden PDF generada exitosamente: {self.archivo_orden_pdf.url}")
            return True

        except Exception as e:
            print(f'❌ Error generando orden PDF: {str(e)}')
            import traceback
            print(f'📋 Traceback: {traceback.format_exc()}')
            return False
    def generar_orden_produccion_pdf(self):
        """Genera el PDF de la orden de producción - VERSIÓN PARA PRODUCCIÓN"""
        try:
            from docxtpl import DocxTemplate
            from io import BytesIO
            import os
            import subprocess
            from django.core.files.base import ContentFile
            import tempfile

            if not self.plantilla_usada or not self.plantilla_usada.archivo_plantilla:
                raise ValueError("No hay plantilla asignada o la plantilla no tiene archivo")

            # Verificar que el archivo de plantilla existe
            if not os.path.exists(self.plantilla_usada.archivo_plantilla.path):
                raise ValueError("El archivo de plantilla no existe en la ruta especificada")

            print(f"📄 Usando plantilla para producción: {self.plantilla_usada.archivo_plantilla.path}")

            # Cargar plantilla
            doc = DocxTemplate(self.plantilla_usada.archivo_plantilla.path)
            orden_produccion = self.orden_produccion

            # Preparar contexto específico para producción
            context = {
                'NUMERO_ORDEN': self.numero_orden,
                'CODIGO_PRODUCCION': orden_produccion.codigo,
                'CODIGO_TOMA': orden_produccion.orden_toma.codigo,
                'NOMBRE_CLIENTE': orden_produccion.nombre_cliente or '',
                'RUC_DNI': orden_produccion.ruc_dni_cliente or '',
                'EMPRESA_CLIENTE': orden_produccion.empresa_cliente or '',
                'PROYECTO_CAMPANIA': orden_produccion.proyecto_campania or '',
                'TITULO_MATERIAL': orden_produccion.titulo_material or '',
                'DESCRIPCION_BREVE': orden_produccion.descripcion_breve or '',
                'TIPO_PRODUCCION': orden_produccion.get_tipo_produccion_display(),
                'ESPECIFICACIONES_TECNICAS': orden_produccion.especificaciones_tecnicas or '',
                'FECHA_INICIO_PLANEADA': orden_produccion.fecha_inicio_planeada.strftime('%d de %B del %Y') if orden_produccion.fecha_inicio_planeada else '',
                'FECHA_FIN_PLANEADA': orden_produccion.fecha_fin_planeada.strftime('%d de %B del %Y') if orden_produccion.fecha_fin_planeada else '',
                'FECHA_INICIO_REAL': orden_produccion.fecha_inicio_real.strftime('%d de %B del %Y') if orden_produccion.fecha_inicio_real else '',
                'FECHA_FIN_REAL': orden_produccion.fecha_fin_real.strftime('%d de %B del %Y') if orden_produccion.fecha_fin_real else '',
                'EQUIPO_ASIGNADO': orden_produccion.equipo_asignado or '',
                'RECURSOS_NECESARIOS': orden_produccion.recursos_necesarios or '',
                'ARCHIVOS_ENTREGABLES': orden_produccion.archivos_entregables or '',
                'OBSERVACIONES_PRODUCCION': orden_produccion.observaciones_produccion or '',
                'PRIORIDAD': orden_produccion.get_prioridad_display(),
                'ESTADO': orden_produccion.get_estado_display(),
                'PRODUCTOR_ASIGNADO': orden_produccion.productor_asignado.get_full_name() if orden_produccion.productor_asignado else '',
                'FECHA_ACTUAL': timezone.now().strftime('%d de %B del %Y'),
            }

            print(f"📋 Contexto preparado para orden producción {self.numero_orden}")

            # Guardar datos de generación
            self.datos_generacion = context
            self.save()

            # Renderizar documento
            doc.render(context)
            
            # Guardar temporalmente el documento Word
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_docx:
                doc.save(tmp_docx.name)
                temp_docx_path = tmp_docx.name

            print(f"💾 DOCX guardado en: {temp_docx_path}")

            # Convertir a PDF usando LibreOffice
            temp_pdf_path = temp_docx_path.replace('.docx', '.pdf')
            
            try:
                # Intentar conversión con LibreOffice
                cmd = [
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', os.path.dirname(temp_docx_path),
                    temp_docx_path
                ]
                
                print(f"🔄 Ejecutando: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    print(f"❌ Error en LibreOffice: {result.stderr}")
                    raise Exception(f"Error en conversión PDF: {result.stderr}")
                    
                print(f"✅ PDF generado en: {temp_pdf_path}")

            except Exception as e:
                print(f"❌ Error en conversión: {e}")
                # Fallback: si no hay LibreOffice, guardar el DOCX directamente
                temp_pdf_path = temp_docx_path
                print("⚠️ Usando DOCX como fallback")

            # Leer el archivo generado y guardarlo en el modelo
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                pdf_filename = f"orden_produccion_{self.numero_orden}.pdf"
                self.archivo_orden_pdf.save(pdf_filename, ContentFile(pdf_content), save=False)

            # Limpiar archivos temporales
            try:
                if os.path.exists(temp_docx_path):
                    os.remove(temp_docx_path)
                if temp_pdf_path != temp_docx_path and os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
            except Exception as e:
                print(f"⚠️ Error limpiando temporales: {e}")

            self.estado = 'generada'
            self.save()
            
            print(f"✅ Orden PDF de producción generada exitosamente: {self.archivo_orden_pdf.url}")
            return True

        except Exception as e:
            print(f'❌ Error generando orden PDF de producción: {str(e)}')
            import traceback
            print(f'📋 Traceback: {traceback.format_exc()}')
            return False

    def marcar_como_impresa(self, user):
        self.estado = 'impresa'
        self.impreso_por = user
        self.fecha_impresion = timezone.now()
        self.save()

       
    def marcar_como_validada(self, user, archivo_validado=None):
        """Marca la orden como validada - VERSIÓN COMPLETA"""
        self.estado = 'validada'
        self.validado_por = user
        self.fecha_validacion = timezone.now()
        
        if archivo_validado:
            self.archivo_orden_validada = archivo_validado
        
        self.save()
        
        # ✅ ACTUALIZAR TAMBIÉN EL ESTADO DE LA ORDEN DE TOMA RELACIONADA
        if self.orden_toma and self.orden_toma.estado != 'validado':
            self.orden_toma.estado = 'validado'
            self.orden_toma.validado_por = user
            self.orden_toma.fecha_validacion = timezone.now()
            self.orden_toma.save()

    @property
    def puede_regenerar(self):
        return self.estado in ('borrador', 'generada')

    def get_absolute_url(self):
        return reverse('orders:orden_generada_detail', kwargs={'pk': self.pk})

# ==================== FUNCIONES AUXILIARES ====================

def numero_a_letras(numero):
    """
    Convierte un número a letras (para el total en letras en las órdenes)
    """
    try:
        from decimal import Decimal
        numero = Decimal(str(numero))
        
        # Parte entera
        entero = int(numero)
        decimales = int((numero - entero) * 100)
        
        # Conversión básica - puedes mejorar esta función
        unidades = ['', 'UNO', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
        decenas = ['', 'DIEZ', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
        especiales = ['DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISÉIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE']
        
        if entero == 0:
            resultado_entero = "CERO"
        elif entero < 10:
            resultado_entero = unidades[entero]
        elif entero < 20:
            resultado_entero = especiales[entero - 10]
        elif entero < 100:
            if entero % 10 == 0:
                resultado_entero = decenas[entero // 10]
            else:
                resultado_entero = f"{decenas[entero // 10]} Y {unidades[entero % 10]}"
        else:
            resultado_entero = str(entero)  # Para números grandes, mejor mostrar el número
            
        if decimales > 0:
            return f"{resultado_entero} CON {decimales:02d}/100"
        else:
            return f"{resultado_entero} EXACTOS"
            
    except:
        return "CANTIDAD EN NÚMEROS"

# ==================== MODELOS DE ORDENES DE PRODUCCIÓN ====================

class OrdenProduccion(models.Model):
    """
    Orden de producción generada automáticamente al validar una orden de toma
    """
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_produccion', 'En Producción'),
        ('completado', 'Completado'),
        ('validado', 'Validado'),
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
        help_text='Código único de la orden de producción (generado automáticamente)'
    )
    
    # Relación con orden de toma
    orden_toma = models.ForeignKey(
        OrdenToma,
        on_delete=models.CASCADE,
        related_name='ordenes_produccion',
        verbose_name='Orden de Toma'
    )
    
    # Información copiada de la orden de toma
    nombre_cliente = models.CharField('Nombre del Cliente', max_length=255)
    ruc_dni_cliente = models.CharField('RUC/DNI del Cliente', max_length=20)
    empresa_cliente = models.CharField('Empresa', max_length=200, blank=True, null=True)
    
    # Detalles específicos de producción
    proyecto_campania = models.CharField(
        'Proyecto/Campaña',
        max_length=255,
        help_text='Nombre del proyecto o campaña'
    )
    
    titulo_material = models.CharField(
        'Título del Material',
        max_length=255,
        help_text='Título del material a producir'
    )
    
    descripcion_breve = models.TextField(
        'Descripción Breve',
        help_text='Descripción breve del trabajo a realizar'
    )
    
    tipo_produccion = models.CharField(
        'Tipo de Producción',
        max_length=50,
        choices=[
            ('video', 'Video'),
            ('audio', 'Audio'),
            ('edicion', 'Edición'),
            ('animacion', 'Animación'),
            ('mixto', 'Mixto'),
        ],
        default='video'
    )
    
    especificaciones_tecnicas = models.TextField(
        'Especificaciones Técnicas',
        blank=True,
        null=True,
        help_text='Formatos, resoluciones, codecs, etc.'
    )
    
    # Fechas de producción
    fecha_inicio_planeada = models.DateField('Fecha Inicio Planeada')
    fecha_fin_planeada = models.DateField('Fecha Fin Planeada')
    fecha_inicio_real = models.DateField('Fecha Inicio Real', null=True, blank=True)
    fecha_fin_real = models.DateField('Fecha Fin Real', null=True, blank=True)
    
    # Equipo y recursos
    equipo_asignado = models.TextField(
        'Equipo Asignado',
        help_text='Equipo técnico asignado para la producción'
    )
    
    recursos_necesarios = models.TextField(
        'Recursos Necesarios',
        blank=True,
        null=True,
        help_text='Recursos adicionales necesarios'
    )
    
    # Estado y prioridad
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='normal'
    )
     # NUEVOS CAMPOS PARA GESTIÓN DE DOCUMENTOS (igual que OrdenToma)
    plantilla_orden = models.ForeignKey(
        'PlantillaOrden',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Plantilla de Orden de Producción',
        help_text='Plantilla Word para generar la orden de producción'
    )
    
    archivo_orden_firmada = models.FileField(
        'Orden Firmada',
        upload_to='ordenes_produccion_firmadas/',
        null=True,
        blank=True,
        help_text='PDF de la orden de producción firmada por el cliente'
    )
    
    fecha_subida_firmada = models.DateTimeField(
        'Fecha Subida Firmada',
        null=True,
        blank=True
    )
    
    # Archivos y entregables
    archivos_entregables = models.TextField(
        'Archivos Entregables',
        blank=True,
        null=True,
        help_text='Lista de archivos a entregar'
    )
    
    observaciones_produccion = models.TextField(
        'Observaciones de Producción',
        blank=True,
        null=True
    )
    
    # Responsables
    productor_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'rol': 'productor'},
        related_name='ordenes_producidas',
        verbose_name='Productor Asignado'
    )
    
    # Fechas
    fecha_creacion = models.DateTimeField('Fecha de Creación', default=timezone.now)
    fecha_validacion = models.DateTimeField('Fecha de Validación', null=True, blank=True)
    fecha_completado = models.DateTimeField('Fecha de Completado', null=True, blank=True)
    
    # Usuarios
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_produccion_validadas',
        verbose_name='Validado por'
    )
    
    completado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes_produccion_completadas',
        verbose_name='Completado por'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ordenes_produccion_creadas',
        verbose_name='Creada por'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Orden de Producción'
        verbose_name_plural = 'Órdenes de Producción'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estado', 'fecha_creacion']),
            models.Index(fields=['orden_toma', 'estado']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre_cliente}"
    
    def save(self, *args, **kwargs):
        """Método save para generar código y copiar datos"""
        if not self.pk and not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Copiar datos de la orden de toma si no existen
        if self.orden_toma and (not self.nombre_cliente or not self.proyecto_campania):
            self.copiar_datos_orden_toma()
        
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        """Genera código único para orden de producción"""
        try:
            ultima_orden = OrdenProduccion.objects.order_by('-id').first()
            if ultima_orden:
                siguiente_numero = ultima_orden.id + 1
            else:
                siguiente_numero = 1
            
            return f"OP{siguiente_numero:06d}"
        except Exception:
            import time
            return f"OP{int(time.time())}"
    
    def copiar_datos_orden_toma(self):
        """Copia datos de la orden de toma relacionada"""
        if self.orden_toma:
            self.nombre_cliente = self.orden_toma.nombre_cliente
            self.ruc_dni_cliente = self.orden_toma.ruc_dni_cliente
            self.empresa_cliente = self.orden_toma.empresa_cliente
            self.proyecto_campania = self.orden_toma.proyecto_campania
            self.titulo_material = self.orden_toma.titulo_material
            self.descripcion_breve = self.orden_toma.descripcion_breve
            self.equipo_asignado = self.orden_toma.equipo_asignado
            self.recursos_necesarios = self.orden_toma.recursos_necesarios
            self.fecha_inicio_planeada = self.orden_toma.fecha_produccion_inicio
            self.fecha_fin_planeada = self.orden_toma.fecha_produccion_fin
    
    def iniciar_produccion(self):
        """Cambia el estado a en producción"""
        if self.estado == 'pendiente':
            self.estado = 'en_produccion'
            self.fecha_inicio_real = timezone.now().date()
            self.save()
    
    def completar(self, user):
        """Completa la orden de producción"""
        self.estado = 'completado'
        self.completado_por = user
        self.fecha_completado = timezone.now()
        self.fecha_fin_real = timezone.now().date()
        self.save()
    
    def validar(self, user):
        """Valida la orden de producción"""
        self.estado = 'validado'
        self.validado_por = user
        self.fecha_validacion = timezone.now()
        self.save()
    
    def cancelar(self):
        """Cancela la orden de producción"""
        self.estado = 'cancelado'
        self.save()
    
    def get_absolute_url(self):
        return reverse('custom_admin:orden_produccion_detail_api', kwargs={'order_id': self.pk})
    
    @property
    def dias_retraso(self):
        """Calcula días de retraso"""
        if self.fecha_fin_planeada and self.estado != 'completado':
            hoy = timezone.now().date()
            if hoy > self.fecha_fin_planeada:
                return (hoy - self.fecha_fin_planeada).days
        return 0
    def generar_orden_desde_plantilla(self, plantilla_id=None, user=None):
        """Genera una orden para imprimir similar a OrdenToma"""
    # Obtener plantilla
        if plantilla_id:
            plantilla = PlantillaOrden.objects.get(id=plantilla_id)
        else:
            plantilla = PlantillaOrden.objects.filter(
                is_default=True, is_active=True
            ).first()
            if not plantilla:
                plantilla = PlantillaOrden.objects.filter(is_active=True).first()
    
        if not plantilla:
            raise ValueError("No hay plantillas de orden disponibles")
    
        # ✅ CORREGIDO: Crear orden generada con orden_toma (obligatorio) y orden_produccion (opcional)
        orden_generada = OrdenGenerada.objects.create(
            orden_toma=self.orden_toma,  # ✅ ESTE CAMPO ES OBLIGATORIO
            orden_produccion=self,       # ✅ ESTE ES OPCIONAL
            plantilla_usada=plantilla,
            generado_por=user or self.created_by,
            estado='borrador'
        )
    
        # Generar el PDF
        if orden_generada.generar_orden_produccion_pdf():
            return orden_generada
        else:
            orden_generada.delete()
            raise ValueError("Error al generar la orden PDF")

    def subir_orden_firmada(self, archivo_firmado, usuario):
        """Procesa la orden firmada subida - igual que OrdenToma"""
        try:
            # Guardar archivo
            self.archivo_orden_firmada = archivo_firmado
            self.fecha_subida_firmada = timezone.now()
            
            # Cambiar estado a validado
            self.estado = 'validado'
            self.validado_por = usuario
            self.fecha_validacion = timezone.now()
            
            self.save()
            
            # Registrar en historial
            HistorialOrdenProduccion.objects.create(
                orden_produccion=self,
                accion='validada',
                usuario=usuario,
                descripcion=f'Orden de producción firmada subida. Archivo: {archivo_firmado.name}'
            )
            
            return True
            
        except Exception as e:
            print(f"Error subiendo orden firmada: {e}")
            return False


class HistorialOrdenProduccion(models.Model):
    """
    Historial de cambios de las órdenes de producción
    """
    
    ACCION_CHOICES = [
        ('creada', 'Creada'),
        ('editada', 'Editada'),
        ('iniciada', 'Producción Iniciada'),
        ('completada', 'Completada'),
        ('validada', 'Validada'),
        ('cancelada', 'Cancelada'),
    ]
    
    orden_produccion = models.ForeignKey(
        OrdenProduccion,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Orden de Producción'
    )
    
    accion = models.CharField('Acción', max_length=20, choices=ACCION_CHOICES)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    descripcion = models.TextField('Descripción')
    
    datos_anteriores = models.JSONField('Datos Anteriores', null=True, blank=True)
    datos_nuevos = models.JSONField('Datos Nuevos', null=True, blank=True)
    
    fecha = models.DateTimeField('Fecha', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Historial de Orden de Producción'
        verbose_name_plural = 'Historial de Órdenes de Producción'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.orden_produccion.codigo} - {self.get_accion_display()} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
