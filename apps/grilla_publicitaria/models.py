# grilla_publicitaria/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import timedelta  # ✅ AGREGAR ESTA IMPORTACIÓN

# Importaciones mejoradas - evitar circulares
from django.apps import apps

class TipoUbicacionPublicitaria(models.Model):
    """Tipos de ubicaciones para publicidad"""
    
    nombre = models.CharField(_('Nombre'), max_length=100)
    codigo = models.CharField(_('Código'), max_length=20, unique=True)
    descripcion = models.TextField(_('Descripción'), blank=True)
    duracion_maxima = models.DurationField(_('Duración Máxima'))
    prioridad = models.IntegerField(_('Prioridad'), default=1)
    
    class Meta:
        verbose_name = _('Tipo de Ubicación Publicitaria')
        verbose_name_plural = _('Tipos de Ubicaciones Publicitarias')
        ordering = ['prioridad', 'nombre']
    
    def __str__(self):
        return self.nombre

class UbicacionPublicitaria(models.Model):
    """Ubicaciones específicas en la programación para publicidad"""
    
    TIPO_PAUSA_CHOICES = [
        ('corta', 'Pausa Corta (30 seg)'),
        ('media', 'Pausa Media (60 seg)'),
        ('larga', 'Pausa Larga (90 seg)'),
        ('especial', 'Pausa Especial (120 seg)'),
    ]
    
    bloque_programacion = models.ForeignKey(
        'programacion_canal.BloqueProgramacion',
        on_delete=models.CASCADE,
        related_name='ubicaciones_publicitarias',
        verbose_name=_('Bloque de Programación')
    )
    
    tipo_pausa = models.CharField(
        _('Tipo de Pausa'),
        max_length=20,
        choices=TIPO_PAUSA_CHOICES,
        default='corta'
    )
    
    nombre = models.CharField(_('Nombre'), max_length=200)
    hora_inicio_relativa = models.DurationField(
        _('Hora Inicio Relativa'),
        help_text=_('Tiempo desde el inicio del bloque (HH:MM:SS)')
    )
    
    duracion_disponible = models.DurationField(
        _('Duración Disponible'),
        help_text=_('Duración máxima para publicidad')
    )
    
    capacidad_cuñas = models.PositiveIntegerField(
        _('Capacidad de Cuñas'),
        default=3  # Por defecto 3 cuñas por pausa
    )
    
    activo = models.BooleanField(_('Activo'), default=True)
    
    class Meta:
        verbose_name = _('Ubicación Publicitaria')
        verbose_name_plural = _('Ubicaciones Publicitarias')
        ordering = ['bloque_programacion', 'hora_inicio_relativa']
    
    def __str__(self):
        return f"{self.bloque_programacion} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        # Establecer duración disponible según el tipo de pausa
        if not self.duracion_disponible:
            duraciones = {
                'corta': timedelta(seconds=30),
                'media': timedelta(seconds=60),
                'larga': timedelta(seconds=90),
                'especial': timedelta(seconds=120),
            }
            self.duracion_disponible = duraciones.get(self.tipo_pausa, timedelta(seconds=30))
        
        super().save(*args, **kwargs)

class AsignacionCuña(models.Model):
    """Asignación de cuñas a ubicaciones específicas"""
    
    ESTADO_CHOICES = [
        ('programada', _('Programada')),
        ('confirmada', _('Confirmada')),
        ('transmitida', _('Transmitida')),
        ('cancelada', _('Cancelada')),
    ]
    
    ubicacion = models.ForeignKey(
        UbicacionPublicitaria,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name=_('Ubicación')
    )
    
    cuña = models.ForeignKey(
        'content_management.CuñaPublicitaria',
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name=_('Cuña Publicitaria')
    )
    
    fecha_emision = models.DateField(_('Fecha de Emisión'))
    hora_emision = models.TimeField(_('Hora de Emisión'))
    
    estado = models.CharField(
        _('Estado'),
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programada'
    )
    
    orden_en_ubicacion = models.PositiveIntegerField(
        _('Orden en Ubicación'),
        default=1
    )
    
    # Metadata
    creado_por = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Creado por')
    )
    
    fecha_creacion = models.DateTimeField(_('Fecha de Creación'), auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(_('Fecha de Actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('Asignación de Cuña')
        verbose_name_plural = _('Asignaciones de Cuñas')
        ordering = ['fecha_emision', 'hora_emision', 'ubicacion', 'orden_en_ubicacion']
    
    def __str__(self):
        return f"{self.cuña.codigo} - {self.fecha_emision} {self.hora_emision}"

class GrillaPublicitaria(models.Model):
    """Grilla publicitaria semanal consolidada"""
    
    programacion_semanal = models.ForeignKey(
        'programacion_canal.ProgramacionSemanal',
        on_delete=models.CASCADE,
        related_name='grillas_publicitarias',
        verbose_name=_('Programación Semanal')
    )
    
    fecha_generacion = models.DateTimeField(_('Fecha de Generación'), auto_now_add=True)
    generada_por = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Generada por')
    )
    
    total_cuñas_programadas = models.PositiveIntegerField(_('Total Cuñas Programadas'), default=0)
    total_ingresos_proyectados = models.DecimalField(
        _('Total Ingresos Proyectados'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        verbose_name = _('Grilla Publicitaria')
        verbose_name_plural = _('Grillas Publicitarias')
        ordering = ['-programacion_semanal__fecha_inicio_semana']
    
    def __str__(self):
        return f"Grilla - {self.programacion_semanal}"
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas de la grilla"""
        self.total_cuñas_programadas = AsignacionCuña.objects.filter(
            ubicacion__bloque_programacion__programacion_semanal=self.programacion_semanal
        ).count()
        
        # Calcular ingresos proyectados
        total_ingresos = 0
        asignaciones = AsignacionCuña.objects.filter(
            ubicacion__bloque_programacion__programacion_semanal=self.programacion_semanal
        ).select_related('cuña')
        
        for asignacion in asignaciones:
            total_ingresos += float(asignacion.cuña.precio_total)
        
        self.total_ingresos_proyectados = total_ingresos
        self.save()