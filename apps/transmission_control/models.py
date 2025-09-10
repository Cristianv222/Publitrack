"""
Modelos para el módulo de Control de Transmisiones
Sistema PubliTrack - Gestión y programación de transmisiones de publicidad radial
"""

import uuid
from datetime import datetime, timedelta, time
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, Count


class ConfiguracionTransmision(models.Model):
    """
    Configuración global del sistema de transmisiones
    """
    
    MODO_OPERACION_CHOICES = [
        ('automatico', 'Automático'),
        ('manual', 'Manual'),
        ('programado', 'Programado'),
        ('mantenimiento', 'Mantenimiento'),
    ]
    
    ESTADO_SISTEMA_CHOICES = [
        ('activo', 'Activo'),
        ('pausado', 'Pausado'),
        ('detenido', 'Detenido'),
        ('error', 'Error'),
        ('mantenimiento', 'Mantenimiento'),
    ]
    
    # Configuración principal
    nombre_configuracion = models.CharField(
        'Nombre de Configuración',
        max_length=100,
        unique=True,
        help_text='Nombre descriptivo de esta configuración'
    )
    
    modo_operacion = models.CharField(
        'Modo de Operación',
        max_length=20,
        choices=MODO_OPERACION_CHOICES,
        default='programado',
        help_text='Modo de operación del sistema'
    )
    
    estado_sistema = models.CharField(
        'Estado del Sistema',
        max_length=20,
        choices=ESTADO_SISTEMA_CHOICES,
        default='activo',
        help_text='Estado actual del sistema de transmisión'
    )
    
    # Configuración de horarios
    hora_inicio_transmision = models.TimeField(
        'Hora de Inicio',
        default=time(6, 0),
        help_text='Hora de inicio de transmisiones diarias'
    )
    
    hora_fin_transmision = models.TimeField(
        'Hora de Fin',
        default=time(22, 0),
        help_text='Hora de fin de transmisiones diarias'
    )
    
    intervalo_minimo_segundos = models.PositiveIntegerField(
        'Intervalo Mínimo (segundos)',
        default=300,
        help_text='Tiempo mínimo entre transmisiones de cuñas'
    )
    
    duracion_maxima_bloque = models.PositiveIntegerField(
        'Duración Máxima de Bloque (segundos)',
        default=180,
        help_text='Duración máxima de un bloque publicitario'
    )
    
    # Configuración de comportamiento
    permitir_solapamiento = models.BooleanField(
        'Permitir Solapamiento',
        default=False,
        help_text='Si permitir que se solapen transmisiones'
    )
    
    priorizar_por_pago = models.BooleanField(
        'Priorizar por Pago',
        default=True,
        help_text='Priorizar cuñas de mayor valor comercial'
    )
    
    reproducir_solo_activas = models.BooleanField(
        'Solo Cuñas Activas',
        default=True,
        help_text='Solo transmitir cuñas en estado "activa"'
    )
    
    verificar_fechas_vigencia = models.BooleanField(
        'Verificar Fechas de Vigencia',
        default=True,
        help_text='Verificar que las cuñas estén dentro de su periodo de vigencia'
    )
    
    # Configuración de alertas
    notificar_errores = models.BooleanField(
        'Notificar Errores',
        default=True,
        help_text='Enviar notificaciones cuando ocurran errores'
    )
    
    notificar_inicio_fin = models.BooleanField(
        'Notificar Inicio/Fin',
        default=False,
        help_text='Notificar inicio y fin de transmisiones'
    )
    
    # Configuración técnica
    volumen_base = models.DecimalField(
        'Volumen Base (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('80.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Volumen base para las transmisiones'
    )
    
    tiempo_fade_in = models.PositiveIntegerField(
        'Tiempo Fade In (ms)',
        default=500,
        help_text='Tiempo de fade in en milisegundos'
    )
    
    tiempo_fade_out = models.PositiveIntegerField(
        'Tiempo Fade Out (ms)',
        default=500,
        help_text='Tiempo de fade out en milisegundos'
    )
    
    # Metadatos
    is_active = models.BooleanField('Activa', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='configuraciones_creadas',
        verbose_name='Creada por'
    )
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Transmisión'
        verbose_name_plural = 'Configuraciones de Transmisión'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre_configuracion} ({self.get_modo_operacion_display()})"
    
    @classmethod
    def get_configuracion_activa(cls):
        """Obtiene la configuración activa"""
        return cls.objects.filter(is_active=True).first()
    
    def esta_en_horario_transmision(self, hora=None):
        """Verifica si está en horario de transmisión"""
        if hora is None:
            hora = timezone.now().time()
        
        return self.hora_inicio_transmision <= hora <= self.hora_fin_transmision
    
    def puede_transmitir(self):
        """Verifica si el sistema puede transmitir"""
        return (
            self.is_active and 
            self.estado_sistema == 'activo' and
            self.esta_en_horario_transmision()
        )


