"""
Formularios para el módulo de Control de Transmisiones
Sistema PubliTrack - Gestión y programación de transmisiones de publicidad radial
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, timedelta
from decimal import Decimal

from .models import (
    ConfiguracionTransmision,
    ProgramacionTransmision,
    TransmisionActual,
    EventoSistema
)
from apps.content_management.models import CuñaPublicitaria


class ConfiguracionTransmisionForm(forms.ModelForm):
    """
    Formulario para configuración del sistema de transmisiones
    """
    
    class Meta:
        model = ConfiguracionTransmision
        fields = [
            'nombre_configuracion',
            'modo_operacion',
            'estado_sistema',
            'hora_inicio_transmision',
            'hora_fin_transmision',
            'intervalo_minimo_segundos',
            'duracion_maxima_bloque',
            'permitir_solapamiento',
            'priorizar_por_pago',
            'reproducir_solo_activas',
            'verificar_fechas_vigencia',
            'notificar_errores',
            'notificar_inicio_fin',
            'volumen_base',
            'tiempo_fade_in',
            'tiempo_fade_out',
        ]
        
        widgets = {
            'nombre_configuracion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Configuración Principal'
            }),
            'modo_operacion': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estado_sistema': forms.Select(attrs={
                'class': 'form-select'
            }),
            'hora_inicio_transmision': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'hora_fin_transmision': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'intervalo_minimo_segundos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '30',
                'max': '3600',
                'placeholder': '300'
            }),
            'duracion_maxima_bloque': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '30',
                'max': '600',
                'placeholder': '180'
            }),
            'volumen_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '80.00'
            }),
            'tiempo_fade_in': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '5000',
                'placeholder': '500'
            }),
            'tiempo_fade_out': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '5000',
                'placeholder': '500'
            }),
            'permitir_solapamiento': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'priorizar_por_pago': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'reproducir_solo_activas': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'verificar_fechas_vigencia': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notificar_errores': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notificar_inicio_fin': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        help_texts = {
            'intervalo_minimo_segundos': 'Tiempo mínimo en segundos entre transmisiones (30-3600)',
            'duracion_maxima_bloque': 'Duración máxima de un bloque publicitario en segundos',
            'volumen_base': 'Volumen base para las transmisiones (0-100%)',
            'tiempo_fade_in': 'Tiempo de fade in en milisegundos',
            'tiempo_fade_out': 'Tiempo de fade out en milisegundos',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar horarios
        hora_inicio = cleaned_data.get('hora_inicio_transmision')
        hora_fin = cleaned_data.get('hora_fin_transmision')
        
        if hora_inicio and hora_fin:
            if hora_fin <= hora_inicio:
                raise ValidationError(
                    'La hora de fin debe ser posterior a la hora de inicio.'
                )
        
        # Validar intervalos
        intervalo_minimo = cleaned_data.get('intervalo_minimo_segundos')
        duracion_maxima = cleaned_data.get('duracion_maxima_bloque')
        
        if intervalo_minimo and duracion_maxima:
            if intervalo_minimo < duracion_maxima:
                raise ValidationError(
                    'El intervalo mínimo debe ser mayor o igual a la duración máxima del bloque.'
                )
        
        return cleaned_data


class ProgramacionTransmisionForm(forms.ModelForm):
    """
    Formulario para crear/editar programaciones de transmisión
    """
    
    # Campo adicional para filtrar cuñas
    solo_cuñas_activas = forms.BooleanField(
        label='Mostrar solo cuñas activas',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ProgramacionTransmision
        fields = [
            'nombre',
            'descripcion',
            'cuña',
            'tipo_programacion',
            'prioridad',
            'fecha_inicio',
            'fecha_fin',
            'repeticiones_por_dia',
            'intervalo_entre_repeticiones',
            'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo',
            'horarios_especificos',
            'permitir_ajuste_automatico',
            'respetar_intervalos_minimos',
        ]
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo de la programación'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional de la programación'
            }),
            'cuña': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_programacion': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleProgramacionFields()'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_inicio': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'fecha_fin': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'repeticiones_por_dia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': '1'
            }),
            'intervalo_entre_repeticiones': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1440',
                'placeholder': '60'
            }),
            'horarios_especificos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Formato JSON: ["08:00", "12:00", "18:00"]'
            }),
            'lunes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'martes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'miercoles': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'jueves': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'viernes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sabado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'domingo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permitir_ajuste_automatico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'respetar_intervalos_minimos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        help_texts = {
            'repeticiones_por_dia': 'Número de veces que se reproduce por día',
            'intervalo_entre_repeticiones': 'Tiempo mínimo entre repeticiones en minutos',
            'horarios_especificos': 'Para programación personalizada, lista de horarios en formato JSON',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar cuñas según el usuario
        cuñas_queryset = CuñaPublicitaria.objects.all()
        
        if user and not user.es_admin:
            if user.es_vendedor:
                # Vendedores solo ven sus cuñas
                cuñas_queryset = cuñas_queryset.filter(vendedor_asignado=user)
            elif user.es_cliente:
                # Clientes solo ven sus propias cuñas
                cuñas_queryset = cuñas_queryset.filter(cliente=user)
        
        # Filtrar solo cuñas activas por defecto
        cuñas_queryset = cuñas_queryset.filter(
            estado__in=['activa', 'aprobada']
        ).select_related('cliente', 'archivo_audio')
        
        self.fields['cuña'].queryset = cuñas_queryset
        
        # Personalizar las opciones del campo cuña
        cuña_choices = [('', '---------')]
        for cuña in cuñas_queryset:
            duracion = ''
            if cuña.archivo_audio and cuña.archivo_audio.duracion_segundos:
                minutos = cuña.archivo_audio.duracion_segundos // 60
                segundos = cuña.archivo_audio.duracion_segundos % 60
                duracion = f" ({minutos:02d}:{segundos:02d})"
            
            cliente_info = f" - {cuña.cliente.nombre_completo}" if cuña.cliente else ""
            
            cuña_choices.append((
                cuña.pk, 
                f"{cuña.codigo} - {cuña.titulo}{duracion}{cliente_info}"
            ))
        
        self.fields['cuña'].choices = cuña_choices
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar fechas
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise ValidationError(
                    'La fecha de fin debe ser posterior a la fecha de inicio.'
                )
        
        # Validar fecha de inicio no sea en el pasado
        if fecha_inicio and fecha_inicio < timezone.now():
            raise ValidationError(
                'La fecha de inicio no puede ser en el pasado.'
            )
        
        # Validar días de la semana para programación semanal
        tipo_programacion = cleaned_data.get('tipo_programacion')
        if tipo_programacion == 'semanal':
            dias_seleccionados = any([
                cleaned_data.get('lunes'),
                cleaned_data.get('martes'),
                cleaned_data.get('miercoles'),
                cleaned_data.get('jueves'),
                cleaned_data.get('viernes'),
                cleaned_data.get('sabado'),
                cleaned_data.get('domingo'),
            ])
            
            if not dias_seleccionados:
                raise ValidationError(
                    'Para programación semanal debe seleccionar al menos un día.'
                )
        
        # Validar horarios específicos
        horarios_especificos = cleaned_data.get('horarios_especificos')
        if horarios_especificos:
            try:
                import json
                horarios = json.loads(horarios_especificos)
                
                if not isinstance(horarios, list):
                    raise ValidationError(
                        'Los horarios específicos deben ser una lista.'
                    )
                
                for horario in horarios:
                    try:
                        datetime.strptime(horario, '%H:%M')
                    except ValueError:
                        raise ValidationError(
                            f'Horario inválido: {horario}. Use formato HH:MM'
                        )
                
                cleaned_data['horarios_especificos'] = horarios
                
            except json.JSONDecodeError:
                raise ValidationError(
                    'Formato JSON inválido en horarios específicos.'
                )
        
        # Validar que la cuña esté en estado válido
        cuña = cleaned_data.get('cuña')
        if cuña and cuña.estado not in ['activa', 'aprobada']:
            raise ValidationError(
                'Solo se pueden programar cuñas en estado "activa" o "aprobada".'
            )
        
        return cleaned_data


class TransmisionManualForm(forms.Form):
    """
    Formulario para iniciar una transmisión manual
    """
    
    cuña = forms.ModelChoiceField(
        queryset=CuñaPublicitaria.objects.none(),
        label='Cuña a transmitir',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Selecciona la cuña para transmisión inmediata'
    )
    
    volumen = forms.DecimalField(
        label='Volumen (%)',
        min_value=0,
        max_value=100,
        initial=80,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '80.00'
        })
    )
    
    aplicar_fade_in = forms.BooleanField(
        label='Aplicar Fade In',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    aplicar_fade_out = forms.BooleanField(
        label='Aplicar Fade Out',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notas = forms.CharField(
        label='Notas',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Notas sobre esta transmisión manual'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar cuñas disponibles para transmisión
        cuñas_queryset = CuñaPublicitaria.objects.filter(
            estado='activa',
            archivo_audio__isnull=False
        ).select_related('cliente', 'archivo_audio')
        
        if user and not user.es_admin:
            if user.es_vendedor:
                cuñas_queryset = cuñas_queryset.filter(vendedor_asignado=user)
            elif user.es_cliente:
                cuñas_queryset = cuñas_queryset.filter(cliente=user)
        
        self.fields['cuña'].queryset = cuñas_queryset
        
        # Personalizar opciones
        cuña_choices = [('', '---------')]
        for cuña in cuñas_queryset:
            duracion = ''
            if cuña.archivo_audio.duracion_segundos:
                minutos = cuña.archivo_audio.duracion_segundos // 60
                segundos = cuña.archivo_audio.duracion_segundos % 60
                duracion = f" ({minutos:02d}:{segundos:02d})"
            
            cuña_choices.append((
                cuña.pk,
                f"{cuña.codigo} - {cuña.titulo}{duracion}"
            ))
        
        self.fields['cuña'].choices = cuña_choices


class FiltroTransmisionesForm(forms.Form):
    """
    Formulario para filtrar transmisiones en las listas
    """
    
    fecha_desde = forms.DateField(
        label='Desde',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        label='Hasta',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    estado = forms.ChoiceField(
        label='Estado',
        required=False,
        choices=[('', 'Todos')] + TransmisionActual.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    cuña = forms.ModelChoiceField(
        label='Cuña',
        queryset=CuñaPublicitaria.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    usuario = forms.ModelChoiceField(
        label='Usuario',
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para usuarios
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        self.fields['usuario'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Configurar queryset para cuñas
        self.fields['cuña'].queryset = CuñaPublicitaria.objects.filter(
            estado__in=['activa', 'aprobada', 'finalizada']
        ).select_related('cliente').order_by('-created_at')


class EventoSistemaForm(forms.ModelForm):
    """
    Formulario para eventos del sistema
    """
    
    class Meta:
        model = EventoSistema
        fields = [
            'tipo_evento',
            'descripcion',
            'datos_sistema',
            'resuelto'
        ]
        
        widgets = {
            'tipo_evento': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'datos_sistema': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Datos en formato JSON'
            }),
            'resuelto': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class BusquedaLogsForm(forms.Form):
    """
    Formulario para búsqueda avanzada de logs
    """
    
    fecha_desde = forms.DateTimeField(
        label='Desde',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    fecha_hasta = forms.DateTimeField(
        label='Hasta',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    accion = forms.ChoiceField(
        label='Acción',
        required=False,
        choices=[('', 'Todas')] + LogTransmision.ACCION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    nivel = forms.ChoiceField(
        label='Nivel',
        required=False,
        choices=[('', 'Todos')] + LogTransmision.NIVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    usuario = forms.CharField(
        label='Usuario',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
    )
    
    descripcion = forms.CharField(
        label='Descripción contiene',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar en descripción'
        })
    )


class ReporteForm(forms.Form):
    """
    Formulario para generar reportes
    """
    
    TIPO_REPORTE_CHOICES = [
        ('general', 'Reporte General'),
        ('por_cuña', 'Por Cuña'),
        ('por_cliente', 'Por Cliente'),
        ('por_vendedor', 'Por Vendedor'),
        ('errores', 'Reporte de Errores'),
    ]
    
    tipo_reporte = forms.ChoiceField(
        label='Tipo de Reporte',
        choices=TIPO_REPORTE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_desde = forms.DateField(
        label='Fecha Desde',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        label='Fecha Hasta',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    formato = forms.ChoiceField(
        label='Formato',
        choices=[
            ('html', 'HTML (Ver en pantalla)'),
            ('pdf', 'PDF (Descargar)'),
            ('csv', 'CSV (Descargar)'),
        ],
        initial='html',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    incluir_graficos = forms.BooleanField(
        label='Incluir Gráficos',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_hasta < fecha_desde:
                raise ValidationError(
                    'La fecha hasta debe ser posterior a la fecha desde.'
                )
            
            # Validar que no sea un rango muy grande (más de 1 año)
            if (fecha_hasta - fecha_desde).days > 365:
                raise ValidationError(
                    'El rango de fechas no puede ser mayor a 1 año.'
                )
        
        return cleaned_data


# Widget personalizado para horarios
class HorariosWidget(forms.Widget):
    """
    Widget personalizado para ingresar múltiples horarios
    """
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.update({'class': 'form-control'})
    
    def render(self, name, value, attrs=None, renderer=None):
        if value:
            if isinstance(value, list):
                value = ', '.join(value)
            elif isinstance(value, str):
                try:
                    import json
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        value = ', '.join(parsed)
                except:
                    pass
        
        return forms.TextInput().render(name, value, attrs)
    
    def value_from_datadict(self, data, files, name):
        value = data.get(name, '')
        if value:
            # Convertir string separado por comas a lista JSON
            horarios = [h.strip() for h in value.split(',') if h.strip()]
            return horarios
        return []