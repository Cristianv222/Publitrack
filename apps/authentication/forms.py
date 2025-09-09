from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from .models import CustomUser

class LoginForm(forms.Form):
    """Formulario de login personalizado"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Usuario o Email',
            'autofocus': True,
            'autocomplete': 'username'
        }),
        label='Usuario'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password'
        }),
        label='Contraseña'
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Recordarme'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            # Permitir login con email o username
            user = None
            if '@' in username:
                # Es un email
                try:
                    user_obj = CustomUser.objects.get(email=username)
                    username = user_obj.username
                except CustomUser.DoesNotExist:
                    pass
            
            # Verificar credenciales
            user = authenticate(username=username, password=password)
            if user is None:
                raise ValidationError('Usuario o contraseña incorrectos.')
            
            if not user.is_active:
                raise ValidationError('Esta cuenta está desactivada.')
            
            if user.status != 'activo':
                raise ValidationError(f'Esta cuenta está {user.get_status_display().lower()}.')
        
        return cleaned_data

class UserRegistrationForm(UserCreationForm):
    """Formulario para registrar nuevos usuarios"""
    
    # Campos básicos del usuario
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombres'
        }),
        label='Nombres'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellidos'
        }),
        label='Apellidos'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Email'
    )
    
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+51 999 999 999'
        }),
        label='Teléfono'
    )
    
    direccion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Dirección completa'
        }),
        label='Dirección'
    )
    
    # Campos de rol y estado
    rol = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'toggleRoleFields()'
        }),
        label='Rol'
    )
    
    status = forms.ChoiceField(
        choices=CustomUser.STATUS_CHOICES,
        required=True,
        initial='activo',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Estado'
    )
    
    # Campos específicos para clientes
    empresa = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control cliente-field',
            'placeholder': 'Nombre de la empresa'
        }),
        label='Empresa'
    )
    
    ruc_dni = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control cliente-field',
            'placeholder': 'RUC o DNI'
        }),
        label='RUC/DNI'
    )
    
    razon_social = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control cliente-field',
            'placeholder': 'Razón social de la empresa'
        }),
        label='Razón Social'
    )
    
    giro_comercial = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control cliente-field',
            'placeholder': 'Actividad comercial principal'
        }),
        label='Giro Comercial'
    )
    
    vendedor_asignado = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(rol='vendedor', status='activo'),
        required=False,
        empty_label="Seleccionar vendedor...",
        widget=forms.Select(attrs={
            'class': 'form-control cliente-field'
        }),
        label='Vendedor Asignado'
    )
    
    limite_credito = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control cliente-field',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        }),
        label='Límite de Crédito'
    )
    
    dias_credito = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control cliente-field',
            'placeholder': '30',
            'min': '0',
            'max': '365'
        }),
        label='Días de Crédito'
    )
    
    # Campos específicos para vendedores
    comision_porcentaje = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control vendedor-field',
            'placeholder': '10.00',
            'step': '0.01',
            'min': '0',
            'max': '100'
        }),
        label='Porcentaje de Comisión (%)'
    )
    
    meta_mensual = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control vendedor-field',
            'placeholder': '5000.00',
            'step': '0.01',
            'min': '0'
        }),
        label='Meta Mensual'
    )
    
    supervisor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(rol='admin', status='activo'),
        required=False,
        empty_label="Seleccionar supervisor...",
        widget=forms.Select(attrs={
            'class': 'form-control vendedor-field'
        }),
        label='Supervisor'
    )
    
    # Configuraciones de notificaciones
    notificaciones_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Notificaciones por Email'
    )
    
    notificaciones_sms = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Notificaciones por SMS'
    )
    
    class Meta:
        model = CustomUser
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password1', 'password2',
            'telefono', 'direccion', 'rol', 'status'
        )
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirmar contraseña'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customizar mensajes de ayuda
        self.fields['password1'].help_text = """
        <small class="form-text text-muted">
            • Mínimo 8 caracteres<br>
            • No debe ser muy común<br>
            • No puede ser solo números
        </small>
        """
        
        # Limpiar help_text de password2
        self.fields['password2'].help_text = None
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario con este email.")
        return email
    
    def clean_ruc_dni(self):
        ruc_dni = self.cleaned_data.get('ruc_dni')
        if ruc_dni and CustomUser.objects.filter(ruc_dni=ruc_dni).exists():
            raise ValidationError("Ya existe un usuario con este RUC/DNI.")
        return ruc_dni
    
    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        
        # Validaciones específicas por rol
        if rol == 'cliente':
            empresa = cleaned_data.get('empresa')
            ruc_dni = cleaned_data.get('ruc_dni')
            
            if not empresa and not ruc_dni:
                raise ValidationError('Los clientes deben tener al menos empresa o RUC/DNI.')
        
        elif rol == 'vendedor':
            comision = cleaned_data.get('comision_porcentaje')
            if comision and (comision < 0 or comision > 100):
                raise ValidationError('La comisión debe estar entre 0 y 100%.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Asignar campos básicos
        user.email = self.cleaned_data['email']
        user.telefono = self.cleaned_data.get('telefono')
        user.direccion = self.cleaned_data.get('direccion')
        user.rol = self.cleaned_data['rol']
        user.status = self.cleaned_data.get('status', 'activo')
        
        # Campos específicos según el rol
        if user.rol == 'cliente':
            user.empresa = self.cleaned_data.get('empresa')
            user.ruc_dni = self.cleaned_data.get('ruc_dni')
            user.razon_social = self.cleaned_data.get('razon_social')
            user.giro_comercial = self.cleaned_data.get('giro_comercial')
            user.vendedor_asignado = self.cleaned_data.get('vendedor_asignado')
            user.limite_credito = self.cleaned_data.get('limite_credito')
            user.dias_credito = self.cleaned_data.get('dias_credito')
        
        elif user.rol == 'vendedor':
            user.comision_porcentaje = self.cleaned_data.get('comision_porcentaje')
            user.meta_mensual = self.cleaned_data.get('meta_mensual')
            user.supervisor = self.cleaned_data.get('supervisor')
        
        # Configuraciones de notificaciones
        user.notificaciones_email = self.cleaned_data.get('notificaciones_email', True)
        user.notificaciones_sms = self.cleaned_data.get('notificaciones_sms', False)
        
        if commit:
            user.save()
        
        return user

class UserProfileForm(forms.ModelForm):
    """Formulario para editar perfil de usuario"""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'telefono', 'direccion',
            'empresa', 'ruc_dni', 'razon_social', 'giro_comercial',
            'notificaciones_email', 'notificaciones_sms', 
            'notificar_vencimientos', 'notificar_pagos',
            'tema_preferido', 'zona_horaria'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc_dni': forms.TextInput(attrs={'class': 'form-control'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control'}),
            'giro_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'notificaciones_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificaciones_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificar_vencimientos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notificar_pagos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tema_preferido': forms.Select(attrs={'class': 'form-control'}),
            'zona_horaria': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = kwargs.get('instance')
        
        # Mostrar solo campos relevantes según el rol
        if user and user.rol != 'cliente':
            # Ocultar campos específicos de cliente
            for field in ['empresa', 'ruc_dni', 'razon_social', 'giro_comercial']:
                if field in self.fields:
                    del self.fields[field]
        
        # No permitir cambiar email si no es admin
        # (implementar lógica según necesidades)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and CustomUser.objects.filter(
            email=email
        ).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Ya existe un usuario con este email.")
        return email

class PasswordChangeForm(DjangoPasswordChangeForm):
    """Formulario personalizado para cambio de contraseña"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Aplicar clases CSS
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Personalizar placeholders
        self.fields['old_password'].widget.attrs.update({
            'placeholder': 'Contraseña actual'
        })
        self.fields['new_password1'].widget.attrs.update({
            'placeholder': 'Nueva contraseña'
        })
        self.fields['new_password2'].widget.attrs.update({
            'placeholder': 'Confirmar nueva contraseña'
        })

class UserSearchForm(forms.Form):
    """Formulario para búsqueda de usuarios"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, email, empresa...'
        }),
        label='Buscar'
    )
    
    rol = forms.ChoiceField(
        choices=[('', 'Todos los roles')] + CustomUser.ROLE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Rol'
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + CustomUser.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Estado'
    )
    
    vendedor = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(rol='vendedor', status='activo'),
        required=False,
        empty_label="Todos los vendedores",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Vendedor'
    )