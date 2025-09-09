"""
Formularios para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Formularios para cuñas publicitarias y archivos de audio
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    CategoriaPublicitaria, 
    TipoContrato, 
    ArchivoAudio, 
    CuñaPublicitaria
)

User = get_user_model()

class CategoriaPublicitariaForm(forms.ModelForm):
    """Formulario para categorías publicitarias"""
    
    class Meta:
        model = CategoriaPublicitaria
        fields = [
            'nombre', 
            'descripcion', 
            'color_codigo', 
            'tarifa_base', 
            'is_active'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la categoría'
            }),
            'color_codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'title': 'Seleccionar color'
            }),
            'tarifa_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_tarifa_base(self):
        tarifa = self.cleaned_data.get('tarifa_base')
        if tarifa and tarifa < 0:
            raise ValidationError('La tarifa base no puede ser negativa.')
        return tarifa
    
    def clean_color_codigo(self):
        color = self.cleaned_data.get('color_codigo')
        if color and not color.startswith('#'):
            color = f'#{color}'
        if len(color) != 7:
            raise ValidationError('El código de color debe tener formato hexadecimal (#RRGGBB).')
        return color

class TipoContratoForm(forms.ModelForm):
    """Formulario para tipos de contrato"""
    
    class Meta:
        model = TipoContrato
        fields = [
            'nombre',
            'descripcion',
            'duracion_tipo',
            'duracion_dias',
            'repeticiones_minimas',
            'descuento_porcentaje',
            'is_active'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del tipo de contrato'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del tipo de contrato'
            }),
            'duracion_tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'duracion_dias': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Días de duración'
            }),
            'repeticiones_minimas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Repeticiones mínimas por día'
            }),
            'descuento_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_descuento_porcentaje(self):
        descuento = self.cleaned_data.get('descuento_porcentaje')
        if descuento and (descuento < 0 or descuento > 100):
            raise ValidationError('El descuento debe estar entre 0% y 100%.')
        return descuento

class ArchivoAudioForm(forms.ModelForm):
    """Formulario para subir archivos de audio"""
    
    class Meta:
        model = ArchivoAudio
        fields = ['archivo']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.mp3,.wav,.aac,.m4a,.ogg',
                'title': 'Seleccionar archivo de audio'
            })
        }
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        
        if archivo:
            # Validar tamaño del archivo (máximo 50MB)
            if archivo.size > 50 * 1024 * 1024:
                raise ValidationError('El archivo es demasiado grande. Máximo 50MB.')
            
            # Validar extensión
            ext = archivo.name.split('.')[-1].lower()
            extensiones_validas = ['mp3', 'wav', 'aac', 'm4a', 'ogg']
            
            if ext not in extensiones_validas:
                raise ValidationError(
                    f'Formato de archivo no válido. Formatos permitidos: {", ".join(extensiones_validas)}'
                )
        
        return archivo

class CuñaPublicitariaForm(forms.ModelForm):
    """Formulario para cuñas publicitarias"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de clientes
        if self.user:
            if self.user.groups.filter(name='Vendedores').exists():
                # Vendedores solo ven clientes asignados a ellos
                self.fields['cliente'].queryset = User.objects.filter(
                    groups__name='Clientes',
                    perfil_vendedor__vendedor=self.user
                )
            elif self.user.groups.filter(name='Clientes').exists():
                # Clientes solo se ven a sí mismos
                self.fields['cliente'].queryset = User.objects.filter(id=self.user.id)
                self.fields['cliente'].initial = self.user
                self.fields['cliente'].widget = forms.HiddenInput()
            else:
                # Admins y supervisores ven todos los clientes
                self.fields['cliente'].queryset = User.objects.filter(groups__name='Clientes')
        
        # Configurar queryset de vendedores
        self.fields['vendedor_asignado'].queryset = User.objects.filter(groups__name='Vendedores')
        
        # Configurar queryset de categorías activas
        self.fields['categoria'].queryset = CategoriaPublicitaria.objects.filter(is_active=True)
        
        # Configurar queryset de tipos de contrato activos
        self.fields['tipo_contrato'].queryset = TipoContrato.objects.filter(is_active=True)
        
        # Configurar queryset de archivos de audio
        if self.user and self.user.groups.filter(name='Clientes').exists():
            # Clientes solo ven archivos de sus cuñas
            self.fields['archivo_audio'].queryset = ArchivoAudio.objects.filter(
                cuñas__cliente=self.user
            ).distinct()
        else:
            self.fields['archivo_audio'].queryset = ArchivoAudio.objects.all()
    
    class Meta:
        model = CuñaPublicitaria
        fields = [
            'titulo',
            'descripcion',
            'cliente',
            'vendedor_asignado',
            'categoria',
            'tipo_contrato',
            'archivo_audio',
            'duracion_planeada',
            'precio_total',
            'repeticiones_dia',
            'fecha_inicio',
            'fecha_fin',
            'prioridad',
            'observaciones',
            'tags',
            'requiere_aprobacion',
            'notificar_vencimiento',
            'dias_aviso_vencimiento'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo de la cuña'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del contenido publicitario'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'vendedor_asignado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_contrato': forms.Select(attrs={
                'class': 'form-select'
            }),
            'archivo_audio': forms.Select(attrs={
                'class': 'form-select'
            }),
            'duracion_planeada': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Duración en segundos'
            }),
            'precio_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'repeticiones_dia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'prioridad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Palabras clave separadas por comas'
            }),
            'requiere_aprobacion': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notificar_vencimiento': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'dias_aviso_vencimiento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30',
                'value': '7'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        duracion_planeada = cleaned_data.get('duracion_planeada')
        archivo_audio = cleaned_data.get('archivo_audio')
        precio_total = cleaned_data.get('precio_total')
        
        # Validar fechas
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
            
            if fecha_inicio < date.today():
                raise ValidationError('La fecha de inicio no puede ser anterior a hoy.')
            
            # Validar que no sea una campaña demasiado larga (máximo 2 años)
            if (fecha_fin - fecha_inicio).days > 730:
                raise ValidationError('La campaña no puede durar más de 2 años.')
        
        # Validar duración vs archivo de audio
        if duracion_planeada and archivo_audio and archivo_audio.duracion_segundos:
            diferencia = abs(duracion_planeada - archivo_audio.duracion_segundos)
            if diferencia > 5:  # Tolerancia de 5 segundos
                raise ValidationError(
                    f'La duración planeada ({duracion_planeada}s) difiere mucho '
                    f'del archivo de audio ({archivo_audio.duracion_segundos}s). '
                    f'La diferencia es de {diferencia} segundos.'
                )
        
        # Validar precio mínimo
        if precio_total and precio_total < Decimal('1.00'):
            raise ValidationError('El precio total debe ser al menos $1.00.')
        
        return cleaned_data
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Limpiar y validar tags
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if len(tags_list) > 10:
                raise ValidationError('Máximo 10 tags permitidos.')
            return ', '.join(tags_list)
        return tags

