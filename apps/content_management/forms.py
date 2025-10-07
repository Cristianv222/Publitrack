"""
Formularios para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Formularios para cuñas publicitarias, archivos de audio y CONTRATOS
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from apps.authentication.models import CustomUser
from .models import (
    CategoriaPublicitaria, 
    TipoContrato, 
    ArchivoAudio, 
    CuñaPublicitaria,
    PlantillaContrato,
    ContratoGenerado
)

User = get_user_model()

# ==================== FORMULARIOS DE CATEGORÍAS ====================

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


# ==================== FORMULARIOS DE TIPOS DE CONTRATO ====================

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


# ==================== FORMULARIOS DE ARCHIVOS DE AUDIO ====================

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


# ==================== FORMULARIOS DE CUÑAS PUBLICITARIAS ====================

class CuñaPublicitariaForm(forms.ModelForm):
    """Formulario para cuñas publicitarias"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de clientes según rol
        if self.user:
            if self.user.rol == 'vendedor':
                # Vendedores ven todos los clientes
                self.fields['cliente'].queryset = CustomUser.objects.filter(rol='cliente', status='activo')
            elif self.user.rol == 'cliente':
                # Clientes solo se ven a sí mismos
                self.fields['cliente'].queryset = CustomUser.objects.filter(id=self.user.id)
                self.fields['cliente'].initial = self.user
                self.fields['cliente'].widget = forms.HiddenInput()
            else:
                # Admins ven todos los clientes
                self.fields['cliente'].queryset = CustomUser.objects.filter(rol='cliente')
        
        # Configurar queryset de vendedores
        self.fields['vendedor_asignado'].queryset = CustomUser.objects.filter(
            rol='vendedor',
            status='activo'
        )
        
        # Configurar queryset de categorías activas
        self.fields['categoria'].queryset = CategoriaPublicitaria.objects.filter(is_active=True)
        
        # Configurar queryset de tipos de contrato activos
        self.fields['tipo_contrato'].queryset = TipoContrato.objects.filter(is_active=True)
        
        # Configurar queryset de archivos de audio
        if self.user and self.user.rol == 'cliente':
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
            'excluir_sabados',
            'excluir_domingos',
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
            'excluir_sabados': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'excluir_domingos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
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
        queryset=CustomUser.objects.filter(rol='vendedor', status='activo'),
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


# ==================== FORMULARIOS DE PLANTILLAS DE CONTRATO ====================

class PlantillaContratoForm(forms.ModelForm):
    """Formulario para plantillas de contrato"""
    
    class Meta:
        model = PlantillaContrato
        fields = [
            'nombre', 
            'tipo_contrato', 
            'descripcion', 
            'archivo_plantilla',
            'incluye_iva', 
            'porcentaje_iva', 
            'instrucciones',
            'version', 
            'is_active', 
            'is_default'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Contrato Publicidad TV 2025'
            }),
            'tipo_contrato': forms.Select(attrs={
                'class': 'form-select'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de cuándo usar esta plantilla'
            }),
            'archivo_plantilla': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.docx'
            }),
            'incluye_iva': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'porcentaje_iva': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '15.00'
            }),
            'instrucciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Instrucciones sobre cómo usar esta plantilla'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'archivo_plantilla': '''
                Archivo Word (.docx) con variables en formato {{VARIABLE}}.<br>
                <strong>Variables disponibles:</strong><br>
                • {{NOMBRE_CLIENTE}} - Nombre o Razón Social<br>
                • {{RUC_DNI}} - RUC o Cédula<br>
                • {{CIUDAD}} - Ciudad del cliente<br>
                • {{PROVINCIA}} - Provincia del cliente<br>
                • {{DIRECCION_EXACTA}} - Dirección completa<br>
                • {{VALOR_LETRAS}} - Valor en letras<br>
                • {{VALOR_NUMEROS}} - Valor en números<br>
                • {{TOTAL_LETRAS}} - Total con IVA en letras<br>
                • {{TOTAL_NUMEROS}} - Total con IVA en números<br>
                • {{FECHA_INICIO}} - Fecha de inicio<br>
                • {{FECHA_FIN}} - Fecha de fin<br>
                • {{DURACION_DIAS}} - Duración en días<br>
                • {{DURACION_MESES}} - Duración en meses<br>
                • {{SPOTS_DIA}} - Spots por día<br>
                • {{NUMERO_CONTRATO}} - Número del contrato
            ''',
            'is_default': 'Si se marca, esta será la plantilla predeterminada para este tipo de contrato',
            'incluye_iva': 'Si se marca, calculará automáticamente el IVA sobre el valor base',
        }
        labels = {
            'nombre': 'Nombre de la Plantilla',
            'tipo_contrato': 'Tipo de Contrato',
            'descripcion': 'Descripción',
            'archivo_plantilla': 'Archivo Word de Plantilla',
            'incluye_iva': 'Incluir IVA en el cálculo',
            'porcentaje_iva': 'Porcentaje de IVA (%)',
            'instrucciones': 'Instrucciones de Uso',
            'version': 'Versión',
            'is_active': 'Plantilla Activa',
            'is_default': 'Plantilla Predeterminada',
        }
    
    def clean_archivo_plantilla(self):
        archivo = self.cleaned_data.get('archivo_plantilla')
        if archivo:
            # Validar que sea .docx
            if not archivo.name.endswith('.docx'):
                raise ValidationError('Solo se permiten archivos .docx (Word 2007 o superior)')
            
            # Validar tamaño (máximo 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no debe superar los 10MB')
        
        return archivo
    
    def clean_porcentaje_iva(self):
        porcentaje = self.cleaned_data.get('porcentaje_iva')
        if porcentaje and (porcentaje < 0 or porcentaje > 100):
            raise ValidationError('El porcentaje de IVA debe estar entre 0% y 100%')
        return porcentaje


