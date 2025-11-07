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
        'ruc_dni_display',
        'total_display',
        'estado_badge',
        'prioridad_badge',
        'proyecto_campania',
        'titulo_material',
        'fecha_produccion_inicio',
        'fecha_produccion_fin',
        'hora_inicio',
        'hora_fin',
        'dias_desde_creacion',
    ]
    
    list_filter = [
        'estado',
        'prioridad',
        'vendedor_asignado',
        'fecha_produccion_inicio',
        'fecha_produccion_fin',
        'created_at',
    ]
    
    search_fields = [
        'codigo',
        'nombre_cliente',
        'ruc_dni_cliente',
        'empresa_cliente',
        'email_cliente',
        'detalle_productos',
        'proyecto_campania',
        'titulo_material',
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
            )
        }),
        ('Detalles de la Orden', {
            'fields': (
                'detalle_productos',
                'cantidad',
                'total',
                'observaciones',
            )
        }),
        ('Información de Producción (Completar Toma)', {
            'fields': (
                'proyecto_campania',
                'titulo_material',
                'descripcion_breve',
                'locaciones',
                'fecha_produccion_inicio',
                'fecha_produccion_fin',
                'hora_inicio',
                'hora_fin',
                'equipo_asignado',
                'recursos_necesarios',
                'observaciones_completado',
            ),
            'description': 'Estos campos se completan cuando se finaliza la toma'
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
    def ruc_dni_display(self, obj):
        """Muestra el RUC/DNI del cliente"""
        return obj.ruc_dni_cliente or '-'
    ruc_dni_display.short_description = 'RUC/DNI'
    def total_display(self, obj):
        """Muestra el total formateado"""
        return format_html('<strong>S/ {}</strong>', obj.total)
    total_display.short_description = 'Total'
    
    def estado_badge(self, obj):
        """Muestra el estado como badge con color"""
        colors = {
            'pendiente': '#ffc107',
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
from .models import OrdenProduccion, HistorialOrdenProduccion

@admin.register(OrdenProduccion)
class OrdenProduccionAdmin(admin.ModelAdmin):
    """
    Administración de Órdenes de Producción en Django Admin
    """
    
    list_display = [
        'codigo',
        'orden_toma_display',
        'nombre_cliente_display',
        'proyecto_campania',
        'titulo_material',
        'tipo_produccion',
        'estado_badge',
        'prioridad_badge',
        'fecha_inicio_planeada',
        'fecha_fin_planeada',
        'dias_retraso_display',
        'productor_asignado_display',
    ]
    
    list_filter = [
        'estado',
        'prioridad',
        'tipo_produccion',
        'productor_asignado',
        'fecha_inicio_planeada',
        'fecha_fin_planeada',
        'created_at',
    ]
    
    search_fields = [
        'codigo',
        'orden_toma__codigo',
        'nombre_cliente',
        'proyecto_campania',
        'titulo_material',
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
                'orden_toma',
                'estado',
                'prioridad',
                'tipo_produccion',
            )
        }),
        ('Información del Cliente', {
            'fields': (
                'nombre_cliente',
                'ruc_dni_cliente',
                'empresa_cliente',
            )
        }),
        ('Detalles de la Producción', {
            'fields': (
                'proyecto_campania',
                'titulo_material',
                'descripcion_breve',
                'especificaciones_tecnicas',
                'archivos_entregables',
            )
        }),
        ('Planificación', {
            'fields': (
                'fecha_inicio_planeada',
                'fecha_fin_planeada',
                'fecha_inicio_real',
                'fecha_fin_real',
            )
        }),
        ('Recursos y Equipo', {
            'fields': (
                'equipo_asignado',
                'recursos_necesarios',
                'productor_asignado',
            )
        }),
        ('Observaciones', {
            'fields': (
                'observaciones_produccion',
            )
        }),
        ('Gestión', {
            'fields': (
                'validado_por',
                'completado_por',
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
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
    
    def orden_toma_display(self, obj):
        """Muestra la orden de toma con enlace"""
        if obj.orden_toma:
            url = reverse('admin:orders_ordentoma_change', args=[obj.orden_toma.pk])
            return format_html('<a href="{}">{}</a>', url, obj.orden_toma.codigo)
        return '-'
    orden_toma_display.short_description = 'Orden Toma'
    
    def nombre_cliente_display(self, obj):
        """Muestra el nombre del cliente"""
        return obj.nombre_cliente or '-'
    nombre_cliente_display.short_description = 'Cliente'
    
    def estado_badge(self, obj):
        """Muestra el estado como badge con color"""
        colors = {
            'pendiente': '#ffc107',
            'en_produccion': '#007bff',
            'completado': '#28a745',
            'validado': '#17a2b8',
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
    
    def productor_asignado_display(self, obj):
        """Muestra el productor asignado"""
        if obj.productor_asignado:
            return obj.productor_asignado.get_full_name()
        return format_html('<span style="color: #999;">Sin asignar</span>')
    productor_asignado_display.short_description = 'Productor'
    
    def dias_retraso_display(self, obj):
        """Muestra días de retraso"""
        dias = obj.dias_retraso
        if dias > 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">{} días</span>', dias)
        elif dias == 0:
            return format_html('<span style="color: #28a745;">Al día</span>')
        else:
            return format_html('<span style="color: #17a2b8;">{} días</span>', abs(dias))
    dias_retraso_display.short_description = 'Retraso'
    
    def save_model(self, request, obj, form, change):
        """Override save_model para registrar usuario creador"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HistorialOrdenProduccion)
class HistorialOrdenProduccionAdmin(admin.ModelAdmin):
    """
    Administración del Historial de Órdenes de Producción
    """
    
    list_display = [
        'orden_produccion_display',
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
        'orden_produccion__codigo',
        'descripcion',
        'usuario__username',
    ]
    
    readonly_fields = [
        'orden_produccion',
        'accion',
        'usuario',
        'descripcion',
        'datos_anteriores',
        'datos_nuevos',
        'fecha',
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def orden_produccion_display(self, obj):
        """Muestra la orden de producción con enlace"""
        if obj.orden_produccion:
            url = reverse('admin:orders_ordenproduccion_change', args=[obj.orden_produccion.pk])
            return format_html('<a href="{}">{}</a>', url, obj.orden_produccion.codigo)
        return '-'
    orden_produccion_display.short_description = 'Orden Producción'
    
    def accion_display(self, obj):
        """Muestra la acción con color"""
        colors = {
            'creada': '#28a745',
            'editada': '#17a2b8',
            'iniciada': '#007bff',
            'completada': '#28a745',
            'validada': '#ffc107',
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