"""
Modelos para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Gestión de cuñas publicitarias y archivos de audio
"""

import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from mutagen import File as MutagenFile
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.mp4 import MP4

User = get_user_model()

def audio_upload_path(instance, filename):
    """
    Genera la ruta de subida para archivos de audio
    """
    # Crear directorio por año/mes
    now = timezone.now()
    year = now.year
    month = now.strftime('%m')
    
    # Generar nombre único preservando la extensión
    ext = filename.split('.')[-1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    return f"audio_spots/{year}/{month}/{unique_filename}"

class CategoriaPublicitaria(models.Model):
    """
    Categorías para clasificar el tipo de publicidad
    """
    
    nombre = models.CharField(
        'Nombre de la Categoría',
        max_length=100,
        unique=True,
        help_text='Nombre de la categoría publicitaria'
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción detallada de la categoría'
    )
    
    color_codigo = models.CharField(
        'Código de Color',
        max_length=7,
        default='#007bff',
        help_text='Color para identificar la categoría (formato hex)'
    )
    
    tarifa_base = models.DecimalField(
        'Tarifa Base',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Tarifa base por segundo para esta categoría'
    )
    
    is_active = models.BooleanField(
        'Activa',
        default=True,
        help_text='Si la categoría está activa para nuevas cuñas'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Categoría Publicitaria'
        verbose_name_plural = 'Categorías Publicitarias'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse('content:categoria_detail', kwargs={'pk': self.pk})

class TipoContrato(models.Model):
    """
    Tipos de contrato publicitario (paquetes, por tiempo, etc.)
    """
    
    DURACION_CHOICES = [
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('personalizado', 'Personalizado'),
    ]
    
    nombre = models.CharField(
        'Nombre del Tipo',
        max_length=100,
        unique=True
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True
    )
    
    duracion_tipo = models.CharField(
        'Tipo de Duración',
        max_length=20,
        choices=DURACION_CHOICES,
        default='mensual'
    )
    
    duracion_dias = models.PositiveIntegerField(
        'Duración en Días',
        default=30,
        help_text='Duración estándar del contrato en días'
    )
    
    repeticiones_minimas = models.PositiveIntegerField(
        'Repeticiones Mínimas',
        default=1,
        help_text='Número mínimo de repeticiones por día'
    )
    
    descuento_porcentaje = models.DecimalField(
        'Descuento (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Descuento aplicable a este tipo de contrato'
    )
    
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Tipo de Contrato'
        verbose_name_plural = 'Tipos de Contrato'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_duracion_tipo_display()})"

