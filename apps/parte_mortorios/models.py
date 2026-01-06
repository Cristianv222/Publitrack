from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from decimal import Decimal
from django.core.validators import FileExtensionValidator
import uuid
class ParteMortorio(models.Model):
    """
    Modelo para gestionar partes mortuorios (transmisiones por fallecimiento)
    """
    
    ESTADO_CHOICES = [
        ('pendiente', '🟡 Pendiente'),
        ('al_aire', '🟢 Al Aire'), 
        ('pausado', '⏸️ Pausado'),
        ('finalizado', '🔴 Finalizado'),
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
    
    # QUITAMOS precio_por_segundo y dejamos solo precio_total
    precio_total = models.DecimalField(
        'Precio Total',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Precio total del parte mortorio'
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
        """Genera código automáticamente si no existe"""
        if not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Ya no calculamos automáticamente el precio
        # El precio total se ingresa manualmente ahora
        
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
        if self.nombres_hijos:
            resumen.append(f"Nombres hijos: {self.nombres_hijos}")
        if self.familiares_adicionales:
            resumen.append(f"Familiares adicionales: {self.familiares_adicionales}")
        return ", ".join(resumen) if resumen else "Sin información familiar adicional"

    def clean(self):
        """Validaciones adicionales del modelo"""
        errors = {}
        
        # Validar que fecha_fin_transmision no sea anterior a fecha_inicio_transmision
        if self.fecha_inicio_transmision and self.fecha_fin_transmision:
            if self.fecha_fin_transmision < self.fecha_inicio_transmision:
                errors['fecha_fin_transmision'] = 'La fecha de fin no puede ser anterior a la fecha de inicio'
        
        # Validar que hijos vivos + fallecidos no superen la cantidad total
        if self.hijos_vivos + self.hijos_fallecidos > self.cantidad_hijos:
            errors['cantidad_hijos'] = 'La suma de hijos vivos y fallecidos no puede ser mayor a la cantidad total de hijos'
        
        if errors:
            raise ValidationError(errors)


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

    @classmethod
    def registrar_cambio(cls, parte_mortorio, usuario, accion, descripcion, datos_anteriores=None, datos_nuevos=None):
        """
        Método helper para registrar cambios en el historial
        """
        return cls.objects.create(
            parte_mortorio=parte_mortorio,
            usuario=usuario,
            accion=accion,
            descripcion=descripcion,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos
        )

# ==================== FUNCIONES PARA RUTAS ====================

def parte_mortorio_template_path(instance, filename):
    """Genera la ruta de subida para plantillas de parte mortorio"""
    ext = filename.split('.')[-1].lower()
    unique_filename = f"template_parte_mortorio_{uuid.uuid4().hex}.{ext}"
    return f"parte_mortorio_templates/{unique_filename}"

def parte_mortorio_output_path(instance, filename):
    """Genera la ruta para partes mortorios PDF generados"""
    ext = filename.split('.')[-1].lower()
    unique_filename = f"parte_mortorio_{instance.numero_parte}_{uuid.uuid4().hex[:8]}.{ext}"
    return f"staticfiles/partes_mortorios/{unique_filename}"

# ==================== MODELOS DE PLANTILLAS ====================

class PlantillaParteMortorio(models.Model):
    """
    Plantillas para partes mortorios en formato Word
    """
    
    TIPO_PARTE_CHOICES = [
        ('transmision_simple', 'Transmisión Simple'),
        ('transmision_completa', 'Transmisión Completa'),
        ('anuncio_especial', 'Anuncio Especial'),
        ('recordatorio', 'Recordatorio'),
        ('otro', 'Otro'),
    ]
    
    nombre = models.CharField(
        'Nombre de la Plantilla',
        max_length=200,
        help_text='Nombre descriptivo (ej: Parte Mortorio Completo 2025)'
    )
    
    tipo_parte = models.CharField(
        'Tipo de Parte',
        max_length=50,
        choices=TIPO_PARTE_CHOICES,
        default='transmision_simple',
        help_text='Tipo de parte mortorio que representa esta plantilla'
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción de cuándo usar esta plantilla'
    )
    
    archivo_plantilla = models.FileField(
        'Archivo de Plantilla (.docx)',
        upload_to=parte_mortorio_template_path,
        validators=[FileExtensionValidator(allowed_extensions=['docx'])],
        help_text='Archivo Word con marcadores: {{NOMBRE_FALLECIDO}}, {{FECHA_FALLECIMIENTO}}, etc.'
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
        related_name='plantillas_parte_mortorio_creadas',
        verbose_name='Creada por'
    )
    
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Plantilla de Parte Mortorio'
        verbose_name_plural = 'Plantillas de Parte Mortorio'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.nombre} (v{self.version})"
    
    def save(self, *args, **kwargs):
        """Override save para generar variables disponibles"""
        if not self.variables_disponibles:
            self.variables_disponibles = {
                'NUMERO_PARTE': 'Número único del parte mortorio',
                'CODIGO_PARTE': 'Código del parte mortorio',
                'NOMBRE_FALLECIDO': 'Nombre completo del fallecido',
                'EDAD_FALLECIDO': 'Edad del fallecido',
                'DNI_FALLECIDO': 'DNI del fallecido',
                'FECHA_NACIMIENTO': 'Fecha de nacimiento del fallecido',
                'FECHA_FALLECIMIENTO': 'Fecha de fallecimiento',
                'NOMBRE_ESPOSA': 'Nombre de la esposa/esposo',
                'CANTIDAD_HIJOS': 'Cantidad total de hijos',
                'HIJOS_VIVOS': 'Número de hijos vivos',
                'HIJOS_FALLECIDOS': 'Número de hijos fallecidos',
                'NOMBRES_HIJOS': 'Nombres de todos los hijos',
                'FAMILIARES_ADICIONALES': 'Familiares adicionales',
                'TIPO_CEREMONIA': 'Tipo de ceremonia',
                'FECHA_MISA': 'Fecha de misa/velatorio',
                'HORA_MISA': 'Hora de misa/velatorio',
                'LUGAR_MISA': 'Lugar de la ceremonia',
                'FECHA_INICIO_TRANSMISION': 'Fecha inicio transmisión',
                'FECHA_FIN_TRANSMISION': 'Fecha fin transmisión',
                'HORA_TRANSMISION': 'Hora de transmisión',
                'DURACION_TRANSMISION': 'Duración en minutos',
                'REPETICIONES_DIA': 'Repeticiones por día',
                'PRECIO_TOTAL': 'Precio total del parte',
                'PRECIO_TOTAL_LETRAS': 'Precio total en letras',
                'URGENCIA': 'Nivel de urgencia',
                'ESTADO': 'Estado del parte',
                'MENSAJE_PERSONALIZADO': 'Mensaje especial',
                'OBSERVACIONES': 'Observaciones adicionales',
                'NOMBRE_CLIENTE': 'Nombre del cliente/familiar',
                'RUC_DNI_CLIENTE': 'RUC/DNI del cliente',
                'EMPRESA_CLIENTE': 'Empresa del cliente',
                'TELEFONO_CLIENTE': 'Teléfono del cliente',
                'EMAIL_CLIENTE': 'Email del cliente',
                'DIRECCION_CLIENTE': 'Dirección del cliente',
                'FECHA_SOLICITUD': 'Fecha de solicitud',
                'FECHA_ACTUAL': 'Fecha actual de generación',
                'RESUMEN_FAMILIA': 'Resumen de información familiar',
            }
        
        # Si se marca como default, desmarcar las demás
        if self.is_default:
            PlantillaParteMortorio.objects.filter(
                tipo_parte=self.tipo_parte,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('custom_admin:plantilla_parte_mortorio_detail', kwargs={'pk': self.pk})


class ParteMortorioGenerado(models.Model):
    """
    Partes mortorios generados a partir de plantillas
    """
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('generado', 'Generado'),
        ('impreso', 'Impreso'),
        ('validado', 'Validado'),
        ('transmitido', 'Transmitido'),
        ('cancelado', 'Cancelado'),
    ]
    
    numero_parte = models.CharField('Número de Parte', max_length=50, unique=True)
    parte_mortorio = models.ForeignKey(
        'ParteMortorio', 
        on_delete=models.CASCADE, 
        related_name='partes_generados',
        verbose_name='Parte Mortorio'
    )
    plantilla_usada = models.ForeignKey(
        'PlantillaParteMortorio', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='partes_generados', 
        verbose_name='Plantilla Utilizada'
    )
    
    # Archivos
    archivo_parte_pdf = models.FileField(
        'Parte en PDF', 
        upload_to=parte_mortorio_output_path, 
        blank=True, 
        null=True
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
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, 
        related_name='partes_mortorio_generados_por', 
        verbose_name='Generado por'
    )
    impreso_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='partes_mortorio_impresos_por', 
        verbose_name='Impreso por'
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        related_name='partes_mortorio_validadas_por', 
        verbose_name='Validado por'
    )
    
    observaciones = models.TextField('Observaciones', blank=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)

    class Meta:
        verbose_name = 'Parte Mortorio Generado'
        verbose_name_plural = 'Partes Mortorios Generados'
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"Parte {self.numero_parte} - {self.parte_mortorio.nombre_fallecido}"

    def save(self, *args, **kwargs):
        if not self.numero_parte:
            self.numero_parte = self.generar_numero_parte()
        super().save(*args, **kwargs)

    def generar_numero_parte(self):
        """Genera número único para el parte generado"""
        año = timezone.now().year
        mes = timezone.now().month
        for intento in range(1, 100):
            count = ParteMortorioGenerado.objects.filter(
                fecha_generacion__year=año,
                fecha_generacion__month=mes
            ).count() + intento
            numero = f"PMG{año}{mes:02d}{count:04d}"
            if not ParteMortorioGenerado.objects.filter(numero_parte=numero).exists():
                return numero
        raise Exception("No se pudo generar un número de parte único")

    def generar_parte_pdf(self):
        """Genera el PDF del parte mortorio"""
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
            parte_mortorio = self.parte_mortorio

            # Función helper para formatear fechas en español
            def formatear_fecha_espanol(fecha):
                if not fecha:
                    return ''
                meses = {
                    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
                }
                return f"{fecha.day:02d} de {meses[fecha.month]} del {fecha.year}"

            # Preparar contexto
            context = {
                'NUMERO_PARTE': self.numero_parte,
                'CODIGO_PARTE': parte_mortorio.codigo,
                'NOMBRE_FALLECIDO': parte_mortorio.nombre_fallecido or '',
                'EDAD_FALLECIDO': str(parte_mortorio.edad_fallecido) if parte_mortorio.edad_fallecido else '',
                'DNI_FALLECIDO': parte_mortorio.dni_fallecido or '',
                'FECHA_NACIMIENTO': formatear_fecha_espanol(parte_mortorio.fecha_nacimiento),
                'FECHA_FALLECIMIENTO': formatear_fecha_espanol(parte_mortorio.fecha_fallecimiento),
                'NOMBRE_ESPOSA': parte_mortorio.nombre_esposa or '',
                'CANTIDAD_HIJOS': str(parte_mortorio.cantidad_hijos),
                'HIJOS_VIVOS': str(parte_mortorio.hijos_vivos),
                'HIJOS_FALLECIDOS': str(parte_mortorio.hijos_fallecidos),
                'NOMBRES_HIJOS': parte_mortorio.nombres_hijos or '',
                'FAMILIARES_ADICIONALES': parte_mortorio.familiares_adicionales or '',
                'TIPO_CEREMONIA': parte_mortorio.get_tipo_ceremonia_display(),
                'FECHA_MISA': formatear_fecha_espanol(parte_mortorio.fecha_misa),
                'HORA_MISA': parte_mortorio.hora_misa.strftime('%H:%M') if parte_mortorio.hora_misa else '',
                'LUGAR_MISA': parte_mortorio.lugar_misa or '',
                'FECHA_INICIO_TRANSMISION': formatear_fecha_espanol(parte_mortorio.fecha_inicio_transmision),
                'FECHA_FIN_TRANSMISION': formatear_fecha_espanol(parte_mortorio.fecha_fin_transmision),
                'HORA_TRANSMISION': parte_mortorio.hora_transmision.strftime('%H:%M') if parte_mortorio.hora_transmision else '',
                'DURACION_TRANSMISION': str(parte_mortorio.duracion_transmision),
                'REPETICIONES_DIA': str(parte_mortorio.repeticiones_dia),
                'PRECIO_TOTAL': f"{parte_mortorio.precio_total:.2f}",
                'PRECIO_TOTAL_LETRAS': numero_a_letras(parte_mortorio.precio_total),
                'URGENCIA': parte_mortorio.get_urgencia_display(),
                'ESTADO': parte_mortorio.get_estado_display(),
                'MENSAJE_PERSONALIZADO': parte_mortorio.mensaje_personalizado or '',
                'OBSERVACIONES': parte_mortorio.observaciones or '',
                'NOMBRE_CLIENTE': parte_mortorio.cliente.get_full_name() if parte_mortorio.cliente else '',
                'RUC_DNI_CLIENTE': parte_mortorio.cliente.ruc_dni if parte_mortorio.cliente else '',
                'EMPRESA_CLIENTE': parte_mortorio.cliente.empresa if parte_mortorio.cliente else '',
                'TELEFONO_CLIENTE': parte_mortorio.cliente.telefono if parte_mortorio.cliente else '',
                'EMAIL_CLIENTE': parte_mortorio.cliente.email if parte_mortorio.cliente else '',
                'DIRECCION_CLIENTE': parte_mortorio.cliente.direccion_exacta if parte_mortorio.cliente else '',
                'FECHA_SOLICITUD': formatear_fecha_espanol(parte_mortorio.fecha_solicitud),
                'FECHA_ACTUAL': formatear_fecha_espanol(timezone.now()),
                'RESUMEN_FAMILIA': parte_mortorio.resumen_familia,
            }

            print(f"📋 Contexto preparado para {self.numero_parte}")

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
                pdf_filename = f"parte_mortorio_{self.numero_parte}.pdf"
                self.archivo_parte_pdf.save(pdf_filename, ContentFile(pdf_content), save=False)

            # Limpiar archivos temporales
            try:
                if os.path.exists(temp_docx_path):
                    os.remove(temp_docx_path)
                if temp_pdf_path != temp_docx_path and os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
            except Exception as e:
                print(f"⚠️ Error limpiando temporales: {e}")

            self.estado = 'generado'
            self.save()
            
            print(f"✅ Parte mortorio PDF generado exitosamente: {self.archivo_parte_pdf.url}")
            return True

        except Exception as e:
            print(f'❌ Error generando parte mortorio PDF: {str(e)}')
            import traceback
            print(f'📋 Traceback: {traceback.format_exc()}')
            return False

    def marcar_como_impreso(self, user):
        self.estado = 'impreso'
        self.impreso_por = user
        self.fecha_impresion = timezone.now()
        self.save()

    def marcar_como_validado(self, user):
        self.estado = 'validado'
        self.validado_por = user
        self.fecha_validacion = timezone.now()
        self.save()

    @property
    def puede_regenerar(self):
        return self.estado in ('borrador', 'generado')

    def get_absolute_url(self):
        return reverse('custom_admin:parte_mortorio_generado_detail', kwargs={'pk': self.pk})


# ==================== FUNCIONES AUXILIARES ====================

def numero_a_letras(numero):
    """
    Convierte un número a letras (para el precio total en letras)
    """
    try:
        from decimal import Decimal
        numero = Decimal(str(numero))
        
        # Parte entera
        entero = int(numero)
        decimales = int((numero - entero) * 100)
        
        # Conversión básica
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
            resultado_entero = str(entero)
            
        if decimales > 0:
            return f"{resultado_entero} CON {decimales:02d}/100 DÓLARES"
        else:
            return f"{resultado_entero} EXACTOS DÓLARES"
            
    except:
        return "CANTIDAD EN NÚMEROS"