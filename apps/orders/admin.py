"""
Configuración del Admin para el módulo de Órdenes
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import OrdenToma, HistorialOrden


@admin.register(OrdenToma)
class OrdenTomaAdmin(admin.ModelAdmin):
    """
    Administración de Órdenes de Toma en Django Admin
    """
    
    list_display = [
        'codigo',
        'nombre_cliente_display',
        'empresa_display',
        'total_display',
        'estado_badge',
        'prioridad_badge',
        'vendedor_display',
        'dias_desde_creacion',
        'fecha_orden',
    ]
    
    list_filter = [
        'estado',
        'prioridad',
        'vendedor_asignado',
        'created_at',
        'fecha_validacion',
    ]
    
    search_fields = [
        'codigo',
        'nombre_cliente',
        'ruc_dni_cliente',
        'empresa_cliente',
        'email_cliente',
        'detalle_productos',
    ]
    
    readonly_fields = [
        'codigo',
        'created_at',
        'updated_at',
        'fecha_validacion',
        'fecha_completado',
        'validado_por',
        'completado_por',
        'created_by',
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'codigo',
                'cliente',
                'estado',
                'prioridad',
            )
        }),
        ('Datos del Cliente', {
            'fields': (
                'nombre_cliente',
                'ruc_dni_cliente',
                'empresa_cliente',
                'ciudad_cliente',
                'direccion_cliente',
                'telefono_cliente',
                'email_cliente',
            ),
            'classes': ('collapse',),
        }),
        ('Detalles de la Orden', {
            'fields': (
                'detalle_productos',
                'cantidad',
                'total',
                'observaciones',
            )
        }),
        ('Gestión Comercial', {
            'fields': (
                'vendedor_asignado',
                'validado_por',
                'completado_por',
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_orden',
                'fecha_validacion',
                'fecha_completado',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
            ),
            'classes': ('collapse',),
        }),
    )
    
    def nombre_cliente_display(self, obj):
        """Muestra el nombre del cliente con enlace"""
        if obj.cliente:
            url = reverse('admin:authentication_customuser_change', args=[obj.cliente.pk])
            return format_html('<a href="{}">{}</a>', url, obj.nombre_cliente)
        return obj.nombre_cliente
    nombre_cliente_display.short_description = 'Cliente'
    
    def empresa_display(self, obj):
        """Muestra la empresa"""
        return obj.empresa_cliente or '-'
    empresa_display.short_description = 'Empresa'
    
    def total_display(self, obj):
        """Muestra el total formateado"""
        return format_html('<strong>S/ {}</strong>', obj.total)
    total_display.short_description = 'Total'
    
    def estado_badge(self, obj):
        """Muestra el estado como badge con color"""
        colors = {
            'generado': '#ffc107',
            'validado': '#17a2b8',
            'en_produccion': '#007bff',
            'completado': '#28a745',
            'cancelado': '#dc3545',
        }
        color = colors.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def prioridad_badge(self, obj):
        """Muestra la prioridad como badge con color"""
        colors = {
            'baja': '#28a745',
            'normal': '#17a2b8',
            'alta': '#ffc107',
            'urgente': '#dc3545',
        }
        color = colors.get(obj.prioridad, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_prioridad_display()
        )
    prioridad_badge.short_description = 'Prioridad'
    
    def vendedor_display(self, obj):
        """Muestra el vendedor asignado"""
        if obj.vendedor_asignado:
            return obj.vendedor_asignado.get_full_name()
        return format_html('<span style="color: #999;">Sin asignar</span>')
    vendedor_display.short_description = 'Vendedor'
    
    def save_model(self, request, obj, form, change):
        """Override save_model para registrar usuario creador"""
        if not change:  # Si es nuevo
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HistorialOrden)
class HistorialOrdenAdmin(admin.ModelAdmin):
    """
    Administración del Historial de Órdenes
    """
    
    list_display = [
        'orden_display',
        'accion_display',
        'usuario_display',
        'fecha',
        'descripcion_corta',
    ]
    
    list_filter = [
        'accion',
        'fecha',
        'usuario',
    ]
    
    search_fields = [
        'orden__codigo',
        'descripcion',
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
    ]
    
    readonly_fields = [
        'orden',
        'accion',
        'usuario',
        'descripcion',
        'datos_anteriores',
        'datos_nuevos',
        'fecha',
    ]
    
    def has_add_permission(self, request):
        """No permitir crear registros de historial manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar registros de historial"""
        return False
    
    def orden_display(self, obj):
        """Muestra la orden con enlace"""
        if obj.orden:
            url = reverse('admin:orders_ordentoma_change', args=[obj.orden.pk])
            return format_html('<a href="{}">{}</a>', url, obj.orden.codigo)
        return '-'
    orden_display.short_description = 'Orden'
    
    def accion_display(self, obj):
        """Muestra la acción con color"""
        colors = {
            'creada': '#28a745',
            'editada': '#17a2b8',
            'validada': '#007bff',
            'produccion': '#ffc107',
            'completada': '#28a745',
            'cancelada': '#dc3545',
        }
        color = colors.get(obj.accion, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_accion_display()
        )
    accion_display.short_description = 'Acción'
    
    def usuario_display(self, obj):
        """Muestra el usuario"""
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '-'
    usuario_display.short_description = 'Usuario'
    
    def descripcion_corta(self, obj):
        """Muestra descripción truncada"""
        if len(obj.descripcion) > 60:
            return obj.descripcion[:60] + '...'
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'
