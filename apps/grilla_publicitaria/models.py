# grilla_publicitaria/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# IMPORTS CONDICIONALES
try:
    from apps.programacion_canal.models import BloqueProgramacion, ProgramacionSemanal
    from apps.content_management.models import CuñaPublicitaria
    from apps.authentication.models import CustomUser
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando modelos: {e}")
    MODELS_AVAILABLE = False
    BloqueProgramacion = None
    ProgramacionSemanal = None
    CuñaPublicitaria = None
    CustomUser = None

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
    
    bloque_programacion = models.ForeignKey(
        BloqueProgramacion,
        on_delete=models.CASCADE,
        related_name='ubicaciones_publicitarias',
        verbose_name=_('Bloque de Programación')
    )
    
    tipo_ubicacion = models.ForeignKey(
        TipoUbicacionPublicitaria,
        on_delete=models.CASCADE,
        related_name='ubicaciones',
        verbose_name=_('Tipo de Ubicación')
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
        default=1
    )
    
    activo = models.BooleanField(_('Activo'), default=True)
    
    class Meta:
        verbose_name = _('Ubicación Publicitaria')
        verbose_name_plural = _('Ubicaciones Publicitarias')
        ordering = ['bloque_programacion', 'hora_inicio_relativa']
    
    def __str__(self):
        return f"{self.bloque_programacion} - {self.nombre}"

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
        CuñaPublicitaria,
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
        CustomUser,
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
        ProgramacionSemanal,
        on_delete=models.CASCADE,
        related_name='grillas_publicitarias',
        verbose_name=_('Programación Semanal')
    )
    
    fecha_generacion = models.DateTimeField(_('Fecha de Generación'), auto_now_add=True)
    generada_por = models.ForeignKey(
        CustomUser,
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