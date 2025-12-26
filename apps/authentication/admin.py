from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CustomUser, UserLoginHistory, Role, Permission, RolePermission

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Administración personalizada para CustomUser"""
    
    # Campos que se muestran en la lista
    list_display = (
        'username', 'get_full_name', 'email', 'rol', 'status_badge', 
        'empresa', 'cargo_empresa', 'profesion', 'vendedor_asignado', 'ultima_conexion', 'created_at'
    )
    
    # Filtros laterales
    list_filter = (
        'rol', 'status', 'is_active', 'is_staff', 'created_at', 'ultima_conexion',
        'cargo_empresa', 'profesion'
    )
    
    # Campos de búsqueda
    search_fields = (
        'username', 'first_name', 'last_name', 'email', 
        'empresa', 'ruc_dni', 'telefono', 'cargo_empresa', 'profesion'
    )
    
    # Campos para ordenar
    ordering = ('-created_at',)
    
    # Campos de solo lectura
    readonly_fields = (
        'created_at', 'updated_at', 'fecha_registro', 'ultima_conexion',
        'date_joined', 'last_login'
    )
    
    # Configuración de fieldsets para el formulario
    fieldsets = (
        ('Información Básica', {
            'fields': ('username', 'password', 'first_name', 'last_name', 'email')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'direccion', 'ciudad', 'provincia', 'direccion_exacta')
        }),
        ('Rol y Estado', {
            'fields': ('rol', 'status', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Información de Cliente', {
            'fields': ('empresa', 'cargo_empresa', 'profesion', 'ruc_dni', 'razon_social', 'giro_comercial', 
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
    
    # Fieldsets para agregar usuario nuevo
    add_fieldsets = (
        ('Información Básica', {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 
                      'password1', 'password2'),
        }),
        ('Rol y Estado', {
            'fields': ('rol', 'status'),
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'direccion'),
            'classes': ('collapse',),
        }),
        ('Información de Cliente/Empresa', {
            'fields': ('empresa', 'cargo_empresa', 'profesion', 'ruc_dni', 'razon_social', 'giro_comercial', 'vendedor_asignado'),
            'classes': ('collapse',),
            'description': 'REQUERIDO para clientes: Al menos empresa o RUC/DNI debe ser completado'
        }),
        ('Información de Vendedor', {
            'fields': ('comision_porcentaje', 'meta_mensual', 'supervisor'),
            'classes': ('collapse',),
            'description': 'Solo completar para vendedores'
        }),
    )
    
    actions = ['activar_usuarios', 'desactivar_usuarios', 'marcar_como_pendientes']
    
    def get_full_name(self, obj):
        return obj.nombre_completo
    get_full_name.short_description = 'Nombre Completo'
    
    def status_badge(self, obj):
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
        return super().get_queryset(request).select_related(
            'vendedor_asignado', 'supervisor'
        )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "vendedor_asignado":
            kwargs["queryset"] = CustomUser.objects.filter(rol='vendedor', status='activo')
        elif db_field.name == "supervisor":
            kwargs["queryset"] = CustomUser.objects.filter(rol='admin', status='activo')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        if obj.rol == 'cliente':
            if not obj.empresa and not obj.ruc_dni:
                from django.core.exceptions import ValidationError
                raise ValidationError('Los clientes deben tener al menos empresa o RUC/DNI.')
        super().save_model(request, obj, form, change)
    
    # Acciones personalizadas
    def activar_usuarios(self, request, queryset):
        count = 0
        for user in queryset:
            if user.status != 'activo':
                user.activar()
                count += 1
        self.message_user(request, f'{count} usuario(s) activado(s) exitosamente.')
    activar_usuarios.short_description = "Activar usuarios seleccionados"
    
    def desactivar_usuarios(self, request, queryset):
        count = 0
        for user in queryset:
            if user.status == 'activo' and not user.es_admin:
                user.desactivar()
                count += 1
        self.message_user(request, f'{count} usuario(s) desactivado(s) exitosamente.')
    desactivar_usuarios.short_description = "Desactivar usuarios seleccionados"
    
    def marcar_como_pendientes(self, request, queryset):
        count = queryset.update(status='pendiente')
        self.message_user(request, f'{count} usuario(s) marcado(s) como pendientes.')
    marcar_como_pendientes.short_description = "Marcar como pendientes"

@admin.register(UserLoginHistory)
class UserLoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time', 'duracion_badge', 'ip_address', 'get_device_info')
    list_filter = ('login_time', 'logout_time')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'login_time', 'logout_time', 'ip_address', 'user_agent', 'session_key', 'duracion_sesion')
    date_hierarchy = 'login_time'
    
    def duracion_badge(self, obj):
        duracion = obj.duracion_sesion
        if duracion:
            total_seconds = int(duracion.total_seconds())
            minutes = (total_seconds % 3600) // 60
            return format_html('<span class="badge badge-info">{}m</span>', minutes)
        return "-"
    duracion_badge.short_description = 'Duración'

    def get_device_info(self, obj):
        return "Desktop" # Simplificado para el ejemplo
    
    def has_add_permission(self, request): return False

# --- REGISTRO DE MODELOS DE ROLES Y PERMISOS ---
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'module', 'action', 'is_active')
    list_filter = ('module', 'action', 'is_active')
    search_fields = ('name', 'codename')

class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'is_system_role', 'is_active')
    list_filter = ('is_system_role', 'is_active')
    search_fields = ('name', 'codename')
    inlines = [RolePermissionInline]

# Configuración del sitio
admin.site.site_header = "PubliTrack - Administración"
admin.site.site_title = "PubliTrack Admin"
admin.site.index_title = "Panel de Administración"