class CuñaAprobacionForm(forms.Form):
    """Formulario para aprobar cuñas publicitarias"""
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre la aprobación (opcional)'
        }),
        help_text='Observaciones adicionales sobre la aprobación'
    )
    
    aprobar = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Confirmar aprobación'
    )

class CuñaFiltroForm(forms.Form):
    """Formulario para filtrar cuñas publicitarias"""
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + CuñaPublicitaria.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaPublicitaria.objects.filter(is_active=True),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    vendedor = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='Vendedores'),
        required=False,
        empty_label='Todos los vendedores',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha inicio desde'
    )
    
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha fin hasta'
    )
    
    prioridad = forms.ChoiceField(
        choices=[('', 'Todas las prioridades')] + CuñaPublicitaria.PRIORIDAD_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    solo_activas = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Solo cuñas activas'
    )
    
    por_vencer = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Próximas a vencer (30 días)'
    )

class BusquedaAvanzadaForm(forms.Form):
    """Formulario para búsqueda avanzada de cuñas"""
    
    texto = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar en código, título, cliente...'
        }),
        label='Texto de búsqueda'
    )
    
    precio_min = forms.DecimalField(
        required=False,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        label='Precio mínimo'
    )
    
    precio_max = forms.DecimalField(
        required=False,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        label='Precio máximo'
    )
    
    duracion_min = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Segundos'
        }),
        label='Duración mínima (segundos)'
    )
    
    duracion_max = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Segundos'
        }),
        label='Duración máxima (segundos)'
    )
    
    con_audio = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Solo cuñas con archivo de audio'
    )
    
    sin_audio = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Solo cuñas sin archivo de audio'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        precio_min = cleaned_data.get('precio_min')
        precio_max = cleaned_data.get('precio_max')
        duracion_min = cleaned_data.get('duracion_min')
        duracion_max = cleaned_data.get('duracion_max')
        con_audio = cleaned_data.get('con_audio')
        sin_audio = cleaned_data.get('sin_audio')
        
        # Validar rangos de precio
        if precio_min and precio_max and precio_min > precio_max:
            raise ValidationError('El precio mínimo no puede ser mayor al precio máximo.')
        
        # Validar rangos de duración
        if duracion_min and duracion_max and duracion_min > duracion_max:
            raise ValidationError('La duración mínima no puede ser mayor a la duración máxima.')
        
        # Validar opciones de audio mutuamente excluyentes
        if con_audio and sin_audio:
            raise ValidationError('No se pueden seleccionar ambas opciones de audio.')
        
        return cleaned_data

class RangoFechasForm(forms.Form):
    """Formulario para seleccionar rango de fechas en reportes"""
    
    fecha_desde = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha desde'
    )
    
    fecha_hasta = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha hasta'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer fechas por defecto (último mes)
        hoy = date.today()
        hace_mes = hoy - timedelta(days=30)
        
        self.fields['fecha_desde'].initial = hace_mes
        self.fields['fecha_hasta'].initial = hoy
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha desde no puede ser posterior a la fecha hasta.')
            
            # Validar que no sea un rango demasiado amplio (máximo 2 años)
            if (fecha_hasta - fecha_desde).days > 730:
                raise ValidationError('El rango de fechas no puede ser mayor a 2 años.')
            
            if fecha_hasta > date.today():
                raise ValidationError('La fecha hasta no puede ser futura.')
        
        return cleaned_data

class EstadoCuñaForm(forms.Form):
    """Formulario para cambiar estado de cuña masivamente"""
    
    cuñas = forms.ModelMultipleChoiceField(
        queryset=CuñaPublicitaria.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        label='Seleccionar cuñas'
    )
    
    nuevo_estado = forms.ChoiceField(
        choices=[
            ('activa', 'Activar'),
            ('pausada', 'Pausar'),
            ('finalizada', 'Finalizar'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Nuevo estado'
    )
    
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre el cambio de estado'
        }),
        label='Observaciones'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filtrar cuñas según el rol del usuario
            queryset = CuñaPublicitaria.objects.all()
            
            if user.groups.filter(name='Clientes').exists():
                queryset = queryset.filter(cliente=user)
            elif user.groups.filter(name='Vendedores').exists():
                queryset = queryset.filter(vendedor_asignado=user)
            
            self.fields['cuñas'].queryset = queryset.filter(
                estado__in=['aprobada', 'activa', 'pausada']
            )