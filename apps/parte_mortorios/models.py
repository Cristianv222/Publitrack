from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from decimal import Decimal

class ParteMortorio(models.Model):
    """
    Modelo para gestionar partes mortuorios (transmisiones por fallecimiento)
    """
    
    ESTADO_CHOICES = [
        ('solicitado', 'Solicitado'),
        ('programado', 'Programado'), 
        ('transmitido', 'Transmitido'),
        ('cancelado', 'Cancelado'),
    ]
    
    URGENCIA_CHOICES = [
        ('normal', 'Normal'),
        ('urgente', 'Urgente'),
        ('muy_urgente', 'Muy Urgente'),
    ]
    
    # Código único
    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único del parte mortorio'
    )
    
    # Relación con cliente (familiares)
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'cliente'},
        related_name='partes_mortorios',
        verbose_name='Cliente/Familiar'
    )
    
    # ==================== INFORMACIÓN DEL FALLECIDO ====================
    nombre_fallecido = models.CharField(
        'Nombre del Fallecido',
        max_length=255,
        help_text='Nombre completo de la persona fallecida'
    )
    
    edad_fallecido = models.PositiveIntegerField(
        'Edad del Fallecido',
        null=True,
        blank=True
    )
    
    dni_fallecido = models.CharField(
        'DNI del Fallecido',
        max_length=20,
        blank=True,
        null=True
    )
    
    fecha_nacimiento = models.DateField(
        'Fecha de Nacimiento',
        null=True,
        blank=True
    )
    
    fecha_fallecimiento = models.DateField(
        'Fecha de Fallecimiento'
    )
    
    # ==================== INFORMACIÓN FAMILIAR ====================
    nombre_esposa = models.CharField(
        'Nombre de la Esposa/Esposo',
        max_length=255,
        blank=True,
        null=True,
        help_text='Nombre del cónyuge del fallecido'
    )
    
    cantidad_hijos = models.PositiveIntegerField(
        'Cantidad de Hijos',
        default=0,
        help_text='Número total de hijos del fallecido'
    )
    
    hijos_vivos = models.PositiveIntegerField(
        'Hijos Vivos',
        default=0,
        help_text='Número de hijos que están vivos'
    )
    
    hijos_fallecidos = models.PositiveIntegerField(
        'Hijos Fallecidos',
        default=0,
        help_text='Número de hijos que han fallecido'
    )
    
    nombres_hijos = models.TextField(
        'Nombres de los Hijos',
        blank=True,
        null=True,
        help_text='Nombres completos de todos los hijos (separados por comas)'
    )
    
    familiares_adicionales = models.TextField(
        'Familiares Adicionales',
        blank=True,
        null=True,
        help_text='Otros familiares importantes (hermanos, padres, etc.)'
    )
    
    # ==================== INFORMACIÓN DE LA CEREMONIA ====================
    tipo_ceremonia = models.CharField(
        'Tipo de Ceremonia',
        max_length=100,
        choices=[
            ('misa', 'Misa'),
            ('velatorio', 'Velatorio'),
            ('ambos', 'Misa y Velatorio'),
            ('otro', 'Otro'),
        ],
        default='misa'
    )
    
    fecha_misa = models.DateField(
        'Fecha de Misa/Velatorio',
        null=True,
        blank=True
    )
    
    hora_misa = models.TimeField(
        'Hora de Misa/Velatorio',
        null=True,
        blank=True
    )
    
    lugar_misa = models.TextField(
        'Lugar de Misa/Velatorio',
        blank=True,
        null=True
    )
    
    # ==================== INFORMACIÓN DE TRANSMISIÓN ====================
    fecha_inicio_transmision = models.DateField(
        'Fecha de Inicio de Transmisión',
        null=True,
        blank=True
    )
    
    fecha_fin_transmision = models.DateField(
        'Fecha de Fin de Transmisión',
        null=True,
        blank=True
    )
    
    hora_transmision = models.TimeField(
        'Hora de Transmisión',
        null=True,
        blank=True
    )
    
    duracion_transmision = models.PositiveIntegerField(
        'Duración (minutos)',
        default=1,
        help_text='Duración en minutos de cada transmisión'
    )
    
    repeticiones_dia = models.PositiveIntegerField(
        'Repeticiones por Día',
        default=1,
        help_text='Número de veces que se transmitirá por día'
    )
    
    precio_por_segundo = models.DecimalField(
        'Precio por Segundo',
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.20'),
        help_text='Precio por segundo de transmisión'
    )
    
    precio_total = models.DecimalField(
        'Precio Total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Precio total calculado automáticamente'
    )
    
    # ==================== ESTADO Y PRIORIDAD ====================
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='solicitado'
    )
    
    urgencia = models.CharField(
        'Urgencia',
        max_length=20,
        choices=URGENCIA_CHOICES,
        default='normal'
    )
    
    # ==================== OBSERVACIONES Y DETALLES ====================
    observaciones = models.TextField(
        'Observaciones',
        blank=True,
        null=True
    )
    
    mensaje_personalizado = models.TextField(
        'Mensaje Personalizado',
        blank=True,
        null=True,
        help_text='Mensaje especial para la transmisión'
    )
    
    # ==================== FECHAS DEL SISTEMA ====================
    fecha_solicitud = models.DateTimeField(
        'Fecha de Solicitud',
        default=timezone.now
    )
    
    fecha_programacion = models.DateTimeField(
        'Fecha de Programación',
        null=True,
        blank=True
    )
    
    fecha_transmision_completada = models.DateTimeField(
        'Fecha Transmisión Completada',
        null=True,
        blank=True
    )
    
    # ==================== RESPONSABLE ====================
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='partes_mortorios_creados',
        verbose_name='Creado por'
    )
    
    # ==================== METADATOS ====================
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Parte Mortorio'
        verbose_name_plural = 'Partes Mortorios'
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['estado', 'fecha_solicitud']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre_fallecido}"
    
    def save(self, *args, **kwargs):
        """Genera código automáticamente si no existe y calcula precio"""
        if not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Calcular precio total automáticamente
        self.calcular_precio_total()
        
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        """Genera código único para el parte mortorio"""
        try:
            ultimo_parte = ParteMortorio.objects.order_by('-id').first()
            if ultimo_parte:
                siguiente_numero = ultimo_parte.id + 1
            else:
                siguiente_numero = 1
            
            return f"PM{siguiente_numero:06d}"
        except Exception:
            import time
            return f"PM{int(time.time())}"
    
    def calcular_precio_total(self):
        """Calcula el precio total basado en duración, repeticiones y días"""
        if (self.fecha_inicio_transmision and self.fecha_fin_transmision and 
            self.duracion_transmision and self.repeticiones_dia and self.precio_por_segundo):
            
            # Calcular días de transmisión
            dias_transmision = (self.fecha_fin_transmision - self.fecha_inicio_transmision).days + 1
            
            # Calcular segundos totales
            segundos_por_transmision = self.duracion_transmision * 60
            transmisiones_totales = self.repeticiones_dia * dias_transmision
            segundos_totales = segundos_por_transmision * transmisiones_totales
            
            # Calcular precio total
            self.precio_total = Decimal(str(segundos_totales)) * self.precio_por_segundo
        else:
            self.precio_total = Decimal('0.00')
    
    def get_absolute_url(self):
        return reverse('parte_mortorios:detalle', kwargs={'pk': self.pk})
    
    def programar(self, user):
        """Programa el parte mortorio"""
        self.estado = 'programado'
        self.fecha_programacion = timezone.now()
        self.save()
    
    def marcar_transmitido(self, user):
        """Marca como transmitido"""
        self.estado = 'transmitido'
        self.fecha_transmision_completada = timezone.now()
        self.save()
    
    def cancelar(self, user):
        """Cancela el parte mortorio"""
        self.estado = 'cancelado'
        self.save()
    
    @property
    def dias_desde_solicitud(self):
        """Calcula días desde la solicitud"""
        return (timezone.now() - self.fecha_solicitud).days
    
    @property
    def necesita_atencion(self):
        """Determina si necesita atención urgente"""
        return self.urgencia in ['urgente', 'muy_urgente'] or self.dias_desde_solicitud > 2
    
    @property
    def dias_transmision(self):
        """Calcula días de transmisión automáticamente"""
        if self.fecha_inicio_transmision and self.fecha_fin_transmision:
            return (self.fecha_fin_transmision - self.fecha_inicio_transmision).days + 1
        return 0

    @property
    def resumen_familia(self):
        """Genera un resumen de la información familiar"""
        resumen = []
        if self.nombre_esposa:
            resumen.append(f"Esposa/o: {self.nombre_esposa}")
        if self.cantidad_hijos > 0:
            resumen.append(f"Hijos: {self.cantidad_hijos} ({self.hijos_vivos} vivos, {self.hijos_fallecidos} fallecidos)")
        return ", ".join(resumen)
class HistorialParteMortorio(models.Model):
    """
    Historial de cambios de los partes mortorios
    """
    
    ACCION_CHOICES = [
        ('creado', 'Creado'),
        ('editado', 'Editado'),
        ('programado', 'Programado'),
        ('transmitido', 'Transmitido'),
        ('cancelado', 'Cancelado'),
    ]
    
    parte_mortorio = models.ForeignKey(
        ParteMortorio,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Parte Mortorio'
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
        verbose_name = 'Historial de Parte Mortorio'
        verbose_name_plural = 'Historial de Partes Mortorios'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.parte_mortorio.codigo} - {self.get_accion_display()} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"