from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser, UserLoginHistory

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Administración personalizada para CustomUser con campos dinámicos"""
    
    # Campos que se muestran en la lista
    list_display = (
        'username', 'get_full_name', 'email', 'rol', 'status_badge', 
        'empresa', 'vendedor_asignado', 'ultima_conexion', 'created_at'
    )
    
    # Filtros laterales
    list_filter = (
        'rol', 'status', 'is_active', 'is_staff', 'created_at', 'ultima_conexion'
    )
    
    # Campos de búsqueda
    search_fields = (
        'username', 'first_name', 'last_name', 'email', 
        'empresa', 'ruc_dni', 'telefono'
    )
    
    # Campos para ordenar
    ordering = ('-created_at',)
    
    # Campos de solo lectura
    readonly_fields = (
        'created_at', 'updated_at', 'fecha_registro', 'ultima_conexion',
        'date_joined', 'last_login'
    )
    
    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('username', 'password', 'first_name', 'last_name', 'email')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'direccion')
        }),
        ('Rol y Estado', {
            'fields': ('rol', 'status', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Información de Cliente', {
            'fields': ('empresa', 'ruc_dni', 'razon_social', 'giro_comercial', 
                      'vendedor_asignado', 'limite_credito', 'dias_credito'),
            'classes': ('collapse',),
            'description': 'Información específica para clientes'
        }),
        ('Información de Vendedor', {
            'fields': ('comision_porcentaje', 'meta_mensual', 'supervisor'),
            'classes': ('collapse',),
            'description': 'Información específica para vendedores'
        }),
        ('Configuraciones de Notificaciones', {
            'fields': ('notificaciones_email', 'notificaciones_sms', 
                      'notificar_vencimientos', 'notificar_pagos'),
            'classes': ('collapse',),
        }),
        ('Configuraciones del Sistema', {
            'fields': ('tema_preferido', 'zona_horaria'),
            'classes': ('collapse',),
        }),
        ('Permisos', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Fechas Importantes', {
            'fields': ('date_joined', 'last_login', 'fecha_registro', 
                      'ultima_conexion', 'fecha_verificacion', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Fieldsets para agregar usuario - TODOS los campos disponibles
    add_fieldsets = (
        ('Información Básica', {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 
                      'password1', 'password2'),
        }),
        ('Rol y Estado', {
            'fields': ('rol', 'status'),
            'description': 'Selecciona el rol para mostrar campos específicos'
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'direccion'),
        }),
        ('Información de Cliente/Empresa', {
            'fields': ('empresa', 'ruc_dni', 'razon_social', 'giro_comercial', 'vendedor_asignado', 'limite_credito', 'dias_credito'),
            'classes': ('cliente-fields',),
            'description': '⚠️ REQUERIDO para clientes: Al menos empresa o RUC/DNI'
        }),
        ('Información de Vendedor', {
            'fields': ('comision_porcentaje', 'meta_mensual', 'supervisor'),
            'classes': ('vendedor-fields',),
            'description': 'Solo para vendedores'
        }),
        ('Configuraciones', {
            'fields': ('notificaciones_email', 'notificaciones_sms'),
            'classes': ('collapse',),
        }),
    )
    
    # JavaScript para mostrar/ocultar campos según el rol
    class Media:
        js = ('admin/js/rol_dependent_fields.js',)
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    
    def get_form(self, request, obj=None, change=False, **kwargs):
        """Personaliza el formulario según si es creación o edición"""
        form = super().get_form(request, obj, change, **kwargs)
        
        # Si es creación de usuario, agregar JavaScript
        if not change:  # Creación
            form.Media.js = form.Media.js + ('admin/js/rol_dependent_fields.js',)
            
        return form
    
    # Acciones personalizadas
    actions = ['activar_usuarios', 'desactivar_usuarios', 'marcar_como_pendientes']
    
    def get_full_name(self, obj):
        """Muestra el nombre completo"""
        return obj.nombre_completo
    get_full_name.short_description = 'Nombre Completo'
    
    def status_badge(self, obj):
        """Muestra el estado con colores"""
        colors = {
            'activo': 'success',
            'inactivo': 'secondary',
            'suspendido': 'danger',
            'pendiente': 'warning'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'vendedor_asignado', 'supervisor'
        )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra las opciones de foreign keys"""
        if db_field.name == "vendedor_asignado":
            kwargs["queryset"] = CustomUser.objects.filter(
                rol='vendedor', status='activo'
            )
        elif db_field.name == "supervisor":
            kwargs["queryset"] = CustomUser.objects.filter(
                rol='admin', status='activo'
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Validación adicional antes de guardar"""
        if obj.rol == 'cliente':
            if not obj.empresa and not obj.ruc_dni:
                from django.core.exceptions import ValidationError
                from django.contrib import messages
                messages.error(request, 'Los clientes deben tener al menos empresa o RUC/DNI.')
                raise ValidationError('Los clientes deben tener al menos empresa o RUC/DNI.')
        super().save_model(request, obj, form, change)
    
    # Acciones personalizadas
    def activar_usuarios(self, request, queryset):
        """Activa los usuarios seleccionados"""
        count = 0
        for user in queryset:
            if user.status != 'activo':
                user.activar()
                count += 1
        
        self.message_user(
            request,
            f'{count} usuario(s) activado(s) exitosamente.'
        )
    activar_usuarios.short_description = "Activar usuarios seleccionados"
    
    def desactivar_usuarios(self, request, queryset):
        """Desactiva los usuarios seleccionados"""
        count = 0
        for user in queryset:
            if user.status == 'activo' and not user.es_admin:
                user.desactivar()
                count += 1
        
        self.message_user(
            request,
            f'{count} usuario(s) desactivado(s) exitosamente.'
        )
    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"
    
    def marcar_como_pendientes(self, request, queryset):
        """Marca usuarios como pendientes"""
        count = queryset.update(status='pendiente')
        self.message_user(
            request,
            f'{count} usuario(s) marcado(s) como pendientes.'
        )
    marcar_como_pendientes.short_description = "Marcar como pendientes"
    
    def get_readonly_fields(self, request, obj=None):
        """Define campos de solo lectura según el usuario"""
        readonly = list(self.readonly_fields)
        
        # Si no es superuser, algunos campos son de solo lectura
        if not request.user.is_superuser:
            readonly.extend(['is_superuser', 'user_permissions', 'groups'])
        
        return readonly


@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    """Administración del historial de conexiones"""
    
    list_display = (
        'user', 'login_time', 'logout_time', 'duracion_badge', 
        'ip_address', 'get_device_info'
    )
    
    list_filter = (
        'login_time', 'logout_time'
    )
    
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'ip_address'
    )
    
    readonly_fields = (
        'user', 'login_time', 'logout_time', 'ip_address', 
        'user_agent', 'session_key', 'duracion_sesion'
    )
    
    date_hierarchy = 'login_time'
    
    ordering = ('-login_time',)
    
    def has_add_permission(self, request):
        """No permitir agregar manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo lectura"""
        return False
    
    def duracion_badge(self, obj):
        """Muestra la duración de la sesión"""
        duracion = obj.duracion_sesion
        if duracion:
            total_seconds = int(duracion.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            if hours > 0:
                texto = f"{hours}h {minutes}m"
                color = "info"
            elif minutes > 30:
                texto = f"{minutes}m"
                color = "success"
            else:
                texto = f"{minutes}m"
                color = "warning"
            
            return format_html(
                '<span class="badge badge-{}">{}</span>',
                color, texto
            )
        elif obj.logout_time is None:
            return format_html(
                '<span class="badge badge-primary">Activa</span>'
            )
        return format_html(
            '<span class="badge badge-secondary">-</span>'
        )
    duracion_badge.short_description = 'Duración'
    
    def get_device_info(self, obj):
        """Extrae información del dispositivo del user agent"""
        if obj.user_agent:
            ua = obj.user_agent.lower()
            if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
                return format_html(
                    '<i class="fas fa-mobile-alt" title="Móvil"></i>'
                )
            elif 'tablet' in ua or 'ipad' in ua:
                return format_html(
                    '<i class="fas fa-tablet-alt" title="Tablet"></i>'
                )
            else:
                return format_html(
                    '<i class="fas fa-desktop" title="Desktop"></i>'
                )
        return '-'
    get_device_info.short_description = 'Dispositivo'
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related('user')


# Personalizar el título del admin
admin.site.site_header = "PubliTrack - Administración"
admin.site.site_title = "PubliTrack Admin"
admin.site.index_title = "Panel de Administración"