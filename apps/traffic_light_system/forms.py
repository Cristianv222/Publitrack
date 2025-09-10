"""
Formularios para el Sistema de Semáforos
Sistema PubliTrack - Forms para configuración y filtros
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import ConfiguracionSemaforo, AlertaSemaforo
from apps.content_management.models import CategoriaPublicitaria
from apps.authentication.models import CustomUser


class ConfiguracionSemaforoForm(forms.ModelForm):
    """
    Formulario para crear/editar configuraciones de semáforo
    """
    
    class Meta:
        model = ConfiguracionSemaforo
        fields = [
            'nombre', 'descripcion', 'tipo_calculo',
            'dias_verde_min', 'dias_amarillo_min',
            'porcentaje_verde_max', 'porcentaje_amarillo_max',
            'estados_verde', 'estados_amarillo', 'estados_rojo', 'estados_gris',
            'enviar_alertas', 'alertas_solo_empeoramiento'
        ]
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la configuración'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada de la configuración'
            }),
            'tipo_calculo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'dias_verde_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 365
            }),
            'dias_amarillo_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 365
            }),
            'porcentaje_verde_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.01
            }),
            'porcentaje_amarillo_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.01
            }),
            'enviar_alertas': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'alertas_solo_empeoramiento': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'nombre': 'Nombre de la Configuración',
            'descripcion': 'Descripción',
            'tipo_calculo': 'Tipo de Cálculo',
            'dias_verde_min': 'Días Mínimos para Verde',
            'dias_amarillo_min': 'Días Mínimos para Amarillo',
            'porcentaje_verde_max': 'Porcentaje Máximo para Verde (%)',
            'porcentaje_amarillo_max': 'Porcentaje Máximo para Amarillo (%)',
            'enviar_alertas': 'Enviar Alertas Automáticas',
            'alertas_solo_empeoramiento': 'Alertas Solo por Empeoramiento'
        }
        
        help_texts = {
            'dias_verde_min': 'Días restantes mínimos para considerar estado verde',
            'dias_amarillo_min': 'Días restantes mínimos para amarillo (menos que esto será rojo)',
            'porcentaje_verde_max': 'Porcentaje máximo de tiempo transcurrido para verde',
            'porcentaje_amarillo_max': 'Porcentaje máximo de tiempo transcurrido para amarillo',
            'enviar_alertas': 'Si el sistema debe generar alertas automáticamente',
            'alertas_solo_empeoramiento': 'Solo alertar cuando el estado empeore (verde→amarillo→rojo)'
        }
    
    # Campos personalizados para manejar estados como checkboxes
    estados_opciones = [
        ('borrador', 'Borrador'),
        ('pendiente_revision', 'Pendiente de Revisión'),
        ('en_produccion', 'En Producción'),
        ('aprobada', 'Aprobada'),
        ('activa', 'Activa'),
        ('pausada', 'Pausada'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    estados_verde_check = forms.MultipleChoiceField(
        choices=estados_opciones,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Estados que muestran Verde'
    )
    
    estados_amarillo_check = forms.MultipleChoiceField(
        choices=estados_opciones,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Estados que muestran Amarillo'
    )
    
    estados_rojo_check = forms.MultipleChoiceField(
        choices=estados_opciones,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Estados que muestran Rojo'
    )
    
    estados_gris_check = forms.MultipleChoiceField(
        choices=estados_opciones,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Estados que muestran Gris'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, poblar los checkboxes con los valores actuales
        if self.instance and self.instance.pk:
            self.fields['estados_verde_check'].initial = self.instance.estados_verde or []
            self.fields['estados_amarillo_check'].initial = self.instance.estados_amarillo or []
            self.fields['estados_rojo_check'].initial = self.instance.estados_rojo or []
            self.fields['estados_gris_check'].initial = self.instance.estados_gris or []
        else:
            # Valores por defecto para nueva configuración
            self.fields['estados_verde_check'].initial = ['activa', 'aprobada']
            self.fields['estados_amarillo_check'].initial = ['pendiente_revision', 'en_produccion', 'pausada']
            self.fields['estados_rojo_check'].initial = ['borrador']
            self.fields['estados_gris_check'].initial = ['finalizada', 'cancelada']
        
        # Remover los campos JSONField originales del formulario visible
        self.fields['estados_verde'].widget = forms.HiddenInput()
        self.fields['estados_amarillo'].widget = forms.HiddenInput()
        self.fields['estados_rojo'].widget = forms.HiddenInput()
        self.fields['estados_gris'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar que los días tengan sentido
        dias_verde = cleaned_data.get('dias_verde_min')
        dias_amarillo = cleaned_data.get('dias_amarillo_min')
        
        if dias_verde and dias_amarillo and dias_amarillo >= dias_verde:
            raise ValidationError(
                "Los días mínimos para amarillo deben ser menores que los días para verde."
            )
        
        # Validar que los porcentajes tengan sentido
        porcentaje_verde = cleaned_data.get('porcentaje_verde_max')
        porcentaje_amarillo = cleaned_data.get('porcentaje_amarillo_max')
        
        if porcentaje_verde and porcentaje_amarillo and porcentaje_verde >= porcentaje_amarillo:
            raise ValidationError(
                "El porcentaje máximo para verde debe ser menor que el porcentaje para amarillo."
            )
        
        # Convertir checkboxes a listas para los campos JSON
        cleaned_data['estados_verde'] = list(cleaned_data.get('estados_verde_check', []))
        cleaned_data['estados_amarillo'] = list(cleaned_data.get('estados_amarillo_check', []))
        cleaned_data['estados_rojo'] = list(cleaned_data.get('estados_rojo_check', []))
        cleaned_data['estados_gris'] = list(cleaned_data.get('estados_gris_check', []))
        
        # Validar que no hay estados duplicados entre colores
        todos_estados = (
            cleaned_data['estados_verde'] + 
            cleaned_data['estados_amarillo'] + 
            cleaned_data['estados_rojo'] + 
            cleaned_data['estados_gris']
        )
        
        if len(todos_estados) != len(set(todos_estados)):
            raise ValidationError(
                "Un estado no puede estar asignado a múltiples colores."
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Asignar las listas de estados desde los checkboxes
        instance.estados_verde = self.cleaned_data.get('estados_verde', [])
        instance.estados_amarillo = self.cleaned_data.get('estados_amarillo', [])
        instance.estados_rojo = self.cleaned_data.get('estados_rojo', [])
        instance.estados_gris = self.cleaned_data.get('estados_gris', [])
        
        if commit:
            instance.save()
        
        return instance


class FiltroEstadosForm(forms.Form):
    """
    Formulario para filtrar la lista de estados
    """
    
    COLOR_CHOICES = [
        ('', 'Todos los colores'),
        ('verde', 'Verde'),
        ('amarillo', 'Amarillo'),
        ('rojo', 'Rojo'),
        ('gris', 'Gris'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('', 'Todas las prioridades'),
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    buscar = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, título, cliente...'
        }),
        label='Buscar'
    )
    
    color = forms.ChoiceField(
        choices=COLOR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Color del Semáforo'
    )
    
    prioridad = forms.ChoiceField(
        choices=PRIORIDAD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Prioridad'
    )
    
    cliente = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(rol='cliente', is_active=True),
        required=False,
        empty_label='Todos los clientes',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cliente'
    )
    
    vendedor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(rol='vendedor', is_active=True),
        required=False,
        empty_label='Todos los vendedores',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Vendedor'
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaPublicitaria.objects.filter(is_active=True),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Categoría'
    )
    
    requiere_alerta = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Solo cuñas que requieren alerta'
    )
    
    fecha_vencimiento_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Vence desde'
    )
    
    fecha_vencimiento_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Vence hasta'
    )


class FiltroHistorialForm(forms.Form):
    """
    Formulario para filtrar el historial de cambios
    """
    
    COLOR_CHOICES = [
        ('', 'Todos los colores'),
        ('verde', 'Verde'),
        ('amarillo', 'Amarillo'),
        ('rojo', 'Rojo'),
        ('gris', 'Gris'),
    ]
    
    cuña_codigo = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de cuña'
        }),
        label='Código de Cuña'
    )
    
    color_anterior = forms.ChoiceField(
        choices=COLOR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Color Anterior'
    )
    
    color_nuevo = forms.ChoiceField(
        choices=COLOR_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Color Nuevo'
    )
    
    fecha_desde = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Hasta'
    )
    
    solo_con_alertas = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Solo cambios que generaron alertas'
    )


class FiltroAlertasForm(forms.Form):
    """
    Formulario para filtrar alertas
    """
    
    TIPO_CHOICES = [
        ('', 'Todos los tipos'),
        ('cambio_estado', 'Cambio de Estado'),
        ('vencimiento_proximo', 'Vencimiento Próximo'),
        ('estado_critico', 'Estado Crítico'),
        ('revision_requerida', 'Revisión Requerida'),
        ('configuracion_cambio', 'Cambio de Configuración'),
    ]
    
    SEVERIDAD_CHOICES = [
        ('', 'Todas las severidades'),
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('critical', 'Crítico'),
    ]
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('pendiente', 'Pendiente'),
        ('enviada', 'Enviada'),
        ('error', 'Error al Enviar'),
        ('ignorada', 'Ignorada'),
    ]
    
    tipo_alerta = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo de Alerta'
    )
    
    severidad = forms.ChoiceField(
        choices=SEVERIDAD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Severidad'
    )
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    
    cuña_codigo = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de cuña'
        }),
        label='Código de Cuña'
    )
    
    fecha_desde = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Creada desde'
    )
    
    fecha_hasta = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Creada hasta'
    )


class EnvioAlertaManualForm(forms.ModelForm):
    """
    Formulario para enviar alertas manuales
    """
    
    class Meta:
        model = AlertaSemaforo
        fields = [
            'cuña', 'tipo_alerta', 'severidad', 'titulo', 'mensaje',
            'enviar_email', 'enviar_sms', 'enviar_push', 'mostrar_dashboard'
        ]
        
        widgets = {
            'cuña': forms.Select(attrs={'class': 'form-select'}),
            'tipo_alerta': forms.Select(attrs={'class': 'form-select'}),
            'severidad': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la alerta'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mensaje detallado de la alerta'
            }),
            'enviar_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enviar_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enviar_push': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_dashboard': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    destinatarios_usuarios = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Usuarios Específicos'
    )
    
    destinatarios_roles = forms.MultipleChoiceField(
        choices=[
            ('admin', 'Administradores'),
            ('vendedor', 'Vendedores'),
            ('cliente', 'Clientes'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Roles'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar cuñas activas solamente
        self.fields['cuña'].queryset = CuñaPublicitaria.objects.filter(
            estado__in=['activa', 'aprobada', 'pendiente_revision', 'en_produccion']
        ).select_related('cliente')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # Agregar destinatarios
            if self.cleaned_data.get('destinatarios_usuarios'):
                instance.usuarios_destino.set(self.cleaned_data['destinatarios_usuarios'])
            
            if self.cleaned_data.get('destinatarios_roles'):
                instance.roles_destino = list(self.cleaned_data['destinatarios_roles'])
                instance.save()
        
        return instance


class ConfiguracionRapidaForm(forms.Form):
    """
    Formulario para configuración rápida del sistema
    """
    
    PERFIL_CHOICES = [
        ('conservador', 'Conservador - Alertas tempranas'),
        ('equilibrado', 'Equilibrado - Balance entre alertas y ruido'),
        ('agresivo', 'Agresivo - Solo alertas críticas'),
    ]
    
    perfil = forms.ChoiceField(
        choices=PERFIL_CHOICES,
        widget=forms.RadioSelect,
        label='Perfil de Configuración'
    )
    
    nombre_configuracion = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre para la nueva configuración'
        }),
        label='Nombre'
    )
    
    activar_inmediatamente = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Activar inmediatamente'
    )
    
    def save(self):
        """Crea una configuración basada en el perfil seleccionado"""
        perfil = self.cleaned_data['perfil']
        nombre = self.cleaned_data['nombre_configuracion']
        
        if perfil == 'conservador':
            config_data = {
                'dias_verde_min': 21,
                'dias_amarillo_min': 14,
                'porcentaje_verde_max': Decimal('40.00'),
                'porcentaje_amarillo_max': Decimal('70.00'),
                'enviar_alertas': True,
                'alertas_solo_empeoramiento': False,
            }
        elif perfil == 'equilibrado':
            config_data = {
                'dias_verde_min': 15,
                'dias_amarillo_min': 7,
                'porcentaje_verde_max': Decimal('50.00'),
                'porcentaje_amarillo_max': Decimal('85.00'),
                'enviar_alertas': True,
                'alertas_solo_empeoramiento': True,
            }
        else:  # agresivo
            config_data = {
                'dias_verde_min': 10,
                'dias_amarillo_min': 3,
                'porcentaje_verde_max': Decimal('70.00'),
                'porcentaje_amarillo_max': Decimal('95.00'),
                'enviar_alertas': True,
                'alertas_solo_empeoramiento': True,
            }
        
        # Crear la configuración
        configuracion = ConfiguracionSemaforo.objects.create(
            nombre=nombre,
            descripcion=f'Configuración automática - Perfil {perfil}',
            tipo_calculo='combinado',
            is_active=self.cleaned_data['activar_inmediatamente'],
            **config_data
        )
        
        return configuracion