class ArchivoAudio(models.Model):
    """
    Archivo de audio de la cuña publicitaria
    """
    
    FORMATO_CHOICES = [
        ('mp3', 'MP3'),
        ('wav', 'WAV'),
        ('aac', 'AAC'),
        ('m4a', 'M4A'),
        ('ogg', 'OGG'),
    ]
    
    CALIDAD_CHOICES = [
        ('baja', 'Baja (128 kbps)'),
        ('media', 'Media (192 kbps)'),
        ('alta', 'Alta (320 kbps)'),
        ('sin_perdida', 'Sin Pérdida'),
    ]
    
    archivo = models.FileField(
        'Archivo de Audio',
        upload_to=audio_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'aac', 'm4a', 'ogg'])],
        help_text='Archivo de audio de la cuña publicitaria'
    )
    
    nombre_original = models.CharField(
        'Nombre Original',
        max_length=255,
        help_text='Nombre original del archivo subido'
    )
    
    formato = models.CharField(
        'Formato',
        max_length=10,
        choices=FORMATO_CHOICES,
        help_text='Formato del archivo de audio'
    )
    
    duracion_segundos = models.PositiveIntegerField(
        'Duración (segundos)',
        null=True,
        blank=True,
        help_text='Duración real del audio en segundos'
    )
    
    tamaño_bytes = models.PositiveBigIntegerField(
        'Tamaño (bytes)',
        null=True,
        blank=True,
        help_text='Tamaño del archivo en bytes'
    )
    
    bitrate = models.PositiveIntegerField(
        'Bitrate (kbps)',
        null=True,
        blank=True,
        help_text='Bitrate del audio en kbps'
    )
    
    sample_rate = models.PositiveIntegerField(
        'Sample Rate (Hz)',
        null=True,
        blank=True,
        help_text='Frecuencia de muestreo en Hz'
    )
    
    canales = models.PositiveIntegerField(
        'Canales',
        null=True,
        blank=True,
        help_text='Número de canales de audio (1=mono, 2=estéreo)'
    )
    
    calidad = models.CharField(
        'Calidad',
        max_length=20,
        choices=CALIDAD_CHOICES,
        null=True,
        blank=True,
        help_text='Calidad estimada del audio'
    )
    
    hash_archivo = models.CharField(
        'Hash del Archivo',
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text='Hash SHA256 del archivo para detectar duplicados'
    )
    
    metadatos_extra = models.JSONField(
        'Metadatos Adicionales',
        default=dict,
        blank=True,
        help_text='Metadatos adicionales extraídos del archivo'
    )
    
    subido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='archivos_audio_subidos',
        verbose_name='Subido por'
    )
    
    fecha_subida = models.DateTimeField('Fecha de Subida', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Archivo de Audio'
        verbose_name_plural = 'Archivos de Audio'
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f"{self.nombre_original} ({self.duracion_formateada})"
    
    def save(self, *args, **kwargs):
        """Override save para extraer metadatos automáticamente"""
        if self.archivo and not self.duracion_segundos:
            self.extraer_metadatos()
        super().save(*args, **kwargs)
    
    def extraer_metadatos(self):
        """
        Extrae metadatos del archivo de audio usando mutagen
        """
        try:
            if self.archivo and os.path.exists(self.archivo.path):
                # Obtener información básica del archivo
                self.tamaño_bytes = os.path.getsize(self.archivo.path)
                self.nombre_original = os.path.basename(self.archivo.name)
                
                # Detectar formato por extensión
                ext = os.path.splitext(self.archivo.name)[1].lower().lstrip('.')
                self.formato = ext if ext in dict(self.FORMATO_CHOICES) else 'mp3'
                
                # Extraer metadatos con mutagen
                audio_file = MutagenFile(self.archivo.path)
                
                if audio_file is not None:
                    # Duración
                    if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
                        self.duracion_segundos = int(audio_file.info.length)
                    
                    # Bitrate
                    if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'bitrate'):
                        self.bitrate = audio_file.info.bitrate
                        
                        # Determinar calidad basada en bitrate
                        if self.bitrate:
                            if self.bitrate < 160:
                                self.calidad = 'baja'
                            elif self.bitrate < 256:
                                self.calidad = 'media'
                            elif self.bitrate < 400:
                                self.calidad = 'alta'
                            else:
                                self.calidad = 'sin_perdida'
                    
                    # Sample rate
                    if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'sample_rate'):
                        self.sample_rate = audio_file.info.sample_rate
                    
                    # Canales
                    if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'channels'):
                        self.canales = audio_file.info.channels
                    
                    # Metadatos adicionales
                    if audio_file.tags:
                        self.metadatos_extra = {
                            'title': str(audio_file.tags.get('TIT2', [''])[0]) if audio_file.tags.get('TIT2') else '',
                            'artist': str(audio_file.tags.get('TPE1', [''])[0]) if audio_file.tags.get('TPE1') else '',
                            'album': str(audio_file.tags.get('TALB', [''])[0]) if audio_file.tags.get('TALB') else '',
                        }
                
        except Exception as e:
            # Si falla la extracción, continuar sin metadatos
            print(f"Error extrayendo metadatos: {e}")
    
    @property
    def duracion_formateada(self):
        """Retorna la duración en formato mm:ss"""
        if self.duracion_segundos:
            minutos = self.duracion_segundos // 60
            segundos = self.duracion_segundos % 60
            return f"{minutos:02d}:{segundos:02d}"
        return "00:00"
    
    @property
    def tamaño_formateado(self):
        """Retorna el tamaño en formato legible"""
        if self.tamaño_bytes:
            if self.tamaño_bytes < 1024:
                return f"{self.tamaño_bytes} B"
            elif self.tamaño_bytes < 1024**2:
                return f"{self.tamaño_bytes/1024:.1f} KB"
            elif self.tamaño_bytes < 1024**3:
                return f"{self.tamaño_bytes/(1024**2):.1f} MB"
            else:
                return f"{self.tamaño_bytes/(1024**3):.1f} GB"
        return "0 B"
    
    def get_absolute_url(self):
        return reverse('content:audio_detail', kwargs={'pk': self.pk})

