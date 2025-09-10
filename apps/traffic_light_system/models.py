"""
Modelos para el Sistema de Semáforos
Sistema PubliTrack - Control visual de estados de cuñas publicitarias
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime, timedelta
import json

class ConfiguracionSemaforo(models.Model):
    """
    Configuración global del sistema de semáforos
    """
    
    TIPO_CALCULO_CHOICES = [
        ('dias_restantes', 'Por Días Restantes'),
        ('porcentaje_tiempo', 'Por Porcentaje de Tiempo Transcurrido'),
        ('estado_cuña', 'Por Estado de la Cuña'),
        ('combinado', 'Combinado (Estado + Tiempo)'),
    ]
    
    # Configuración básica
    nombre = models.CharField(
        'Nombre de Configuración',
        max_length=100,
        unique=True,
        help_text='Nombre descriptivo de la configuración'
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción detallada de esta configuración'
    )
    
    tipo_calculo = models.CharField(
        'Tipo de Cálculo',
        max_length=20,
        choices=TIPO_CALCULO_CHOICES,
        default='combinado',
        help_text='Método de cálculo para determinar el color del semáforo'
    )
    
    # Umbrales por días restantes
    dias_verde_min = models.PositiveIntegerField(
        'Días Mínimos para Verde',
        default=15,
        help_text='Días mínimos restantes para mostrar verde'
    )
    
    dias_amarillo_min = models.PositiveIntegerField(
        'Días Mínimos para Amarillo',
        default=7,
        help_text='Días mínimos restantes para mostrar amarillo (menos que esto es rojo)'
    )
    
    # Umbrales por porcentaje
    porcentaje_verde_max = models.DecimalField(
        'Porcentaje Máximo para Verde',
        max_digits=5,
        decimal_places=2,
        default=Decimal('50.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Porcentaje máximo de tiempo transcurrido para mostrar verde'
    )
    
    porcentaje_amarillo_max = models.DecimalField(
        'Porcentaje Máximo para Amarillo',
        max_digits=5,
        decimal_places=2,
        default=Decimal('85.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Porcentaje máximo de tiempo transcurrido para mostrar amarillo'
    )
    
    # Estados que determinan colores
    estados_verde = models.JSONField(
        'Estados Verde',
        default=list,
        help_text='Lista de estados de cuña que muestran verde'
    )
    
    estados_amarillo = models.JSONField(
        'Estados Amarillo',
        default=list,
        help_text='Lista de estados de cuña que muestran amarillo'
    )
    
    estados_rojo = models.JSONField(
        'Estados Rojo',
        default=list,
        help_text='Lista de estados de cuña que muestran rojo'
    )
    
    estados_gris = models.JSONField(
        'Estados Gris',
        default=list,
        help_text='Lista de estados de cuña que muestran gris'
    )
    
    # Configuraciones de alertas
    enviar_alertas = models.BooleanField(
        'Enviar Alertas',
        default=True,
        help_text='Si enviar alertas automáticas cuando cambia el estado'
    )
    
    alertas_solo_empeoramiento = models.BooleanField(
        'Alertas Solo por Empeoramiento',
        default=True,
        help_text='Solo alertar cuando el estado empeora (verde->amarillo->rojo)'
    )
    
    # Configuración activa
    is_active = models.BooleanField(
        'Activa',
        default=False,
        help_text='Si esta configuración está activa (solo una puede estar activa)'
    )
    
    is_default = models.BooleanField(
        'Por Defecto',
        default=False,
        help_text='Si esta es la configuración por defecto'
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='configuraciones_semaforo_creadas',
        verbose_name='Creada por'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Semáforo'
        verbose_name_plural = 'Configuraciones de Semáforo'
        ordering = ['-is_active', '-is_default', 'nombre']
    
    def __str__(self):
        status = " (ACTIVA)" if self.is_active else " (Inactiva)"
        return f"{self.nombre}{status}"
    
    def save(self, *args, **kwargs):
        """Override para asegurar que solo una configuración esté activa"""
        if self.is_active:
            # Desactivar todas las demás
            ConfiguracionSemaforo.objects.exclude(pk=self.pk).update(is_active=False)
        
        # Si es la primera configuración, hacerla activa por defecto
        if not ConfiguracionSemaforo.objects.exclude(pk=self.pk).exists():
            self.is_active = True
            self.is_default = True
        
        # Inicializar estados por defecto si están vacíos
        if not self.estados_verde:
            self.estados_verde = ['activa', 'aprobada']
        if not self.estados_amarillo:
            self.estados_amarillo = ['pendiente_revision', 'en_produccion', 'pausada']
        if not self.estados_rojo:
            self.estados_rojo = ['borrador']
        if not self.estados_gris:
            self.estados_gris = ['finalizada', 'cancelada']
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active(cls):
        """Obtiene la configuración activa"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            # Si no hay activa, crear una por defecto
            return cls.objects.create(
                nombre="Configuración por Defecto",
                descripcion="Configuración automática creada por el sistema",
                is_active=True,
                is_default=True
            )


