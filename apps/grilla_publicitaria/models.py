# grilla_publicitaria/models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import timedelta, time

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
        ('corta', _('Pausa Corta (30-60s)')),
        ('media', _('Pausa Media (1-2min)')),
        ('larga', _('Pausa Larga (2-5min)')),
    ]
    
    bloque_programacion = models.ForeignKey(
        'programacion_canal.BloqueProgramacion',
        on_delete=models.CASCADE,
        related_name='ubicaciones_publicitarias',
        verbose_name=_('Bloque de Programación')
    )
    
    nombre = models.CharField(_('Nombre de la Pausa'), max_length=200)
    
    hora_pausa = models.TimeField(
        _('Hora de la Pausa'),
        help_text=_('Hora exacta dentro del bloque donde inicia la pausa'),
        default=time(12, 0, 0)
    )
    
    tipo_pausa = models.CharField(
        _('Tipo de Pausa'),
        max_length=20,
        choices=TIPO_PAUSA_CHOICES,
        default='media'
    )
    
    duracion_pausa = models.DurationField(
        _('Duración Total'),
        help_text=_('Duración total de la pausa publicitaria'),
        default=timedelta(minutes=2)
    )
    
    capacidad_cuñas = models.PositiveIntegerField(
        _('Espacios Disponibles'),
        default=3,
        help_text=_('Número máximo de cuñas que caben en esta pausa')
    )
    
    activo = models.BooleanField(_('Activa'), default=True)
    
    class Meta:
        verbose_name = _('Ubicación Publicitaria')
        verbose_name_plural = _('Ubicaciones Publicitarias')
        ordering = ['bloque_programacion', 'hora_pausa']
        # SIN unique_together por ahora

    def __str__(self):
        return f"{self.nombre} - {self.hora_pausa}"
    
    @property
    def duracion_disponible(self):
        """Alias para compatibilidad"""
        return self.duracion_pausa
    
    @property
    def espacios_disponibles(self):
        """Calcula cuántos espacios quedan disponibles"""
        asignadas = self.asignaciones.count()
        return max(0, self.capacidad_cuñas - asignadas)
    
    @property
    def tiene_espacios_disponibles(self):
        """Verifica si hay espacios disponibles"""
        return self.espacios_disponibles > 0
    
    @property
    def cuñas_asignadas(self):
        """Obtiene las cuñas asignadas ordenadas"""
        return self.asignaciones.select_related('cuña').order_by('orden_en_ubicacion')
    
    def get_color_pausa(self):
        """Color según el tipo de pausa"""
        colors = {
            'corta': '#28a745',  # Verde
            'media': '#ffc107',  # Amarillo
            'larga': '#dc3545',  # Rojo
        }
        return colors.get(self.tipo_pausa, '#6c757d')
    
    def clean(self):
        """Validaciones adicionales"""
        super().clean()
        
        # Validar que la duración no sea cero o negativa
        if self.duracion_pausa.total_seconds() <= 0:
            raise ValidationError({
                'duracion_pausa': _('La duración debe ser mayor a cero.')
            })
        
        # Validar capacidad
        if self.capacidad_cuñas <= 0:
            raise ValidationError({
                'capacidad_cuñas': _('La capacidad debe ser mayor a cero.')
            })

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
        unique_together = ['ubicacion', 'fecha_emision', 'orden_en_ubicacion']
    
    def __str__(self):
        return f"{self.cuña.codigo} - {self.fecha_emision} {self.hora_emision}"
    
    def clean(self):
        """Validaciones para la asignación"""
        super().clean()
        
        # Validar que no se exceda la capacidad de la ubicación
        if self.ubicacion and self.fecha_emision:
            asignaciones_existentes = AsignacionCuña.objects.filter(
                ubicacion=self.ubicacion,
                fecha_emision=self.fecha_emision
            ).exclude(pk=self.pk if self.pk else None)
            
            if asignaciones_existentes.count() >= self.ubicacion.capacidad_cuñas:
                raise ValidationError(
                    _('La ubicación ya ha alcanzado su capacidad máxima de cuñas para esta fecha.')
                )
        
        # Validar que la ubicación esté activa
        if self.ubicacion and not self.ubicacion.activo:
            raise ValidationError(
                _('No se pueden asignar cuñas a ubicaciones inactivas.')
            )

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
        unique_together = ['programacion_semanal']
    
    def __str__(self):
        return f"Grilla - {self.programacion_semanal}"
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas de la grilla"""
        from django.db.models import Count, Sum
        
        # Contar cuñas programadas
        self.total_cuñas_programadas = AsignacionCuña.objects.filter(
            ubicacion__bloque_programacion__programacion_semanal=self.programacion_semanal,
            estado__in=['programada', 'confirmada']
        ).count()
        
        # Calcular ingresos proyectados
        resultado = AsignacionCuña.objects.filter(
            ubicacion__bloque_programacion__programacion_semanal=self.programacion_semanal,
            estado__in=['programada', 'confirmada']
        ).aggregate(
            total_ingresos=Sum('cuña__precio_total')
        )
        
        self.total_ingresos_proyectados = resultado['total_ingresos'] or 0
        self.save()
    
    def save(self, *args, **kwargs):
        """Actualizar estadísticas al guardar"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Actualizar estadísticas después de guardar
        if not is_new:
            self.actualizar_estadisticas()