class CuñaPublicitaria(models.Model):
    """
    Modelo principal para las cuñas publicitarias
    """
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente_revision', 'Pendiente de Revisión'),
        ('en_produccion', 'En Producción'),
        ('aprobada', 'Aprobada'),
        ('activa', 'Activa'),
        ('pausada', 'Pausada'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    # Información básica
    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único de la cuña (generado automáticamente)'
    )
    
    titulo = models.CharField(
        'Título',
        max_length=200,
        help_text='Título descriptivo de la cuña publicitaria'
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción detallada del contenido publicitario'
    )
    
    # Relaciones
    cliente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'groups__name': 'Clientes'},
        related_name='cuñas_publicitarias',
        verbose_name='Cliente'
    )
    
    vendedor_asignado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'groups__name': 'Vendedores'},
        related_name='cuñas_vendidas',
        verbose_name='Vendedor Asignado'
    )
    
    categoria = models.ForeignKey(
        CategoriaPublicitaria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuñas',
        verbose_name='Categoría'
    )
    
    tipo_contrato = models.ForeignKey(
        TipoContrato,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuñas',
        verbose_name='Tipo de Contrato'
    )
    
    archivo_audio = models.ForeignKey(
        ArchivoAudio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuñas',
        verbose_name='Archivo de Audio'
    )
    
    # Estado y prioridad
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='borrador',
        help_text='Estado actual de la cuña'
    )
    
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='normal',
        help_text='Prioridad de la cuña'
    )
    
    # Información técnica
    duracion_planeada = models.PositiveIntegerField(
        'Duración Planeada (segundos)',
        help_text='Duración planeada de la cuña en segundos'
    )
    
    # Información comercial
    precio_total = models.DecimalField(
        'Precio Total',
        max_digits=10,
        decimal_places=2,
        help_text='Precio total del contrato publicitario'
    )
    
    precio_por_segundo = models.DecimalField(
        'Precio por Segundo',
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Precio por segundo de duración'
    )
    
    repeticiones_dia = models.PositiveIntegerField(
        'Repeticiones por Día',
        default=1,
        help_text='Número de veces que se reproduce por día'
    )
    
    # Fechas del contrato
    fecha_inicio = models.DateField(
        'Fecha de Inicio',
        help_text='Fecha de inicio de la campaña publicitaria'
    )
    
    fecha_fin = models.DateField(
        'Fecha de Fin',
        help_text='Fecha de finalización de la campaña publicitaria'
    )
    
    # Información de aprobación
    aprobada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuñas_aprobadas',
        verbose_name='Aprobada por'
    )
    
    fecha_aprobacion = models.DateTimeField(
        'Fecha de Aprobación',
        null=True,
        blank=True
    )
    
    observaciones = models.TextField(
        'Observaciones',
        blank=True,
        help_text='Observaciones sobre la cuña publicitaria'
    )
    
    # Configuraciones adicionales
    requiere_aprobacion = models.BooleanField(
        'Requiere Aprobación',
        default=True,
        help_text='Si la cuña requiere aprobación antes de ser transmitida'
    )
    
    permite_edicion = models.BooleanField(
        'Permite Edición',
        default=True,
        help_text='Si la cuña puede ser editada después de creada'
    )
    
    notificar_vencimiento = models.BooleanField(
        'Notificar Vencimiento',
        default=True,
        help_text='Si notificar cuando esté próxima a vencer'
    )
    
    dias_aviso_vencimiento = models.PositiveIntegerField(
        'Días de Aviso de Vencimiento',
        default=7,
        help_text='Días antes del vencimiento para enviar notificación'
    )
    
    # Tags y palabras clave
    tags = models.CharField(
        'Tags',
        max_length=500,
        blank=True,
        help_text='Palabras clave separadas por comas para búsqueda'
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cuñas_creadas',
        verbose_name='Creada por'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Cuña Publicitaria'
        verbose_name_plural = 'Cuñas Publicitarias'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['estado', 'fecha_inicio']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['vendedor_asignado', 'estado']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        """Override save para generar código automáticamente"""
        if not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Calcular precio por segundo si no está definido
        if not self.precio_por_segundo and self.duracion_planeada:
            self.precio_por_segundo = self.precio_total / self.duracion_planeada
        
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        """Genera un código único para la cuña"""
        año = timezone.now().year
        mes = timezone.now().month
        
        # Contar cuñas del mes actual
        count = CuñaPublicitaria.objects.filter(
            created_at__year=año,
            created_at__month=mes
        ).count() + 1
        
        return f"CP{año}{mes:02d}{count:04d}"
    
    def clean(self):
        """Validaciones personalizadas"""
        # Validar fechas
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Validar duración vs archivo de audio
        if self.archivo_audio and self.archivo_audio.duracion_segundos:
            diferencia = abs(self.duracion_planeada - self.archivo_audio.duracion_segundos)
            if diferencia > 5:  # Tolerancia de 5 segundos
                raise ValidationError(
                    f'La duración planeada ({self.duracion_planeada}s) difiere mucho '
                    f'del archivo de audio ({self.archivo_audio.duracion_segundos}s).'
                )
    
    @property
    def dias_restantes(self):
        """Calcula los días restantes hasta el fin de la campaña"""
        if self.fecha_fin:
            hoy = timezone.now().date()
            if self.fecha_fin >= hoy:
                return (self.fecha_fin - hoy).days
            return 0
        return None
    
    @property
    def esta_activa(self):
        """Verifica si la cuña está en periodo activo"""
        hoy = timezone.now().date()
        return (
            self.estado == 'activa' and
            self.fecha_inicio <= hoy <= self.fecha_fin
        )
    
    @property
    def esta_vencida(self):
        """Verifica si la cuña está vencida"""
        hoy = timezone.now().date()
        return self.fecha_fin < hoy if self.fecha_fin else False
    
    @property
    def requiere_notificacion_vencimiento(self):
        """Verifica si debe notificar por próximo vencimiento"""
        if not self.notificar_vencimiento or not self.fecha_fin:
            return False
        
        hoy = timezone.now().date()
        dias_hasta_vencimiento = (self.fecha_fin - hoy).days
        
        return (
            0 <= dias_hasta_vencimiento <= self.dias_aviso_vencimiento and
            self.estado in ['activa', 'aprobada']
        )
    
    @property
    def duracion_total_dias(self):
        """Calcula la duración total de la campaña en días"""
        if self.fecha_inicio and self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).days + 1
        return 0
    
    @property
    def reproducciones_totales(self):
        """Calcula el total de reproducciones planeadas"""
        return self.duracion_total_dias * self.repeticiones_dia
    
    @property
    def costo_por_reproduccion(self):
        """Calcula el costo por cada reproducción"""
        if self.reproducciones_totales > 0:
            return self.precio_total / self.reproducciones_totales
        return Decimal('0.00')
    
    @property
    def semaforo_estado(self):
        """Determina color de semáforo basado en estado y fechas"""
        if self.esta_vencida:
            return 'rojo'
        elif self.requiere_notificacion_vencimiento:
            return 'amarillo'
        elif self.estado in ['activa', 'aprobada']:
            return 'verde'
        elif self.estado in ['cancelada', 'finalizada']:
            return 'gris'
        else:
            return 'amarillo'
    
    def aprobar(self, user):
        """Aprueba la cuña publicitaria"""
        self.estado = 'aprobada'
        self.aprobada_por = user
        self.fecha_aprobacion = timezone.now()
        self.save()
    
    def activar(self):
        """Activa la cuña publicitaria"""
        if self.estado == 'aprobada':
            self.estado = 'activa'
            self.save()
    
    def pausar(self):
        """Pausa la cuña publicitaria"""
        if self.estado == 'activa':
            self.estado = 'pausada'
            self.save()
    
    def finalizar(self):
        """Finaliza la cuña publicitaria"""
        self.estado = 'finalizada'
        self.save()
    
    def get_absolute_url(self):
        return reverse('content:cuña_detail', kwargs={'pk': self.pk})

