"""
Administración Django para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Interfaz administrativa para cuñas publicitarias y archivos de audio
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from .models import (
    CategoriaPublicitaria,
    TipoContrato,
    ArchivoAudio,
    CuñaPublicitaria,
    HistorialCuña
)

# ==================== CONFIGURACIÓN GENERAL ====================

admin.site.site_header = "PubliTrack - Administración"
admin.site.site_title = "PubliTrack Admin"
admin.site.index_title = "Panel de Administración PubliTrack"

# ==================== ADMIN INLINES ====================

class HistorialCuñaInline(admin.TabularInline):
    """Inline para mostrar historial en cuñas"""
    model = HistorialCuña
    extra = 0
    readonly_fields = ('accion', 'usuario', 'descripcion', 'fecha')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False

# ==================== CATEGORIAS PUBLICITARIAS ====================

@admin.register(CategoriaPublicitaria)
class CategoriaPublicitariaAdmin(admin.ModelAdmin):
    """Administración de categorías publicitarias"""
    
    list_display = [
        'nombre', 
        'color_preview', 
        'tarifa_base', 
        'total_cuñas', 
        'ingresos_totales',
        'is_active', 
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'is_active')
        }),
        ('Configuración Visual', {
            'fields': ('color_codigo',)
        }),
        ('Configuración Comercial', {
            'fields': ('tarifa_base',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def color_preview(self, obj):
        """Muestra preview del color"""
        if obj.color_codigo:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
                obj.color_codigo
            )
        return '-'
    color_preview.short_description = 'Color'
    
    def total_cuñas(self, obj):
        """Cuenta total de cuñas por categoría"""
        count = obj.cuñas.count()
        if count > 0:
            url = reverse('admin:content_management_cuñapublicitaria_changelist')
            return format_html(
                '<a href="{}?categoria__id__exact={}">{} cuñas</a>',
                url, obj.pk, count
            )
        return '0 cuñas'
    total_cuñas.short_description = 'Total Cuñas'
    
    def ingresos_totales(self, obj):
        """Calcula ingresos totales por categoría"""
        total = obj.cuñas.aggregate(total=Sum('precio_total'))['total'] or 0
        return f'${total:,.2f}'
    ingresos_totales.short_description = 'Ingresos Totales'

# ==================== TIPOS DE CONTRATO ====================

@admin.register(TipoContrato)
class TipoContratoAdmin(admin.ModelAdmin):
    """Administración de tipos de contrato"""
    
    list_display = [
        'nombre',
        'duracion_tipo',
        'duracion_dias',
        'repeticiones_minimas',
        'descuento_porcentaje',
        'total_cuñas_activas',
        'is_active'
    ]
    list_filter = ['duracion_tipo', 'is_active', 'created_at']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'is_active')
        }),
        ('Configuración de Duración', {
            'fields': ('duracion_tipo', 'duracion_dias')
        }),
        ('Configuración Comercial', {
            'fields': ('repeticiones_minimas', 'descuento_porcentaje')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_cuñas_activas(self, obj):
        """Cuenta cuñas activas con este tipo de contrato"""
        count = obj.cuñas.filter(estado='activa').count()
        if count > 0:
            url = reverse('admin:content_management_cuñapublicitaria_changelist')
            return format_html(
                '<a href="{}?tipo_contrato__id__exact={}&estado__exact=activa">{} activas</a>',
                url, obj.pk, count
            )
        return '0 activas'
    total_cuñas_activas.short_description = 'Cuñas Activas'

# ==================== ARCHIVOS DE AUDIO ====================

@admin.register(ArchivoAudio)
class ArchivoAudioAdmin(admin.ModelAdmin):
    """Administración de archivos de audio"""
    
    list_display = [
        'nombre_original',
        'formato',
        'duracion_formateada',
        'tamaño_formateado',
        'calidad',
        'cuñas_asociadas',
        'subido_por',
        'fecha_subida'
    ]
    list_filter = [
        'formato',
        'calidad',
        'fecha_subida',
        'subido_por'
    ]
    search_fields = [
        'nombre_original',
        'subido_por__username',
        'subido_por__first_name',
        'subido_por__last_name'
    ]
    readonly_fields = [
        'nombre_original',
        'formato',
        'duracion_segundos',
        'tamaño_bytes',
        'bitrate',
        'sample_rate',
        'canales',
        'calidad',
        'hash_archivo',
        'metadatos_extra',
        'fecha_subida'
    ]
    ordering = ['-fecha_subida']
    
    fieldsets = (
        ('Archivo', {
            'fields': ('archivo', 'nombre_original')
        }),
        ('Metadatos Técnicos', {
            'fields': (
                'formato',
                'duracion_segundos',
                'tamaño_bytes',
                'bitrate',
                'sample_rate',
                'canales',
                'calidad'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos Adicionales', {
            'fields': ('metadatos_extra', 'hash_archivo'),
            'classes': ('collapse',)
        }),
        ('Información de Subida', {
            'fields': ('subido_por', 'fecha_subida')
        }),
    )
    
    def cuñas_asociadas(self, obj):
        """Muestra cuñas que usan este archivo"""
        count = obj.cuñas.count()
        if count > 0:
            url = reverse('admin:content_management_cuñapublicitaria_changelist')
            return format_html(
                '<a href="{}?archivo_audio__id__exact={}">{} cuñas</a>',
                url, obj.pk, count
            )
        return 'Sin usar'
    cuñas_asociadas.short_description = 'Cuñas'
    
    def has_delete_permission(self, request, obj=None):
        """Prevenir eliminación si el archivo está en uso"""
        if obj and obj.cuñas.exists():
            return False
        return super().has_delete_permission(request, obj)

# ==================== CUÑAS PUBLICITARIAS ====================

@admin.register(CuñaPublicitaria)
class CuñaPublicitariaAdmin(admin.ModelAdmin):
    """Administración de cuñas publicitarias"""
    
    list_display = [
        'codigo',
        'titulo',
        'cliente_info',
        'vendedor_info',
        'categoria',
        'estado_badge',
        'semaforo_indicator',
        'precio_total',
        'fecha_inicio',
        'fecha_fin',
        'dias_restantes_display'
    ]
    
    list_filter = [
        'estado',
        'prioridad',
        'categoria',
        'tipo_contrato',
        'vendedor_asignado',
        'requiere_aprobacion',
        'created_at',
        'fecha_inicio',
        'fecha_fin'
    ]
    
    search_fields = [
        'codigo',
        'titulo',
        'cliente__username',
        'cliente__first_name',
        'cliente__last_name',
        'vendedor_asignado__username',
        'vendedor_asignado__first_name',
        'vendedor_asignado__last_name'
    ]
    
    readonly_fields = [
        'codigo',
        'precio_por_segundo',
        'created_at',
        'updated_at',
        'fecha_aprobacion',
        'duracion_total_dias',
        'reproducciones_totales',
        'costo_por_reproduccion',
        'semaforo_estado'
    ]
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'codigo',
                'titulo',
                'descripcion',
                'tags'
            )
        }),
        ('Participantes', {
            'fields': (
                'cliente',
                'vendedor_asignado',
                'created_by'
            )
        }),
        ('Configuración Comercial', {
            'fields': (
                'categoria',
                'tipo_contrato',
                'precio_total',
                'precio_por_segundo',
                'repeticiones_dia'
            )
        }),
        ('Configuración Técnica', {
            'fields': (
                'archivo_audio',
                'duracion_planeada',
                'estado',
                'prioridad'
            )
        }),
        ('Período de Campaña', {
            'fields': (
                'fecha_inicio',
                'fecha_fin',
                'duracion_total_dias',
                'reproducciones_totales',
                'costo_por_reproduccion'
            )
        }),
        ('Aprobación', {
            'fields': (
                'requiere_aprobacion',
                'aprobada_por',
                'fecha_aprobacion'
            ),
            'classes': ('collapse',)
        }),
        ('Configuraciones Adicionales', {
            'fields': (
                'permite_edicion',
                'notificar_vencimiento',
                'dias_aviso_vencimiento',
                'observaciones'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos del Sistema', {
            'fields': (
                'semaforo_estado',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [HistorialCuñaInline]
    
    actions = [
        'aprobar_cuñas_seleccionadas',
        'activar_cuñas_seleccionadas',
        'pausar_cuñas_seleccionadas',
        'finalizar_cuñas_seleccionadas'
    ]
    
    def cliente_info(self, obj):
        if obj.cliente:
            return obj.cliente.empresa if hasattr(obj.cliente, 'empresa') else obj.cliente.get_full_name()
        return '-'
    cliente_info.short_description = 'Cliente'
    
    def vendedor_info(self, obj):
        if obj.vendedor_asignado:
            return obj.vendedor_asignado.get_full_name()
        return '-'
    vendedor_info.short_description = 'Vendedor'
    
    def estado_badge(self, obj):
        """Badge visual para el estado"""
        colors = {
            'borrador': 'secondary',
            'pendiente_revision': 'warning',
            'en_produccion': 'info',
            'aprobada': 'primary',
            'activa': 'success',
            'pausada': 'warning',
            'finalizada': 'dark',
            'cancelada': 'danger'
        }
        color = colors.get(obj.estado, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def semaforo_indicator(self, obj):
        """Indicador de semáforo visual"""
        colors = {
            'verde': '#28a745',
            'amarillo': '#ffc107',
            'rojo': '#dc3545',
            'gris': '#6c757d'
        }
        semaforo = obj.semaforo_estado
        color = colors.get(semaforo, '#6c757d')
        
        return format_html(
            '<div style="width: 15px; height: 15px; background-color: {}; border-radius: 50%; border: 1px solid #ccc;" title="{}"></div>',
            color,
            semaforo.title()
        )
    semaforo_indicator.short_description = 'Semáforo'
    
    def dias_restantes_display(self, obj):
        """Muestra días restantes con color"""
        dias = obj.dias_restantes
        if dias is None:
            return '-'
        
        if dias <= 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">Vencida</span>')
        elif dias <= 7:
            return format_html('<span style="color: #ffc107; font-weight: bold;">{} días</span>', dias)
        else:
            return format_html('<span style="color: #28a745;">{} días</span>', dias)
    dias_restantes_display.short_description = 'Días Restantes'
    
    # ==================== ACCIONES MASIVAS ====================
    
    def aprobar_cuñas_seleccionadas(self, request, queryset):
        """Acción para aprobar cuñas seleccionadas"""
        count = 0
        for cuña in queryset.filter(estado='pendiente_revision'):
            cuña.aprobar(request.user)
            count += 1
        
        self.message_user(
            request,
            f'{count} cuñas aprobadas exitosamente.'
        )
    aprobar_cuñas_seleccionadas.short_description = "Aprobar cuñas seleccionadas"
    
    def activar_cuñas_seleccionadas(self, request, queryset):
        """Acción para activar cuñas seleccionadas"""
        count = 0
        for cuña in queryset.filter(estado='aprobada'):
            cuña.activar()
            count += 1
        
        self.message_user(
            request,
            f'{count} cuñas activadas exitosamente.'
        )
    activar_cuñas_seleccionadas.short_description = "Activar cuñas seleccionadas"
    
    def pausar_cuñas_seleccionadas(self, request, queryset):
        """Acción para pausar cuñas seleccionadas"""
        count = 0
        for cuña in queryset.filter(estado='activa'):
            cuña.pausar()
            count += 1
        
        self.message_user(
            request,
            f'{count} cuñas pausadas exitosamente.'
        )
    pausar_cuñas_seleccionadas.short_description = "Pausar cuñas seleccionadas"
    
    def finalizar_cuñas_seleccionadas(self, request, queryset):
        """Acción para finalizar cuñas seleccionadas"""
        count = 0
        for cuña in queryset.filter(estado__in=['activa', 'pausada']):
            cuña.finalizar()
            count += 1
        
        self.message_user(
            request,
            f'{count} cuñas finalizadas exitosamente.'
        )
    finalizar_cuñas_seleccionadas.short_description = "Finalizar cuñas seleccionadas"
    
    def get_queryset(self, request):
        """Optimizar queryset con select_related"""
        return super().get_queryset(request).select_related(
            'cliente',
            'vendedor_asignado',
            'categoria',
            'tipo_contrato',
            'archivo_audio',
            'created_by',
            'aprobada_por'
        )

# ==================== HISTORIAL DE CUÑAS ====================

@admin.register(HistorialCuña)
class HistorialCuñaAdmin(admin.ModelAdmin):
    """Administración del historial de cuñas"""
    
    list_display = [
        'cuña_codigo',
        'accion_badge',
        'usuario_info',
        'descripcion_truncada',
        'fecha'
    ]
    
    list_filter = [
        'accion',
        'fecha',
        'usuario'
    ]
    
    search_fields = [
        'cuña__codigo',
        'cuña__titulo',
        'usuario__username',
        'descripcion'
    ]
    
    readonly_fields = [
        'cuña',
        'accion',
        'usuario',
        'descripcion',
        'datos_anteriores',
        'datos_nuevos',
        'fecha'
    ]
    
    ordering = ['-fecha']
    date_hierarchy = 'fecha'
    
    def has_add_permission(self, request):
        """No permitir agregar entradas manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir modificar entradas del historial"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo super usuarios pueden eliminar historial"""
        return request.user.is_superuser
    
    def cuña_codigo(self, obj):
        """Enlace al código de la cuña"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:content_management_cuñapublicitaria_change', args=[obj.cuña.pk]),
            obj.cuña.codigo
        )
    cuña_codigo.short_description = 'Cuña'
    
    def accion_badge(self, obj):
        """Badge para la acción"""
        colors = {
            'creada': 'success',
            'editada': 'info',
            'aprobada': 'primary',
            'activada': 'success',
            'pausada': 'warning',
            'finalizada': 'dark',
            'cancelada': 'danger',
            'audio_subido': 'info',
            'audio_cambiado': 'warning'
        }
        color = colors.get(obj.accion, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_accion_display()
        )
    accion_badge.short_description = 'Acción'
    
    def usuario_info(self, obj):
        """Información del usuario que realizó la acción"""
        if obj.usuario:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:auth_user_change', args=[obj.usuario.pk]),
                obj.usuario.get_full_name() or obj.usuario.username
            )
        return 'Sistema'
    usuario_info.short_description = 'Usuario'
    
    def descripcion_truncada(self, obj):
        """Descripción truncada para la lista"""
        if len(obj.descripcion) > 50:
            return f"{obj.descripcion[:50]}..."
        return obj.descripcion
    descripcion_truncada.short_description = 'Descripción'

# ==================== CONFIGURACIÓN ADICIONAL ====================

# Personalizar el admin site
class PubliTrackAdminSite(admin.AdminSite):
    """Sitio de administración personalizado"""
    
    def index(self, request, extra_context=None):
        """Dashboard personalizado"""
        extra_context = extra_context or {}
        
        # Estadísticas rápidas
        hoy = timezone.now().date()
        hace_semana = hoy - timedelta(days=7)
        hace_mes = hoy - timedelta(days=30)
        
        extra_context.update({
            'cuñas_activas': CuñaPublicitaria.objects.filter(estado='activa').count(),
            'cuñas_pendientes': CuñaPublicitaria.objects.filter(estado='pendiente_revision').count(),
            'cuñas_por_vencer': CuñaPublicitaria.objects.filter(
                fecha_fin__lte=hoy + timedelta(days=7),
                estado='activa'
            ).count(),
            'nuevas_esta_semana': CuñaPublicitaria.objects.filter(
                created_at__date__gte=hace_semana
            ).count(),
            'ingresos_mes': CuñaPublicitaria.objects.filter(
                created_at__date__gte=hace_mes,
                estado__in=['aprobada', 'activa', 'finalizada']
            ).aggregate(total=Sum('precio_total'))['total'] or 0,
        })
        
        return super().index(request, extra_context)

# Registrar el sitio personalizado si se desea usar
# admin_site = PubliTrackAdminSite(name='publi_admin')