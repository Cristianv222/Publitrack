from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

class CustomUserManager(BaseUserManager):
    """Manager personalizado para el modelo CustomUser"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Crea y guarda un usuario regular"""
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Crea y guarda un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        extra_fields.setdefault('status', 'activo')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado para PubliTrack
    Sistema completo de gestión de publicidad radial/TV
    """
    
    # Opciones de roles
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('vendedor', 'Vendedor'),
        ('cliente', 'Cliente'),
        ('productor', 'Productor'),
        ('productor', 'Productor'),
        ('vtr', 'VTR'),
    ]
    
    # Estados del usuario
    STATUS_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('suspendido', 'Suspendido'),
        ('pendiente', 'Pendiente Verificación'),
    ]
    
    # INFORMACIÓN BÁSICA
    email = models.EmailField(
        'Email',
        unique=True,
        help_text='Dirección de email única del usuario'
    )
    
    telefono = models.CharField(
        'Teléfono',
        max_length=20,
        blank=True,
        null=True,
        help_text='Número de teléfono de contacto'
    )
    
    direccion = models.TextField(
        'Dirección',
        blank=True,
        null=True,
        help_text='Dirección completa del usuario'
    )
    
    # ROL Y ESTADO
    rol = models.CharField(
        'Rol',
        max_length=20,
        choices=ROLE_CHOICES,
        default='cliente',
        help_text='Rol del usuario en el sistema'
    )
    
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=STATUS_CHOICES,
        default='activo',
        help_text='Estado actual del usuario'
    )
    
    # FECHAS Y CONEXIONES
    fecha_registro = models.DateTimeField(
        'Fecha de Registro',
        auto_now_add=True
    )
    
    ultima_conexion = models.DateTimeField(
        'Última Conexión',
        null=True,
        blank=True
    )
    
    fecha_verificacion = models.DateTimeField(
        'Fecha de Verificación',
        null=True,
        blank=True
    )
    
    # INFORMACIÓN ESPECÍFICA PARA VENDEDORES
    comision_porcentaje = models.DecimalField(
        'Porcentaje de Comisión',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Porcentaje de comisión para vendedores (ej: 15.50)'
    )
    
    meta_mensual = models.DecimalField(
        'Meta Mensual',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Meta de ventas mensual para vendedores'
    )
    
    supervisor = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendedores_supervisados',
        limit_choices_to={'rol': 'admin'},
        verbose_name='Supervisor',
        help_text='Supervisor asignado al vendedor'
    )
    
    # INFORMACIÓN ESPECÍFICA PARA CLIENTES
    empresa = models.CharField(
        'Empresa',
        max_length=200,
        blank=True,
        null=True,
        help_text='Nombre de la empresa del cliente'
    )
    
    cargo_empresa = models.CharField(
        'Cargo en la Empresa',
        max_length=100,
        blank=True,
        null=True,
        help_text='Cargo que ocupa el cliente en la empresa (ej: Gerente, Director, etc.)'
    )   

    profesion = models.CharField(
        'Profesión/Título',
        max_length=100,
        blank=True,
        null=True,
        help_text='Título profesional (ej: Ing., Msc., Doc., Lic., etc.)'
    )

    ruc_dni = models.CharField(
        'RUC/DNI',
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        help_text='Número de RUC o DNI del cliente'
    )
    
    razon_social = models.CharField(
        'Razón Social',
        max_length=255,
        blank=True,
        null=True,
        help_text='Razón social de la empresa'
    )
    
    giro_comercial = models.CharField(
        'Giro Comercial',
        max_length=200,
        blank=True,
        null=True,
        help_text='Actividad comercial principal'
    )
    
    vendedor_asignado = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes_asignados',
        limit_choices_to={'rol': 'vendedor'},
        verbose_name='Vendedor Asignado',
        help_text='Vendedor responsable del cliente'
    )
    ciudad = models.CharField(
        'Ciudad',
        max_length=100,
        blank=True,
        null=True,
        help_text='Ciudad del cliente'
    )
    
    provincia = models.CharField(
        'Provincia/Estado',
        max_length=100,
        blank=True,
        null=True,
        help_text='Provincia o estado del cliente'
    )
    
    direccion_exacta = models.TextField(
        'Dirección Exacta',
        blank=True,
        null=True,
        help_text='Dirección completa y detallada del cliente'
    )

    # CONFIGURACIONES DE NOTIFICACIONES
    notificaciones_email = models.BooleanField(
        'Notificaciones por Email',
        default=True,
        help_text='Recibir notificaciones por correo electrónico'
    )
    
    notificaciones_sms = models.BooleanField(
        'Notificaciones por SMS',
        default=False,
        help_text='Recibir notificaciones por SMS'
    )
    
    notificar_vencimientos = models.BooleanField(
        'Notificar Vencimientos',
        default=True,
        help_text='Recibir alertas de vencimientos de cuñas'
    )
    
    notificar_pagos = models.BooleanField(
        'Notificar Pagos',
        default=True,
        help_text='Recibir notificaciones de pagos y cobros'
    )
    
    # CONFIGURACIONES FINANCIERAS
    limite_credito = models.DecimalField(
        'Límite de Crédito',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Límite de crédito para clientes'
    )
    
    dias_credito = models.PositiveIntegerField(
        'Días de Crédito',
        null=True,
        blank=True,
        help_text='Días de crédito permitidos'
    )
    
    # CONFIGURACIONES DEL SISTEMA
    tema_preferido = models.CharField(
        'Tema Preferido',
        max_length=20,
        choices=[
            ('light', 'Claro'),
            ('dark', 'Oscuro'),
            ('auto', 'Automático'),
        ],
        default='light'
    )
    
    zona_horaria = models.CharField(
        'Zona Horaria',
        max_length=50,
        default='America/Lima'
    )
    
    # METADATOS
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    # Manager personalizado
    objects = CustomUserManager()
    
    # Configuración del modelo
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rol', 'status']),
            models.Index(fields=['email']),
            models.Index(fields=['ruc_dni']),
            models.Index(fields=['vendedor_asignado']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para validaciones personalizadas"""
        if self.pk:
            old_user = CustomUser.objects.get(pk=self.pk)
            if old_user.email != self.email:
                self.fecha_verificacion = None
        
        if self.rol == 'vendedor' and not self.comision_porcentaje:
            self.comision_porcentaje = Decimal('10.00')
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('authentication:user_detail', kwargs={'pk': self.pk})
    
    # PROPIEDADES DE ROL
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'admin'
    
    @property
    def es_vendedor(self):
        """Verifica si el usuario es vendedor"""
        return self.rol == 'vendedor'
    
    @property
    def es_cliente(self):
        """Verifica si el usuario es cliente"""
        return self.rol == 'cliente'
    
    @property
    def es_productor(self):
        """Verifica si el usuario es productor"""
        return self.rol == 'productor'

    @property
    def es_vtr(self):
        """Verifica si el usuario es VTR"""
        return self.rol == 'vtr'

    @property
    def es_doctor(self):
        """Verifica si el usuario es doctor"""
        return self.rol == 'doctor'
    
    @property
    def esta_activo(self):
        """Verifica si el usuario está activo"""
        return self.status == 'activo' and self.is_active
    
    # MÉTODOS DE PERMISOS
    def puede_gestionar_usuarios(self):
        """Verifica si puede gestionar otros usuarios"""
        return self.es_admin
    
    def puede_ver_finanzas(self):
        """Verifica si puede ver información financiera"""
        return self.rol in ['admin', 'vendedor']
    
    def puede_gestionar_cuñas(self):
        """Verifica si puede gestionar cuñas publicitarias"""
        return self.rol in ['admin', 'vendedor', 'productor', 'vtr']
    
    def puede_ver_reportes(self):
        """Verifica si puede ver reportes"""
        return self.rol in ['admin', 'vendedor']
    
    def puede_configurar_sistema(self):
        """Verifica si puede configurar el sistema"""
        return self.es_admin
    
    # MÉTODOS DE PERMISOS AVANZADOS
    def has_permission(self, permission_codename):
        """Verifica si el usuario tiene un permiso específico"""
        if not self.is_active or self.status != 'activo':
            return False
        
        if self.is_superuser:
            return True
        
        try:
            role = Role.objects.get(codename=self.rol, is_active=True)
            return role.permissions.filter(
                codename=permission_codename,
                is_active=True
            ).exists()
        except Role.DoesNotExist:
            return False

    def has_module_access(self, module_name):
        """Verifica si el usuario tiene acceso a un módulo"""
        if not self.is_active or self.status != 'activo':
            return False
        
        if self.is_superuser:
            return True
        
        module_permissions = {
            'authentication': ['admin'],
            'content_management': ['admin', 'vendedor', 'productor', 'vtr'],
            'financial_management': ['admin'],
            'traffic_light_system': ['admin', 'vendedor'],
            'transmission_control': ['admin', 'vendedor', 'productor', 'vtr'],
            'notifications': ['admin', 'vendedor', 'productor', 'vtr'],
            'sales_management': ['admin', 'vendedor'],
            'reports_analytics': ['admin', 'vendedor'],
            'system_configuration': ['admin'],
        }
        
        return self.rol in module_permissions.get(module_name, [])

    def get_user_permissions(self):
        """Retorna todos los permisos del usuario"""
        if not self.is_active or self.status != 'activo':
            return Permission.objects.none()
        
        if self.is_superuser:
            return Permission.objects.filter(is_active=True) if Permission.objects.exists() else Permission.objects.none()
        
        try:
            role = Role.objects.get(codename=self.rol, is_active=True)
            return role.permissions.filter(is_active=True)
        except Role.DoesNotExist:
            return Permission.objects.none()

    def get_permissions_by_module(self):
        """Retorna permisos del usuario agrupados por módulo"""
        from collections import defaultdict
        perms_by_module = defaultdict(list)
        
        for perm in self.get_user_permissions():
            perms_by_module[perm.module].append(perm)
        
        return dict(perms_by_module)

    def can_manage_users(self):
        """Verifica si puede gestionar usuarios"""
        return self.has_permission('manage_users') or self.es_admin

    def can_view_reports(self):
        """Verifica si puede ver reportes"""
        return self.has_permission('view_reports') or self.rol in ['admin', 'vendedor']

    def can_manage_content(self):
        """Verifica si puede gestionar contenido"""
        return self.has_permission('manage_content') or self.rol in ['admin', 'vendedor', 'productor', 'vtr']

    def can_manage_finances(self):
        """Verifica si puede gestionar finanzas"""
        return self.has_permission('manage_finances') or self.es_admin

    def can_configure_system(self):
        """Verifica si puede configurar el sistema"""
        return self.has_permission('configure_system') or self.es_admin
    
    # MÉTODOS DE RELACIONES
    def get_clientes(self):
        """Obtiene los clientes asignados (para vendedores)"""
        if self.es_vendedor:
            return CustomUser.objects.filter(
                vendedor_asignado=self,
                status='activo',
                rol='cliente'
            )
        return CustomUser.objects.none()
    
    def get_vendedor(self):
        """Obtiene el vendedor asignado (para clientes)"""
        if self.es_cliente and self.vendedor_asignado:
            return self.vendedor_asignado
        return None
    
    def get_supervisor(self):
        """Obtiene el supervisor (para vendedores)"""
        if self.es_vendedor and self.supervisor:
            return self.supervisor
        return None
    
    # MÉTODOS DE ESTADÍSTICAS
    def get_total_clientes(self):
        """Total de clientes asignados (para vendedores)"""
        return self.get_clientes().count()
    
    def get_ventas_mes_actual(self):
        """Ventas del mes actual (implementar con el modelo de ventas)"""
        return Decimal('0.00')
    
    def get_comisiones_mes_actual(self):
        """Comisiones del mes actual (implementar con el modelo de comisiones)"""
        return Decimal('0.00')
    
    def get_porcentaje_meta(self):
        """Porcentaje de cumplimiento de meta"""
        if self.meta_mensual and self.meta_mensual > 0:
            ventas = self.get_ventas_mes_actual()
            return (ventas / self.meta_mensual) * 100
        return 0
    
    # MÉTODOS DE VALIDACIÓN
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        if self.email and CustomUser.objects.filter(
            email=self.email
        ).exclude(pk=self.pk).exists():
            raise ValidationError({'email': 'Ya existe un usuario con este email.'})
        
        if self.ruc_dni and CustomUser.objects.filter(
            ruc_dni=self.ruc_dni
        ).exclude(pk=self.pk).exists():
            raise ValidationError({'ruc_dni': 'Ya existe un usuario con este RUC/DNI.'})
        
        if self.rol == 'cliente':
            if not self.empresa and not self.ruc_dni:
                raise ValidationError('Los clientes deben tener empresa o RUC/DNI.')
        
        if self.rol == 'vendedor':
            if self.comision_porcentaje and (self.comision_porcentaje < 0 or self.comision_porcentaje > 100):
                raise ValidationError({'comision_porcentaje': 'La comisión debe estar entre 0 y 100.'})
    
    # MÉTODOS DE UTILIDAD
    def marcar_ultima_conexion(self):
        """Actualiza la última conexión del usuario"""
        self.ultima_conexion = timezone.now()
        self.save(update_fields=['ultima_conexion'])
    
    def activar(self):
        """Activa el usuario"""
        self.status = 'activo'
        self.is_active = True
        self.save(update_fields=['status', 'is_active'])
    
    def desactivar(self):
        """Desactiva el usuario"""
        self.status = 'inactivo'
        self.is_active = False
        self.save(update_fields=['status', 'is_active'])
    
    def suspender(self):
        """Suspende el usuario"""
        self.status = 'suspendido'
        self.is_active = False
        self.save(update_fields=['status', 'is_active'])