class HistorialCuña(models.Model):
    """
    Historial de cambios de las cuñas publicitarias
    """
    
    ACCION_CHOICES = [
        ('creada', 'Creada'),
        ('editada', 'Editada'),
        ('aprobada', 'Aprobada'),
        ('activada', 'Activada'),
        ('pausada', 'Pausada'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
        ('audio_subido', 'Audio Subido'),
        ('audio_cambiado', 'Audio Cambiado'),
    ]
    
    cuña = models.ForeignKey(
        CuñaPublicitaria,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Cuña'
    )
    
    accion = models.CharField(
        'Acción',
        max_length=20,
        choices=ACCION_CHOICES
    )
    
    usuario = models.ForeignKey(
        User,
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
        verbose_name = 'Historial de Cuña'
        verbose_name_plural = 'Historial de Cuñas'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.cuña.codigo} - {self.get_accion_display()} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

# Señales para crear automáticamente el historial
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=CuñaPublicitaria)
def cuña_pre_save(sender, instance, **kwargs):
    """Captura el estado anterior antes de guardar"""
    if instance.pk:
        try:
            instance._estado_anterior = CuñaPublicitaria.objects.get(pk=instance.pk)
        except CuñaPublicitaria.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None

@receiver(post_save, sender=CuñaPublicitaria)
def cuña_post_save(sender, instance, created, **kwargs):
    """Crea entrada en el historial después de guardar"""
    if created:
        # Cuña creada
        HistorialCuña.objects.create(
            cuña=instance,
            accion='creada',
            usuario=getattr(instance, 'created_by', None),
            descripcion=f'Cuña publicitaria "{instance.titulo}" creada',
            datos_nuevos={
                'titulo': instance.titulo,
                'estado': instance.estado,
                'precio_total': str(instance.precio_total),
                'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
                'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
            }
        )
    else:
        # Cuña editada - verificar cambios
        estado_anterior = getattr(instance, '_estado_anterior', None)
        if estado_anterior:
            cambios = []
            
            # Verificar cambio de estado
            if estado_anterior.estado != instance.estado:
                cambios.append(f"Estado: {estado_anterior.get_estado_display()} → {instance.get_estado_display()}")
                
                # Crear entrada específica para cambios de estado importantes
                if instance.estado == 'aprobada':
                    HistorialCuña.objects.create(
                        cuña=instance,
                        accion='aprobada',
                        usuario=instance.aprobada_por,
                        descripcion=f'Cuña aprobada por {instance.aprobada_por}',
                        datos_anteriores={'estado': estado_anterior.estado},
                        datos_nuevos={'estado': instance.estado, 'aprobada_por': instance.aprobada_por.username if instance.aprobada_por else None}
                    )
            
            # Verificar otros cambios importantes
            if estado_anterior.archivo_audio != instance.archivo_audio:
                accion = 'audio_subido' if not estado_anterior.archivo_audio else 'audio_cambiado'
                HistorialCuña.objects.create(
                    cuña=instance,
                    accion=accion,
                    usuario=getattr(instance, '_user_modificador', None),
                    descripcion=f'Archivo de audio {"subido" if accion == "audio_subido" else "cambiado"}',
                    datos_anteriores={'archivo_audio': str(estado_anterior.archivo_audio) if estado_anterior.archivo_audio else None},
                    datos_nuevos={'archivo_audio': str(instance.archivo_audio) if instance.archivo_audio else None}
                )
            
            # Si hay otros cambios, crear entrada genérica
            if (estado_anterior.titulo != instance.titulo or 
                estado_anterior.precio_total != instance.precio_total or
                estado_anterior.fecha_inicio != instance.fecha_inicio or
                estado_anterior.fecha_fin != instance.fecha_fin):
                
                HistorialCuña.objects.create(
                    cuña=instance,
                    accion='editada',
                    usuario=getattr(instance, '_user_modificador', None),
                    descripcion='Cuña publicitaria editada',
                    datos_anteriores={
                        'titulo': estado_anterior.titulo,
                        'precio_total': str(estado_anterior.precio_total),
                        'fecha_inicio': estado_anterior.fecha_inicio.isoformat() if estado_anterior.fecha_inicio else None,
                        'fecha_fin': estado_anterior.fecha_fin.isoformat() if estado_anterior.fecha_fin else None,
                    },
                    datos_nuevos={
                        'titulo': instance.titulo,
                        'precio_total': str(instance.precio_total),
                        'fecha_inicio': instance.fecha_inicio.isoformat() if instance.fecha_inicio else None,
                        'fecha_fin': instance.fecha_fin.isoformat() if instance.fecha_fin else None,
                    }
                )