class PlantillaContratoFiltroForm(forms.Form):
    """Formulario para filtrar plantillas de contrato"""
    
    tipo = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + PlantillaContrato.TIPO_CONTRATO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    activa = forms.ChoiceField(
        choices=[('', 'Todas'), ('true', 'Activas'), ('false', 'Inactivas')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    solo_default = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Solo plantillas predeterminadas'
    )


# ==================== FORMULARIOS DE CONTRATOS GENERADOS ====================

class ContratoGeneradoForm(forms.ModelForm):
    """Formulario para contratos generados (solo para edición manual)"""
    
    class Meta:
        model = ContratoGenerado
        fields = [
            'estado', 
            'observaciones'
        ]
        widgets = {
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones sobre el contrato'
            }),
        }


class ContratoGeneradoFiltroForm(forms.Form):
    """Formulario para filtrar contratos generados"""
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + ContratoGenerado.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Generado desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Generado hasta'
    )
    
    plantilla = forms.ModelChoiceField(
        queryset=PlantillaContrato.objects.filter(is_active=True),
        required=False,
        empty_label='Todas las plantillas',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    cliente_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por cliente o RUC'
        }),
        label='Buscar cliente'
    )


class GenerarContratoForm(forms.Form):
    """Formulario para seleccionar plantilla al generar contrato"""
    
    plantilla = forms.ModelChoiceField(
        queryset=PlantillaContrato.objects.filter(is_active=True),
        required=True,
        empty_label='Seleccione una plantilla',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Plantilla de Contrato'
    )
    
    observaciones_iniciales = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones iniciales (opcional)'
        }),
        label='Observaciones'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si hay una plantilla predeterminada, seleccionarla
        plantilla_default = PlantillaContrato.objects.filter(
            is_default=True,
            is_active=True
        ).first()
        
        if plantilla_default:
            self.fields['plantilla'].initial = plantilla_default


# ==================== FORMULARIOS AUXILIARES ====================

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
            
            if user.rol == 'cliente':
                queryset = queryset.filter(cliente=user)
            elif user.rol == 'vendedor':
                queryset = queryset.filter(vendedor_asignado=user)
            
            self.fields['cuñas'].queryset = queryset.filter(
                estado__in=['aprobada', 'activa', 'pausada']
            )


# ==================== FORMULARIOS DE CLIENTES ====================

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear/editar clientes SIN contraseña
    Los clientes son entidades comerciales que no requieren acceso al sistema
    """
    
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'telefono',
            'empresa',
            'ruc_dni',
            'razon_social',
            'giro_comercial',
            'ciudad',
            'provincia',
            'direccion_exacta',
            'vendedor_asignado',
            'limite_credito',
            'dias_credito',
            'status',
        ]
        
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usuario único para el cliente'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del contacto'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido del contacto'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de contacto'
            }),
            'empresa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre comercial de la empresa'
            }),
            'ruc_dni': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RUC o Cédula'
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razón social completa'
            }),
            'giro_comercial': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Actividad comercial'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad'
            }),
            'provincia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Provincia o Estado'
            }),
            'direccion_exacta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección completa y detallada'
            }),
            'vendedor_asignado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'limite_credito': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'dias_credito': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '30'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        
        labels = {
            'username': 'Usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'empresa': 'Nombre de la Empresa',
            'ruc_dni': 'RUC/Cédula',
            'razon_social': 'Razón Social',
            'giro_comercial': 'Giro Comercial',
            'ciudad': 'Ciudad',
            'provincia': 'Provincia/Estado',
            'direccion_exacta': 'Dirección Exacta',
            'vendedor_asignado': 'Vendedor Asignado',
            'limite_credito': 'Límite de Crédito',
            'dias_credito': 'Días de Crédito',
            'status': 'Estado',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo vendedores activos para el campo vendedor_asignado
        self.fields['vendedor_asignado'].queryset = CustomUser.objects.filter(
            rol='vendedor',
            status='activo',
            is_active=True
        )
        self.fields['vendedor_asignado'].required = False
        
        # Campos requeridos para clientes
        self.fields['empresa'].required = True
        self.fields['ruc_dni'].required = True
        self.fields['email'].required = True
        self.fields['telefono'].required = True
        self.fields['ciudad'].required = True
        self.fields['provincia'].required = True
    
    def clean_username(self):
        """Validar username único"""
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio.')
        
        # Verificar si ya existe (excepto en edición)
        qs = CustomUser.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        
        return username
    
    def clean_email(self):
        """Validar email único"""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('El correo electrónico es obligatorio.')
        
        # Verificar si ya existe (excepto en edición)
        qs = CustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        
        return email
    
    def clean_ruc_dni(self):
        """Validar RUC/DNI único"""
        ruc_dni = self.cleaned_data.get('ruc_dni')
        if not ruc_dni:
            raise ValidationError('El RUC/Cédula es obligatorio.')
        
        # Verificar si ya existe (excepto en edición)
        qs = CustomUser.objects.filter(ruc_dni=ruc_dni)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        
        if qs.exists():
            raise ValidationError('Este RUC/Cédula ya está registrado.')
        
        return ruc_dni
    
    def save(self, commit=True):
        """Guardar cliente SIN contraseña"""
        cliente = super().save(commit=False)
        
        # Establecer rol como cliente
        cliente.rol = 'cliente'
        
        # Si es nuevo cliente, configurar sin contraseña
        if not self.instance.pk:
            cliente.set_unusable_password()  # ✅ SIN contraseña
            cliente.is_active = True
            cliente.is_staff = False
            cliente.is_superuser = False
        
        if commit:
            cliente.save()
        
        return cliente