class UserLoginHistory(models.Model):
    """Historial de conexiones de usuarios"""
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    
    login_time = models.DateTimeField('Hora de Ingreso', auto_now_add=True)
    logout_time = models.DateTimeField('Hora de Salida', null=True, blank=True)
    ip_address = models.GenericIPAddressField('Dirección IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    session_key = models.CharField('Session Key', max_length=40, blank=True)
    
    class Meta:
        verbose_name = 'Historial de Conexión'
        verbose_name_plural = 'Historial de Conexiones'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def duracion_sesion(self):
        """Calcula la duración de la sesión"""
        if self.logout_time:
            return self.logout_time - self.login_time
        return None


class Permission(models.Model):
    """
    Sistema de permisos granular para PubliTrack
    """
    
    MODULE_CHOICES = [
        ('authentication', 'Autenticación y Usuarios'),
        ('content_management', 'Gestión de Contenido'),
        ('financial_management', 'Gestión Financiera'),
        ('traffic_light_system', 'Sistema de Semáforos'),
        ('transmission_control', 'Control de Transmisiones'),
        ('notifications', 'Notificaciones'),
        ('sales_management', 'Gestión de Ventas'),
        ('reports_analytics', 'Reportes y Analíticas'),
        ('system_configuration', 'Configuración del Sistema'),
    ]
    
    ACTION_CHOICES = [
        ('view', 'Ver'),
        ('add', 'Agregar'),
        ('change', 'Modificar'),
        ('delete', 'Eliminar'),
        ('export', 'Exportar'),
        ('approve', 'Aprobar'),
        ('assign', 'Asignar'),
        ('configure', 'Configurar'),
    ]
    
    name = models.CharField(
        'Nombre',
        max_length=100,
        unique=True,
        help_text='Nombre descriptivo del permiso'
    )
    
    codename = models.CharField(
        'Código',
        max_length=100,
        unique=True,
        help_text='Código único del permiso (ej: view_users)'
    )
    
    module = models.CharField(
        'Módulo',
        max_length=50,
        choices=MODULE_CHOICES,
        help_text='Módulo al que pertenece este permiso'
    )
    
    action = models.CharField(
        'Acción',
        max_length=20,
        choices=ACTION_CHOICES,
        help_text='Tipo de acción que permite'
    )
    
    description = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción detallada del permiso'
    )
    
    is_active = models.BooleanField(
        'Activo',
        default=True,
        help_text='Si el permiso está activo en el sistema'
    )
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['module', 'action', 'name']
        indexes = [
            models.Index(fields=['module', 'action']),
            models.Index(fields=['codename']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_module_display()})"


