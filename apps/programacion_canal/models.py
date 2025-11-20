from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()
class CategoriaPrograma(models.Model):
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    nombre = models.CharField(_('Nombre de la Categoría'), max_length=100, unique=True)
    descripcion = models.TextField(_('Descripción'), blank=True)
    color = models.CharField(_('Color'), max_length=7, default='#3498db', help_text='Color hexadecimal para identificar la categoría', blank=True)
    estado = models.CharField(_('Estado'), max_length=10, choices=ESTADO_CHOICES, default='activo')
    orden = models.PositiveIntegerField(_('Orden'), default=0, help_text='Orden de visualización', blank=True, null=True)
    
    # Metadatos
    created_at = models.DateTimeField(_('Creado'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado'), auto_now=True)
    
    class Meta:
        verbose_name = _('Categoría de Programa')
        verbose_name_plural = _('Categorías de Programas')
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        # Si no se especifica orden, asignar el siguiente disponible
        if self.orden is None:
            max_orden = CategoriaPrograma.objects.aggregate(models.Max('orden'))['orden__max']
            self.orden = (max_orden or 0) + 1
        super().save(*args, **kwargs)
class Programa(models.Model):
    TIPO_PROGRAMA_CHOICES = [
        ('noticiero', 'Noticiero'),
        ('entretenimiento', 'Entretenimiento'),
        ('deportivo', 'Deportivo'),
        ('cultural', 'Cultural'),
        ('educativo', 'Educativo'),
        ('musical', 'Musical'),
        ('variedades', 'Variedades'),
        ('pelicula', 'Película'),
        ('serie', 'Serie'),
        ('documental', 'Documental'),
        ('otros', 'Otros'),
    ]
    
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('en_produccion', 'En Producción'),
    ]
    
    # Información básica
    nombre = models.CharField(_('Nombre del Programa'), max_length=200)
    descripcion = models.TextField(_('Descripción'), blank=True)
    
    # Categoría personalizada (nuevo campo)
    categoria = models.ForeignKey(
        CategoriaPrograma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programas',
        verbose_name=_('Categoría')
    )
    
    # Tipo como respaldo (mantener para compatibilidad)
    tipo = models.CharField(_('Tipo'), max_length=20, choices=TIPO_PROGRAMA_CHOICES, default='entretenimiento')
    
    # Duración y características
    duracion_estandar = models.DurationField(_('Duración Estándar'), help_text='Duración típica del programa (HH:MM:SS)')
    codigo = models.CharField(_('Código'), max_length=20, unique=True, help_text='Código único del programa')
    
    # Estado y metadatos
    estado = models.CharField(_('Estado'), max_length=15, choices=ESTADO_CHOICES, default='activo')
    color = models.CharField(_('Color en calendario'), max_length=7, default='#3498db', help_text='Color hexadecimal para el calendario')
    
    # Para series
    es_serie = models.BooleanField(_('Es una serie'), default=False)
    temporada = models.PositiveIntegerField(_('Temporada'), null=True, blank=True)
    episodio = models.PositiveIntegerField(_('Episodio'), null=True, blank=True)
    titulo_episodio = models.CharField(_('Título del Episodio'), max_length=200, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(_('Creado'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado'), auto_now=True)
    
    class Meta:
        verbose_name = _('Programa')
        verbose_name_plural = _('Programas')
        ordering = ['nombre']
    
    def __str__(self):
        if self.es_serie and self.titulo_episodio:
            return f"{self.nombre} - S{self.temporada}E{self.episodio}: {self.titulo_episodio}"
        elif self.es_serie:
            return f"{self.nombre} - S{self.temporada}E{self.episodio}"
        return self.nombre
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        from django.utils.text import slugify
        base_code = slugify(self.nombre).upper()[:15]
        timestamp = str(int(timezone.now().timestamp()))[-4:]
        return f"PRG{base_code}{timestamp}"

class ProgramacionSemanal(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('publicada', 'Publicada'),
        ('en_emision', 'En Emisión'),
        ('completada', 'Completada'),
    ]
    
    # Identificación
    nombre = models.CharField(_('Nombre de la Programación'), max_length=200)
    codigo = models.CharField(_('Código'), max_length=20, unique=True)
    
    # Periodo
    fecha_inicio_semana = models.DateField(_('Inicio de Semana'), help_text='Lunes de la semana programada')
    fecha_fin_semana = models.DateField(_('Fin de Semana'), help_text='Domingo de la semana programada')
    
    # Estado
    estado = models.CharField(_('Estado'), max_length=15, choices=ESTADO_CHOICES, default='borrador')
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='programaciones_semanales_creadas',
        verbose_name=_('Creado por')
    )
    created_at = models.DateTimeField(_('Creado'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado'), auto_now=True)
    
    class Meta:
        verbose_name = _('Programación Semanal')
        verbose_name_plural = _('Programaciones Semanales')
        ordering = ['-fecha_inicio_semana']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.fecha_inicio_semana} al {self.fecha_fin_semana})"
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        from django.utils.text import slugify
        import time
    
        # Generar código más corto y único
        fecha_str = self.fecha_inicio_semana.strftime("%y%m%d")  # YYMMDD en lugar de YYYYMMDD
        timestamp = str(int(time.time()))[-4:]  # Últimos 4 dígitos del timestamp
    
        # Código más corto: PRG + Fecha(YYMMDD) + Timestamp(4)
        return f"PRG{fecha_str}{timestamp}"
    
    def clean(self):
        if self.fecha_fin_semana <= self.fecha_inicio_semana:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Verificar que sea un lunes
        if self.fecha_inicio_semana.weekday() != 0:
            raise ValidationError('La fecha de inicio debe ser un lunes.')
        
        # Verificar que sea un domingo
        if self.fecha_fin_semana.weekday() != 6:
            raise ValidationError('La fecha de fin debe ser un domingo.')

class BloqueProgramacion(models.Model):
    DIA_SEMANA_CHOICES = [
        (0, _('Lunes')),
        (1, _('Martes')),
        (2, _('Miércoles')),
        (3, _('Jueves')),
        (4, _('Viernes')),
        (5, _('Sábado')),
        (6, _('Domingo')),
    ]
    
    # Relaciones
    programacion_semanal = models.ForeignKey(
        ProgramacionSemanal,
        on_delete=models.CASCADE,
        related_name='bloques',
        verbose_name=_('Programación Semanal')
    )
    
    programa = models.ForeignKey(
        Programa,
        on_delete=models.CASCADE,
        related_name='bloques_programacion',
        verbose_name=_('Programa')
    )
    
    # Tiempo
    dia_semana = models.PositiveIntegerField(_('Día de la Semana'), choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField(_('Hora de Inicio'))
    duracion_real = models.DurationField(_('Duración Real'), help_text='Duración real en emisión (HH:MM:SS)')
    
    # Información adicional
    es_repeticion = models.BooleanField(_('Es Repetición'), default=False)
    notas = models.TextField(_('Notas'), blank=True, help_text='Notas adicionales sobre este bloque')
    
    # Metadatos
    created_at = models.DateTimeField(_('Creado'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado'), auto_now=True)
    
    class Meta:
        verbose_name = _('Bloque de Programación')
        verbose_name_plural = _('Bloques de Programación')
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['programacion_semanal', 'dia_semana', 'hora_inicio']
    
    def __str__(self):
        dia = dict(self.DIA_SEMANA_CHOICES)[self.dia_semana]
        return f"{dia} {self.hora_inicio} - {self.programa.nombre}"
    
    @property
    def hora_fin(self):
        from datetime import datetime, timedelta
        hora_base = datetime(2000, 1, 1, self.hora_inicio.hour, self.hora_inicio.minute)
        hora_fin = hora_base + self.duracion_real
        return hora_fin.time()
    
    def clean(self):
        # Verificar que no haya solapamientos
        bloques_mismo_dia = BloqueProgramacion.objects.filter(
            programacion_semanal=self.programacion_semanal,
            dia_semana=self.dia_semana
        ).exclude(pk=self.pk if self.pk else None)
        
        for bloque in bloques_mismo_dia:
            if self.hay_solapamiento(bloque):
                raise ValidationError(
                    f'El bloque se solapa con {bloque.programa.nombre} '
                    f'({bloque.hora_inicio} - {bloque.hora_fin})'
                )
    
    def hay_solapamiento(self, otro_bloque):
        """Verifica si este bloque se solapa con otro bloque"""
        if self.hora_inicio < otro_bloque.hora_fin and self.hora_fin > otro_bloque.hora_inicio:
            return True
        return False