class ProgramacionTransmision(models.Model):
    """
    Programación de transmisiones para cuñas publicitarias
    """
    
    TIPO_PROGRAMACION_CHOICES = [
        ('unica', 'Transmisión Única'),
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('personalizada', 'Personalizada'),
    ]
    
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('activa', 'Activa'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('error', 'Error'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
        ('critica', 'Crítica'),
    ]
    
    # Información básica
    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único de la programación'
    )
    
    nombre = models.CharField(
        'Nombre',
        max_length=200,
        help_text='Nombre descriptivo de la programación'
    )
    
    descripcion = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción detallada de la programación'
    )
    
    # Relaciones
    cuña = models.ForeignKey(
        'content_management.CuñaPublicitaria',
        on_delete=models.CASCADE,
        related_name='programaciones',
        verbose_name='Cuña Publicitaria'
    )
    
    configuracion = models.ForeignKey(
        ConfiguracionTransmision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programaciones',
        verbose_name='Configuración'
    )
    
    # Estado y prioridad
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programada'
    )
    
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='normal'
    )
    
    # Configuración temporal
    tipo_programacion = models.CharField(
        'Tipo de Programación',
        max_length=20,
        choices=TIPO_PROGRAMACION_CHOICES,
        default='diaria'
    )
    
    fecha_inicio = models.DateTimeField(
        'Fecha de Inicio',
        help_text='Fecha y hora de inicio de la programación'
    )
    
    fecha_fin = models.DateTimeField(
        'Fecha de Fin',
        null=True,
        blank=True,
        help_text='Fecha y hora de fin de la programación'
    )
    
    # Configuración de repetición
    repeticiones_por_dia = models.PositiveIntegerField(
        'Repeticiones por Día',
        default=1,
        help_text='Número de veces que se reproduce por día'
    )
    
    intervalo_entre_repeticiones = models.PositiveIntegerField(
        'Intervalo entre Repeticiones (minutos)',
        default=60,
        help_text='Tiempo mínimo entre repeticiones'
    )
    
    # Días de la semana (para programación semanal)
    lunes = models.BooleanField('Lunes', default=True)
    martes = models.BooleanField('Martes', default=True)
    miercoles = models.BooleanField('Miércoles', default=True)
    jueves = models.BooleanField('Jueves', default=True)
    viernes = models.BooleanField('Viernes', default=True)
    sabado = models.BooleanField('Sábado', default=False)
    domingo = models.BooleanField('Domingo', default=False)
    
    # Horarios específicos
    horarios_especificos = models.JSONField(
        'Horarios Específicos',
        default=list,
        blank=True,
        help_text='Lista de horarios específicos para transmisión (formato HH:MM)'
    )
    
    # Configuración avanzada
    permitir_ajuste_automatico = models.BooleanField(
        'Permitir Ajuste Automático',
        default=True,
        help_text='Permitir que el sistema ajuste horarios automáticamente'
    )
    
    respetar_intervalos_minimos = models.BooleanField(
        'Respetar Intervalos Mínimos',
        default=True,
        help_text='Respetar los intervalos mínimos configurados'
    )
    
    # Estadísticas
    total_reproducciones_programadas = models.PositiveIntegerField(
        'Total Reproducciones Programadas',
        default=0
    )
    
    total_reproducciones_ejecutadas = models.PositiveIntegerField(
        'Total Reproducciones Ejecutadas',
        default=0
    )
    
    ultima_reproduccion = models.DateTimeField(
        'Última Reproducción',
        null=True,
        blank=True
    )
    
    proxima_reproduccion = models.DateTimeField(
        'Próxima Reproducción',
        null=True,
        blank=True
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='programaciones_creadas',
        verbose_name='Creada por'
    )
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Programación de Transmisión'
        verbose_name_plural = 'Programaciones de Transmisión'
        ordering = ['-prioridad', 'proxima_reproduccion']
        indexes = [
            models.Index(fields=['estado', 'proxima_reproduccion']),
            models.Index(fields=['cuña', 'estado']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
        ]
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        
        # Calcular próxima reproducción
        if not self.proxima_reproduccion:
            self.calcular_proxima_reproduccion()
        
        super().save(*args, **kwargs)
    
    def generar_codigo(self):
        """Genera un código único para la programación"""
        año = timezone.now().year
        mes = timezone.now().month
        count = ProgramacionTransmision.objects.filter(
            created_at__year=año,
            created_at__month=mes
        ).count() + 1
        
        return f"PT{año}{mes:02d}{count:04d}"
    
    def clean(self):
        """Validaciones personalizadas"""
        # Validar fechas
        if self.fecha_fin and self.fecha_inicio >= self.fecha_fin:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        # Validar que la cuña esté en estado válido
        if self.cuña and self.cuña.estado not in ['activa', 'aprobada']:
            raise ValidationError('La cuña debe estar en estado "activa" o "aprobada".')
    
    @property
    def esta_activa(self):
        """Verifica si la programación está activa"""
        ahora = timezone.now()
        return (
            self.estado == 'activa' and
            self.fecha_inicio <= ahora and
            (self.fecha_fin is None or ahora <= self.fecha_fin)
        )
    
    @property
    def dias_semana_activos(self):
        """Retorna lista de días de la semana activos"""
        dias = []
        if self.lunes: dias.append(0)
        if self.martes: dias.append(1)
        if self.miercoles: dias.append(2)
        if self.jueves: dias.append(3)
        if self.viernes: dias.append(4)
        if self.sabado: dias.append(5)
        if self.domingo: dias.append(6)
        return dias
    
    def calcular_proxima_reproduccion(self):
        """Calcula la próxima fecha/hora de reproducción"""
        if not self.esta_activa:
            self.proxima_reproduccion = None
            return
        
        ahora = timezone.now()
        
        if self.tipo_programacion == 'unica':
            if self.fecha_inicio > ahora:
                self.proxima_reproduccion = self.fecha_inicio
            else:
                self.proxima_reproduccion = None
        
        elif self.tipo_programacion == 'diaria':
            # Encontrar la próxima hora disponible hoy o mañana
            self.proxima_reproduccion = self._calcular_proxima_diaria(ahora)
        
        elif self.tipo_programacion == 'semanal':
            # Encontrar el próximo día de la semana activo
            self.proxima_reproduccion = self._calcular_proxima_semanal(ahora)
        
        # Guardar sin disparar señales
        if self.pk:
            ProgramacionTransmision.objects.filter(pk=self.pk).update(
                proxima_reproduccion=self.proxima_reproduccion
            )
    
    def _calcular_proxima_diaria(self, desde):
        """Calcula próxima reproducción para programación diaria"""
        if self.horarios_especificos:
            # Usar horarios específicos
            for horario_str in self.horarios_especificos:
                try:
                    hora, minuto = map(int, horario_str.split(':'))
                    proxima = desde.replace(hour=hora, minute=minuto, second=0, microsecond=0)
                    
                    if proxima > desde:
                        return proxima
                except ValueError:
                    continue
            
            # Si no hay horarios válidos hoy, probar mañana
            mañana = desde + timedelta(days=1)
            return self._calcular_proxima_diaria(mañana.replace(hour=0, minute=0, second=0))
        
        else:
            # Distribución automática basada en repeticiones_por_dia
            config = ConfiguracionTransmision.get_configuracion_activa()
            if not config:
                return None
            
            inicio_transmision = datetime.combine(desde.date(), config.hora_inicio_transmision)
            fin_transmision = datetime.combine(desde.date(), config.hora_fin_transmision)
            
            if timezone.is_naive(inicio_transmision):
                inicio_transmision = timezone.make_aware(inicio_transmision)
            if timezone.is_naive(fin_transmision):
                fin_transmision = timezone.make_aware(fin_transmision)
            
            # Calcular intervalos
            duracion_total = (fin_transmision - inicio_transmision).total_seconds()
            intervalo = duracion_total / self.repeticiones_por_dia
            
            # Encontrar próximo slot
            tiempo_transcurrido = (desde - inicio_transmision).total_seconds()
            if tiempo_transcurrido < 0:
                return inicio_transmision
            
            slot_actual = int(tiempo_transcurrido / intervalo)
            if slot_actual < self.repeticiones_por_dia:
                proxima = inicio_transmision + timedelta(seconds=(slot_actual + 1) * intervalo)
                if proxima <= fin_transmision:
                    return proxima
            
            # Si no hay más slots hoy, programar para mañana
            mañana = desde + timedelta(days=1)
            return self._calcular_proxima_diaria(mañana.replace(hour=0, minute=0, second=0))
    
    def _calcular_proxima_semanal(self, desde):
        """Calcula próxima reproducción para programación semanal"""
        dias_activos = self.dias_semana_activos
        if not dias_activos:
            return None
        
        # Encontrar el próximo día activo
        dia_actual = desde.weekday()
        
        for i in range(7):
            dia_prueba = (dia_actual + i) % 7
            if dia_prueba in dias_activos:
                fecha_prueba = desde + timedelta(days=i)
                
                if i == 0:  # Hoy
                    proxima = self._calcular_proxima_diaria(desde)
                    if proxima and proxima.date() == desde.date():
                        return proxima
                else:  # Otro día
                    return self._calcular_proxima_diaria(
                        fecha_prueba.replace(hour=0, minute=0, second=0, microsecond=0)
                    )
        
        return None
    
    def puede_reproducir_ahora(self):
        """Verifica si puede reproducirse ahora"""
        if not self.esta_activa:
            return False
        
        ahora = timezone.now()
        
        # Verificar si es tiempo de reproducir
        if self.proxima_reproduccion and ahora >= self.proxima_reproduccion:
            return True
        
        # Verificar última reproducción vs intervalo mínimo
        if self.ultima_reproduccion:
            tiempo_transcurrido = (ahora - self.ultima_reproduccion).total_seconds()
            if tiempo_transcurrido < self.intervalo_entre_repeticiones * 60:
                return False
        
        return True
    
    def marcar_reproduccion_ejecutada(self):
        """Marca una reproducción como ejecutada"""
        self.total_reproducciones_ejecutadas += 1
        self.ultima_reproduccion = timezone.now()
        self.calcular_proxima_reproduccion()
        self.save(update_fields=[
            'total_reproducciones_ejecutadas',
            'ultima_reproduccion',
            'proxima_reproduccion'
        ])
    
    def activar(self):
        """Activa la programación"""
        self.estado = 'activa'
        self.calcular_proxima_reproduccion()
        self.save()
    
    def cancelar(self):
        """Cancela la programación"""
        self.estado = 'cancelada'
        self.proxima_reproduccion = None
        self.save()


class TransmisionActual(models.Model):
    """
    Control de transmisión en tiempo real
    """
    
    ESTADO_CHOICES = [
        ('preparando', 'Preparando'),
        ('transmitiendo', 'Transmitiendo'),
        ('pausada', 'Pausada'),
        ('completada', 'Completada'),
        ('error', 'Error'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Información de la transmisión
    session_id = models.UUIDField(
        'ID de Sesión',
        default=uuid.uuid4,
        unique=True,
        help_text='Identificador único de la sesión de transmisión'
    )
    
    programacion = models.ForeignKey(
        ProgramacionTransmision,
        on_delete=models.CASCADE,
        related_name='transmisiones',
        verbose_name='Programación'
    )
    
    cuña = models.ForeignKey(
        'content_management.CuñaPublicitaria',
        on_delete=models.CASCADE,
        related_name='transmisiones_actuales',
        verbose_name='Cuña'
    )
    
    # Estado y control
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='preparando'
    )
    
    # Tiempo y duración
    inicio_programado = models.DateTimeField(
        'Inicio Programado',
        help_text='Hora programada para iniciar la transmisión'
    )
    
    inicio_real = models.DateTimeField(
        'Inicio Real',
        null=True,
        blank=True,
        help_text='Hora real de inicio de la transmisión'
    )
    
    fin_programado = models.DateTimeField(
        'Fin Programado',
        null=True,
        blank=True,
        help_text='Hora programada para finalizar la transmisión'
    )
    
    fin_real = models.DateTimeField(
        'Fin Real',
        null=True,
        blank=True,
        help_text='Hora real de finalización de la transmisión'
    )
    
    duracion_segundos = models.PositiveIntegerField(
        'Duración (segundos)',
        null=True,
        blank=True,
        help_text='Duración real de la transmisión en segundos'
    )
    
    posicion_actual = models.PositiveIntegerField(
        'Posición Actual (segundos)',
        default=0,
        help_text='Posición actual de reproducción en segundos'
    )
    
    # Configuración técnica
    volumen = models.DecimalField(
        'Volumen (%)',
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    fade_in_aplicado = models.BooleanField('Fade In Aplicado', default=False)
    fade_out_aplicado = models.BooleanField('Fade Out Aplicado', default=False)
    
    # Control manual
    pausado_manualmente = models.BooleanField('Pausado Manualmente', default=False)
    pausado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transmisiones_pausadas',
        verbose_name='Pausado por'
    )
    
    pausado_en = models.DateTimeField('Pausado en', null=True, blank=True)
    tiempo_total_pausado = models.PositiveIntegerField(
        'Tiempo Total Pausado (segundos)',
        default=0
    )
    
    # Información adicional
    calidad_transmision = models.CharField(
        'Calidad de Transmisión',
        max_length=20,
        choices=[
            ('excelente', 'Excelente'),
            ('buena', 'Buena'),
            ('regular', 'Regular'),
            ('mala', 'Mala'),
        ],
        null=True,
        blank=True
    )
    
    errores_detectados = models.JSONField(
        'Errores Detectados',
        default=list,
        blank=True,
        help_text='Lista de errores detectados durante la transmisión'
    )
    
    metadatos_transmision = models.JSONField(
        'Metadatos de Transmisión',
        default=dict,
        blank=True,
        help_text='Metadatos técnicos de la transmisión'
    )
    
    # Timestamps
    created_at = models.DateTimeField('Creada', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizada', auto_now=True)
    
    class Meta:
        verbose_name = 'Transmisión Actual'
        verbose_name_plural = 'Transmisiones Actuales'
        ordering = ['-inicio_programado']
        indexes = [
            models.Index(fields=['estado', 'inicio_programado']),
            models.Index(fields=['session_id']),
            models.Index(fields=['cuña', 'estado']),
        ]
    
    def __str__(self):
        return f"Transmisión {self.session_id} - {self.cuña.titulo}"
    
    def save(self, *args, **kwargs):
        # Calcular fin programado si no está definido
        if not self.fin_programado and self.cuña and self.cuña.archivo_audio:
            duracion = self.cuña.archivo_audio.duracion_segundos or self.cuña.duracion_planeada
            self.fin_programado = self.inicio_programado + timedelta(seconds=duracion)
        
        super().save(*args, **kwargs)
    
    @property
    def esta_transmitiendo(self):
        """Verifica si está transmitiendo actualmente"""
        return self.estado == 'transmitiendo'
    
    @property
    def esta_pausada(self):
        """Verifica si está pausada"""
        return self.estado == 'pausada'
    
    @property
    def progreso_porcentaje(self):
        """Calcula el porcentaje de progreso"""
        if self.duracion_segundos and self.posicion_actual:
            return min((self.posicion_actual / self.duracion_segundos) * 100, 100)
        return 0
    
    @property
    def tiempo_restante(self):
        """Calcula el tiempo restante en segundos"""
        if self.duracion_segundos and self.posicion_actual:
            return max(self.duracion_segundos - self.posicion_actual, 0)
        return 0
    
    @property
    def retraso_inicio(self):
        """Calcula el retraso en el inicio (en segundos)"""
        if self.inicio_real and self.inicio_programado:
            return (self.inicio_real - self.inicio_programado).total_seconds()
        return 0
    
    def iniciar_transmision(self, usuario=None):
        """Inicia la transmisión"""
        self.estado = 'transmitiendo'
        self.inicio_real = timezone.now()
        
        if self.cuña and self.cuña.archivo_audio:
            self.duracion_segundos = self.cuña.archivo_audio.duracion_segundos
        
        self.save()
        
        # Crear log
        LogTransmision.objects.create(
            transmision=self,
            accion='iniciada',
            usuario=usuario,
            descripcion='Transmisión iniciada',
            datos={'inicio_real': self.inicio_real.isoformat()}
        )
    
    def pausar_transmision(self, usuario=None):
        """Pausa la transmisión"""
        if self.estado == 'transmitiendo':
            self.estado = 'pausada'
            self.pausado_manualmente = True
            self.pausado_por = usuario
            self.pausado_en = timezone.now()
            self.save()
            
            # Crear log
            LogTransmision.objects.create(
                transmision=self,
                accion='pausada',
                usuario=usuario,
                descripcion='Transmisión pausada manualmente',
                datos={'pausado_en': self.pausado_en.isoformat()}
            )
    
    def reanudar_transmision(self, usuario=None):
        """Reanuda la transmisión"""
        if self.estado == 'pausada':
            # Calcular tiempo pausado
            if self.pausado_en:
                tiempo_pausado = (timezone.now() - self.pausado_en).total_seconds()
                self.tiempo_total_pausado += int(tiempo_pausado)
            
            self.estado = 'transmitiendo'
            self.pausado_manualmente = False
            self.pausado_por = None
            self.pausado_en = None
            self.save()
            
            # Crear log
            LogTransmision.objects.create(
                transmision=self,
                accion='reanudada',
                usuario=usuario,
                descripcion='Transmisión reanudada',
                datos={'tiempo_pausado': tiempo_pausado}
            )
    
    def finalizar_transmision(self, usuario=None, razon='completada'):
        """Finaliza la transmisión"""
        self.estado = 'completada' if razon == 'completada' else razon
        self.fin_real = timezone.now()
        
        if self.inicio_real:
            self.duracion_segundos = int((self.fin_real - self.inicio_real).total_seconds())
        
        self.save()
        
        # Marcar reproducción ejecutada en la programación
        if self.programacion:
            self.programacion.marcar_reproduccion_ejecutada()
        
        # Crear log
        LogTransmision.objects.create(
            transmision=self,
            accion='finalizada',
            usuario=usuario,
            descripcion=f'Transmisión finalizada: {razon}',
            datos={
                'fin_real': self.fin_real.isoformat(),
                'duracion_total': self.duracion_segundos,
                'razon': razon
            }
        )
    
    def reportar_error(self, error_mensaje, usuario=None):
        """Reporta un error en la transmisión"""
        self.estado = 'error'
        
        error_info = {
            'timestamp': timezone.now().isoformat(),
            'mensaje': error_mensaje,
            'usuario': usuario.username if usuario else None
        }
        
        self.errores_detectados.append(error_info)
        self.save()
        
        # Crear log
        LogTransmision.objects.create(
            transmision=self,
            accion='error',
            usuario=usuario,
            descripcion=f'Error reportado: {error_mensaje}',
            datos=error_info
        )


class LogTransmision(models.Model):
    """
    Registro histórico de todas las transmisiones y eventos
    """
    
    ACCION_CHOICES = [
        # Acciones de transmisión
        ('programada', 'Programada'),
        ('iniciada', 'Iniciada'),
        ('pausada', 'Pausada'),
        ('reanudada', 'Reanudada'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
        ('error', 'Error'),
        
        # Acciones de sistema
        ('sistema_iniciado', 'Sistema Iniciado'),
        ('sistema_pausado', 'Sistema Pausado'),
        ('sistema_detenido', 'Sistema Detenido'),
        ('configuracion_cambiada', 'Configuración Cambiada'),
        
        # Acciones manuales
        ('intervencion_manual', 'Intervención Manual'),
        ('orden_cambiado', 'Orden Cambiado'),
        ('programacion_modificada', 'Programación Modificada'),
    ]
    
    NIVEL_CHOICES = [
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('critical', 'Crítico'),
    ]
    
    # Información del evento
    transmision = models.ForeignKey(
        TransmisionActual,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name='Transmisión'
    )
    
    programacion = models.ForeignKey(
        ProgramacionTransmision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name='Programación'
    )
    
    cuña = models.ForeignKey(
        'content_management.CuñaPublicitaria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_transmision',
        verbose_name='Cuña'
    )
    
    # Detalles del evento
    accion = models.CharField(
        'Acción',
        max_length=30,
        choices=ACCION_CHOICES
    )
    
    nivel = models.CharField(
        'Nivel',
        max_length=10,
        choices=NIVEL_CHOICES,
        default='info'
    )
    
    descripcion = models.TextField(
        'Descripción',
        help_text='Descripción detallada del evento'
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_transmision',
        verbose_name='Usuario'
    )
    
    # Datos técnicos
    datos = models.JSONField(
        'Datos Adicionales',
        default=dict,
        blank=True,
        help_text='Datos adicionales del evento en formato JSON'
    )
    
    ip_address = models.GenericIPAddressField(
        'Dirección IP',
        null=True,
        blank=True
    )
    
    user_agent = models.TextField(
        'User Agent',
        blank=True
    )
    
    # Timestamp
    timestamp = models.DateTimeField(
        'Fecha y Hora',
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = 'Log de Transmisión'
        verbose_name_plural = 'Logs de Transmisión'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['accion', 'timestamp']),
            models.Index(fields=['nivel', 'timestamp']),
            models.Index(fields=['transmision', 'timestamp']),
            models.Index(fields=['usuario', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp.strftime('%d/%m/%Y %H:%M:%S')} - {self.get_accion_display()}"
    
    @classmethod
    def log_evento(cls, accion, descripcion, transmision=None, programacion=None, 
                   cuña=None, usuario=None, nivel='info', datos=None, ip_address=None, 
                   user_agent=None):
        """
        Método de conveniencia para crear logs
        """
        return cls.objects.create(
            transmision=transmision,
            programacion=programacion,
            cuña=cuña,
            accion=accion,
            nivel=nivel,
            descripcion=descripcion,
            usuario=usuario,
            datos=datos or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def get_logs_por_periodo(cls, fecha_inicio, fecha_fin, accion=None, nivel=None):
        """
        Obtiene logs por periodo de tiempo
        """
        queryset = cls.objects.filter(
            timestamp__range=[fecha_inicio, fecha_fin]
        )
        
        if accion:
            queryset = queryset.filter(accion=accion)
        
        if nivel:
            queryset = queryset.filter(nivel=nivel)
        
        return queryset.order_by('-timestamp')
    
    @classmethod
    def get_estadisticas_periodo(cls, fecha_inicio, fecha_fin):
        """
        Obtiene estadísticas de transmisiones por periodo
        """
        logs = cls.objects.filter(
            timestamp__range=[fecha_inicio, fecha_fin]
        )
        
        stats = {
            'total_eventos': logs.count(),
            'transmisiones_iniciadas': logs.filter(accion='iniciada').count(),
            'transmisiones_completadas': logs.filter(accion='finalizada').count(),
            'errores': logs.filter(nivel='error').count(),
            'intervenciones_manuales': logs.filter(accion='intervencion_manual').count(),
        }
        
        # Cuñas más transmitidas
        cuñas_stats = logs.filter(
            accion='iniciada',
            cuña__isnull=False
        ).values(
            'cuña__titulo',
            'cuña__codigo'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        stats['cuñas_mas_transmitidas'] = list(cuñas_stats)
        
        return stats


class EventoSistema(models.Model):
    """
    Eventos del sistema de transmisión (inicio, parada, mantenimiento, etc.)
    """
    
    TIPO_EVENTO_CHOICES = [
        ('inicio_sistema', 'Inicio del Sistema'),
        ('parada_sistema', 'Parada del Sistema'),
        ('reinicio_sistema', 'Reinicio del Sistema'),
        ('mantenimiento_inicio', 'Inicio de Mantenimiento'),
        ('mantenimiento_fin', 'Fin de Mantenimiento'),
        ('cambio_configuracion', 'Cambio de Configuración'),
        ('error_critico', 'Error Crítico'),
        ('recuperacion_error', 'Recuperación de Error'),
    ]
    
    tipo_evento = models.CharField(
        'Tipo de Evento',
        max_length=30,
        choices=TIPO_EVENTO_CHOICES
    )
    
    descripcion = models.TextField(
        'Descripción',
        help_text='Descripción detallada del evento del sistema'
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_sistema_transmision',
        verbose_name='Usuario'
    )
    
    datos_sistema = models.JSONField(
        'Datos del Sistema',
        default=dict,
        blank=True,
        help_text='Estado del sistema al momento del evento'
    )
    
    configuracion_antes = models.JSONField(
        'Configuración Anterior',
        null=True,
        blank=True,
        help_text='Configuración antes del cambio (para eventos de configuración)'
    )
    
    configuracion_despues = models.JSONField(
        'Configuración Posterior',
        null=True,
        blank=True,
        help_text='Configuración después del cambio'
    )
    
    resuelto = models.BooleanField(
        'Resuelto',
        default=True,
        help_text='Si el evento fue resuelto satisfactoriamente'
    )
    
    timestamp = models.DateTimeField('Fecha y Hora', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Evento del Sistema'
        verbose_name_plural = 'Eventos del Sistema'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp.strftime('%d/%m/%Y %H:%M')} - {self.get_tipo_evento_display()}"


# Managers personalizados
class TransmisionManager(models.Manager):
    """Manager personalizado para transmisiones"""
    
    def activas(self):
        """Transmisiones actualmente en curso"""
        return self.filter(estado='transmitiendo')
    
    def programadas_para_hoy(self):
        """Transmisiones programadas para hoy"""
        hoy = timezone.now().date()
        return self.filter(
            inicio_programado__date=hoy,
            estado__in=['preparando', 'transmitiendo']
        )
    
    def completadas_hoy(self):
        """Transmisiones completadas hoy"""
        hoy = timezone.now().date()
        return self.filter(
            fin_real__date=hoy,
            estado='completada'
        )


# Asignar el manager personalizado
TransmisionActual.objects = TransmisionManager()


# Funciones de utilidad
def obtener_transmision_actual():
    """Obtiene la transmisión que está ejecutándose actualmente"""
    return TransmisionActual.objects.filter(estado='transmitiendo').first()


def obtener_proximas_transmisiones(limite=10):
    """Obtiene las próximas transmisiones programadas"""
    ahora = timezone.now()
    return TransmisionActual.objects.filter(
        estado='preparando',
        inicio_programado__gt=ahora
    ).order_by('inicio_programado')[:limite]


def verificar_sistema_listo_para_transmitir():
    """Verifica si el sistema está listo para transmitir"""
    config = ConfiguracionTransmision.get_configuracion_activa()
    if not config:
        return False, "No hay configuración activa"
    
    if not config.puede_transmitir():
        return False, "Sistema no está en condiciones de transmitir"
    
    # Verificar que no haya errores críticos recientes
    errores_recientes = LogTransmision.objects.filter(
        nivel='critical',
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if errores_recientes > 0:
        return False, f"Hay {errores_recientes} errores críticos recientes"
    
    return True, "Sistema listo para transmitir"