class Role(models.Model):
    """
    Roles del sistema con permisos asociados
    """
    
    name = models.CharField(
        'Nombre',
        max_length=50,
        unique=True,
        help_text='Nombre del rol'
    )
    
    codename = models.CharField(
        'Código',
        max_length=50,
        unique=True,
        help_text='Código único del rol'
    )
    
    description = models.TextField(
        'Descripción',
        blank=True,
        help_text='Descripción del rol y sus responsabilidades'
    )
    
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        verbose_name='Permisos',
        help_text='Permisos asociados a este rol'
    )
    
    is_system_role = models.BooleanField(
        'Rol del Sistema',
        default=False,
        help_text='Si es un rol predefinido del sistema'
    )
    
    is_active = models.BooleanField(
        'Activo',
        default=True,
        help_text='Si el rol está activo'
    )
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_permissions_by_module(self):
        """Retorna permisos agrupados por módulo"""
        from collections import defaultdict
        perms_by_module = defaultdict(list)
        
        for perm in self.permissions.filter(is_active=True):
            perms_by_module[perm.module].append(perm)
        
        return dict(perms_by_module)


class RolePermission(models.Model):
    """
    Relación entre roles y permisos con metadatos adicionales
    """
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name='Rol'
    )
    
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        verbose_name='Permiso'
    )
    
    granted_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Otorgado por',
        help_text='Usuario que otorgó este permiso al rol'
    )
    
    granted_at = models.DateTimeField(
        'Fecha de Otorgamiento',
        auto_now_add=True
    )
    
    notes = models.TextField(
        'Notas',
        blank=True,
        help_text='Notas sobre este permiso'
    )
    
    class Meta:
        verbose_name = 'Permiso de Rol'
        verbose_name_plural = 'Permisos de Roles'
        unique_together = ['role', 'permission']
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"