class EstadoSemaforo(models.Model):
    """
    Estados calculados del semáforo para cada cuña
    """
    
    COLOR_CHOICES = [
        ('verde', 'Verde'),
        ('amarillo', 'Amarillo'),
        ('rojo', 'Rojo'),
        ('gris', 'Gris'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    # Relación con la cuña
    cuña = models.OneToOneField(
        'content_management.CuñaPublicitaria',
        on_delete=models.CASCADE,
        related_name='estado_semaforo',
        verbose_name='Cuña Publicitaria'
    )
    
    # Estado actual
    color_actual = models.CharField(
        'Color Actual',
        max_length=10,
        choices=COLOR_CHOICES,
        help_text='Color actual del semáforo'
    )
    
    color_anterior = models.CharField(
        'Color Anterior',
        max_length=10,
        choices=COLOR_CHOICES,
        null=True,
        blank=True,
        help_text='Color anterior del semáforo'
    )
    
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='media',
        help_text='Prioridad basada en el estado actual'
    )
    
    # Métricas calculadas
    dias_restantes = models.IntegerField(
        'Días Restantes',
        null=True,
        blank=True,
        help_text='Días restantes hasta la fecha fin'
    )
    
    porcentaje_tiempo_transcurrido = models.DecimalField(
        'Porcentaje Tiempo Transcurrido',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Porcentaje del tiempo total que ha transcurrido'
    )
    
    # Razones del cálculo
    razon_color = models.TextField(
        'Razón del Color',
        blank=True,
        help_text='Explicación de por qué se asignó este color'
    )
    
    metadatos_calculo = models.JSONField(
        'Metadatos del Cálculo',
        default=dict,
        help_text='Información adicional sobre el cálculo realizado'
    )
    
    # Control de alertas
    requiere_alerta = models.BooleanField(
        'Requiere Alerta',
        default=False,
        help_text='Si se debe enviar una alerta por este estado'
    )
    
    alerta_enviada = models.BooleanField(
        'Alerta Enviada',
        default=False,
        help_text='Si ya se envió la alerta para este estado'
    )
    
    fecha_alerta_enviada = models.DateTimeField(
        'Fecha Alerta Enviada',
        null=True,
        blank=True
    )
    
    # Configuración utilizada
    configuracion_utilizada = models.ForeignKey(
        ConfiguracionSemaforo,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Configuración Utilizada',
        help_text='Configuración de semáforo que se utilizó para este cálculo'
    )
    
    # Metadatos
    calculado_en = models.DateTimeField('Calculado en', auto_now=True)
    ultimo_calculo = models.DateTimeField('Último Cálculo', auto_now=True)
    
    class Meta:
        verbose_name = 'Estado de Semáforo'
        verbose_name_plural = 'Estados de Semáforo'
        ordering = ['-ultimo_calculo']
        indexes = [
            models.Index(fields=['color_actual', 'prioridad']),
            models.Index(fields=['requiere_alerta', 'alerta_enviada']),
            models.Index(fields=['ultimo_calculo']),
        ]
    
    def __str__(self):
        return f"{self.cuña.codigo} - {self.get_color_actual_display()}"
    
    @property
    def necesita_atencion(self):
        """Verifica si el estado requiere atención"""
        return self.color_actual in ['rojo', 'amarillo']
    
    @property
    def cambio_color(self):
        """Verifica si hubo cambio de color"""
        return self.color_anterior and self.color_anterior != self.color_actual
    
    @property
    def empeoro_estado(self):
        """Verifica si el estado empeoró"""
        if not self.color_anterior:
            return False
        
        orden_colores = {'verde': 1, 'amarillo': 2, 'rojo': 3, 'gris': 0}
        anterior = orden_colores.get(self.color_anterior, 0)
        actual = orden_colores.get(self.color_actual, 0)
        
        return actual > anterior
    
    def marcar_alerta_enviada(self):
        """Marca la alerta como enviada"""
        self.alerta_enviada = True
        self.fecha_alerta_enviada = timezone.now()
        self.save(update_fields=['alerta_enviada', 'fecha_alerta_enviada'])


class HistorialEstadoSemaforo(models.Model):
    """
    Historial de cambios de estado del semáforo
    """
    
    # Relación
    cuña = models.ForeignKey(
        'content_management.CuñaPublicitaria',
        on_delete=models.CASCADE,
        related_name='historial_semaforo',
        verbose_name='Cuña Publicitaria'
    )
    
    # Cambio de estado
    color_anterior = models.CharField(
        'Color Anterior',
        max_length=10,
        choices=EstadoSemaforo.COLOR_CHOICES,
        null=True,
        blank=True
    )
    
    color_nuevo = models.CharField(
        'Color Nuevo',
        max_length=10,
        choices=EstadoSemaforo.COLOR_CHOICES
    )
    
    prioridad_anterior = models.CharField(
        'Prioridad Anterior',
        max_length=10,
        choices=EstadoSemaforo.PRIORIDAD_CHOICES,
        null=True,
        blank=True
    )
    
    prioridad_nueva = models.CharField(
        'Prioridad Nueva',
        max_length=10,
        choices=EstadoSemaforo.PRIORIDAD_CHOICES
    )
    
    # Contexto del cambio
    razon_cambio = models.TextField(
        'Razón del Cambio',
        help_text='Explicación de por qué cambió el estado'
    )
    
    dias_restantes = models.IntegerField(
        'Días Restantes',
        null=True,
        blank=True
    )
    
    porcentaje_tiempo = models.DecimalField(
        'Porcentaje Tiempo Transcurrido',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Configuración utilizada
    configuracion_utilizada = models.ForeignKey(
        ConfiguracionSemaforo,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Configuración Utilizada'
    )
    
    # Alertas
    alerta_generada = models.BooleanField(
        'Alerta Generada',
        default=False,
        help_text='Si se generó una alerta para este cambio'
    )
    
    # Usuario que provocó el cambio (opcional)
    usuario_trigger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario que Provocó el Cambio'
    )
    
    # Metadatos
    fecha_cambio = models.DateTimeField('Fecha del Cambio', auto_now_add=True)
    metadatos = models.JSONField('Metadatos', default=dict)
    
    class Meta:
        verbose_name = 'Historial de Estado Semáforo'
        verbose_name_plural = 'Historial de Estados Semáforo'
        ordering = ['-fecha_cambio']
        indexes = [
            models.Index(fields=['cuña', 'fecha_cambio']),
            models.Index(fields=['color_nuevo', 'fecha_cambio']),
            models.Index(fields=['alerta_generada']),
        ]
    
    def __str__(self):
        anterior = self.get_color_anterior_display() if self.color_anterior else "Nuevo"
        return f"{self.cuña.codigo}: {anterior} → {self.get_color_nuevo_display()}"


class AlertaSemaforo(models.Model):
    """
    Alertas generadas por el sistema de semáforos
    """
    
    TIPO_ALERTA_CHOICES = [
        ('cambio_estado', 'Cambio de Estado'),
        ('vencimiento_proximo', 'Vencimiento Próximo'),
        ('estado_critico', 'Estado Crítico'),
        ('revision_requerida', 'Revisión Requerida'),
        ('configuracion_cambio', 'Cambio de Configuración'),
    ]
    
    SEVERIDAD_CHOICES = [
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('critical', 'Crítico'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('error', 'Error al Enviar'),
        ('ignorada', 'Ignorada'),
    ]
    
    # Relaciones
    cuña = models.ForeignKey(
        'content_management.CuñaPublicitaria',
        on_delete=models.CASCADE,
        related_name='alertas_semaforo',
        verbose_name='Cuña Publicitaria',
        null=True,
        blank=True  # Para alertas que no son específicas de una cuña
    )
    
    estado_semaforo = models.ForeignKey(
        EstadoSemaforo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Estado Semáforo'
    )
    
    # Información de la alerta
    tipo_alerta = models.CharField(
        'Tipo de Alerta',
        max_length=20,
        choices=TIPO_ALERTA_CHOICES
    )
    
    severidad = models.CharField(
        'Severidad',
        max_length=10,
        choices=SEVERIDAD_CHOICES,
        default='warning'
    )
    
    titulo = models.CharField(
        'Título',
        max_length=200,
        help_text='Título descriptivo de la alerta'
    )
    
    mensaje = models.TextField(
        'Mensaje',
        help_text='Mensaje detallado de la alerta'
    )
    
    # Destinatarios
    usuarios_destino = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='alertas_semaforo_recibidas',
        verbose_name='Usuarios Destino',
        blank=True
    )
    
    roles_destino = models.JSONField(
        'Roles Destino',
        default=list,
        help_text='Lista de roles que deben recibir esta alerta'
    )
    
    # Estado de envío
    estado = models.CharField(
        'Estado',
        max_length=10,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    
    # Canales de envío
    enviar_email = models.BooleanField('Enviar por Email', default=True)
    enviar_sms = models.BooleanField('Enviar por SMS', default=False)
    enviar_push = models.BooleanField('Enviar Push Notification', default=True)
    mostrar_dashboard = models.BooleanField('Mostrar en Dashboard', default=True)
    
    # Control de tiempo
    fecha_programada = models.DateTimeField(
        'Fecha Programada',
        null=True,
        blank=True,
        help_text='Fecha programada para envío (si es diferente de creación)'
    )
    
    fecha_enviada = models.DateTimeField(
        'Fecha Enviada',
        null=True,
        blank=True
    )
    
    fecha_vencimiento = models.DateTimeField(
        'Fecha de Vencimiento',
        null=True,
        blank=True,
        help_text='Fecha hasta la cual la alerta es relevante'
    )
    
    # Configuración de reintento
    reintentos = models.PositiveIntegerField(
        'Reintentos',
        default=0,
        help_text='Número de reintentos de envío'
    )
    
    max_reintentos = models.PositiveIntegerField(
        'Máximo Reintentos',
        default=3
    )
    
    error_mensaje = models.TextField(
        'Mensaje de Error',
        blank=True,
        help_text='Último mensaje de error si falló el envío'
    )
    
    # Metadatos
    metadatos = models.JSONField(
        'Metadatos',
        default=dict,
        help_text='Información adicional sobre la alerta'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Alerta de Semáforo'
        verbose_name_plural = 'Alertas de Semáforo'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tipo_alerta', 'severidad']),
            models.Index(fields=['estado', 'fecha_programada']),
            models.Index(fields=['cuña', 'created_at']),
            models.Index(fields=['fecha_vencimiento']),
        ]
    
    def __str__(self):
        cuña_info = f" - {self.cuña.codigo}" if self.cuña else ""
        return f"{self.get_tipo_alerta_display()}{cuña_info}"
    
    @property
    def esta_vencida(self):
        """Verifica si la alerta está vencida"""
        if self.fecha_vencimiento:
            return timezone.now() > self.fecha_vencimiento
        return False
    
    @property
    def puede_reintentarse(self):
        """Verifica si se puede reintentar el envío"""
        return (
            self.estado == 'error' and 
            self.reintentos < self.max_reintentos and
            not self.esta_vencida
        )
    
    def marcar_como_enviada(self):
        """Marca la alerta como enviada exitosamente"""
        self.estado = 'enviada'
        self.fecha_enviada = timezone.now()
        self.save(update_fields=['estado', 'fecha_enviada'])
    
    def marcar_error(self, mensaje_error):
        """Marca la alerta con error y incrementa reintentos"""
        self.estado = 'error'
        self.error_mensaje = mensaje_error
        self.reintentos += 1
        self.save(update_fields=['estado', 'error_mensaje', 'reintentos'])
    
    def programar_reintento(self, minutos_delay=30):
        """Programa un reintento para más tarde"""
        if self.puede_reintentarse:
            self.fecha_programada = timezone.now() + timedelta(minutes=minutos_delay)
            self.estado = 'pendiente'
            self.save(update_fields=['fecha_programada', 'estado'])


class ResumenEstadosSemaforo(models.Model):
    """
    Resumen agregado de estados para reporting y dashboard
    """
    
    PERIODO_CHOICES = [
        ('dia', 'Diario'),
        ('semana', 'Semanal'),
        ('mes', 'Mensual'),
    ]
    
    # Período del resumen
    periodo = models.CharField(
        'Período',
        max_length=10,
        choices=PERIODO_CHOICES
    )
    
    fecha = models.DateField(
        'Fecha',
        help_text='Fecha del resumen (día, inicio de semana, o inicio de mes)'
    )
    
    # Contadores por color
    total_cuñas = models.PositiveIntegerField('Total Cuñas', default=0)
    cuñas_verde = models.PositiveIntegerField('Cuñas Verde', default=0)
    cuñas_amarillo = models.PositiveIntegerField('Cuñas Amarillo', default=0)
    cuñas_rojo = models.PositiveIntegerField('Cuñas Rojo', default=0)
    cuñas_gris = models.PositiveIntegerField('Cuñas Gris', default=0)
    
    # Contadores por prioridad
    cuñas_prioridad_baja = models.PositiveIntegerField('Prioridad Baja', default=0)
    cuñas_prioridad_media = models.PositiveIntegerField('Prioridad Media', default=0)
    cuñas_prioridad_alta = models.PositiveIntegerField('Prioridad Alta', default=0)
    cuñas_prioridad_critica = models.PositiveIntegerField('Prioridad Crítica', default=0)
    
    # Métricas adicionales
    alertas_generadas = models.PositiveIntegerField('Alertas Generadas', default=0)
    cambios_estado = models.PositiveIntegerField('Cambios de Estado', default=0)
    
    # Porcentajes calculados
    porcentaje_verde = models.DecimalField(
        'Porcentaje Verde',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    porcentaje_problemas = models.DecimalField(
        'Porcentaje con Problemas',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Porcentaje de cuñas en amarillo o rojo'
    )
    
    # Metadatos
    configuracion_utilizada = models.ForeignKey(
        ConfiguracionSemaforo,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Configuración Utilizada'
    )
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Resumen Estados Semáforo'
        verbose_name_plural = 'Resúmenes Estados Semáforo'
        ordering = ['-fecha', '-periodo']
        unique_together = ['periodo', 'fecha']
        indexes = [
            models.Index(fields=['periodo', 'fecha']),
            models.Index(fields=['fecha']),
        ]
    
    def __str__(self):
        return f"Resumen {self.get_periodo_display()} - {self.fecha}"
    
    def calcular_porcentajes(self):
        """Calcula los porcentajes basados en los contadores"""
        if self.total_cuñas > 0:
            self.porcentaje_verde = (self.cuñas_verde / self.total_cuñas) * 100
            self.porcentaje_problemas = ((self.cuñas_amarillo + self.cuñas_rojo) / self.total_cuñas) * 100
        else:
            self.porcentaje_verde = Decimal('0.00')
            self.porcentaje_problemas = Decimal('0.00')
    
    def save(self, *args, **kwargs):
        """Override para calcular porcentajes automáticamente"""
        self.calcular_porcentajes()
        super().save(*args, **kwargs)