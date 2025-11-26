"""
Administración Django para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Interfaz administrativa para cuñas publicitarias y archivos de audio
INCLUYE: Administración de Plantillas y Contratos Generados
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
    HistorialCuña,
    PlantillaContrato,
    ContratoGenerado
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


class ContratoGeneradoInline(admin.TabularInline):
    """Inline para mostrar contratos generados en cuñas"""
    model = ContratoGenerado
    extra = 0
    readonly_fields = ('numero_contrato', 'estado', 'valor_total', 'fecha_generacion', 'ver_contrato')
    fields = ('numero_contrato', 'estado', 'valor_total', 'fecha_generacion', 'ver_contrato')
    can_delete = False
    
    def ver_contrato(self, obj):
        if obj.pk:
            url = reverse('admin:content_management_contratogenerado_change', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Ver Detalle</a>', url)
        return '-'
    ver_contrato.short_description = 'Acciones'
    
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
        'dias_restantes_display',
        'total_contratos'
    ]
    
    list_filter = [
        'estado',
        'prioridad',
        'categoria',
        'tipo_contrato',
        'vendedor_asignado',
        'requiere_aprobacion',
        'excluir_sabados',
        'excluir_domingos',
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
        'cliente__empresa',
        'cliente__ruc_dni',
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
        'dias_efectivos',
        'emisiones_totales_reales',
        'reproducciones_totales',
        'costo_por_reproduccion',
        'costo_por_emision_real',
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
                'excluir_sabados',
                'excluir_domingos',
                'duracion_total_dias',
                'dias_efectivos',
                'reproducciones_totales',
                'emisiones_totales_reales',
                'costo_por_reproduccion',
                'costo_por_emision_real'
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
    
    inlines = [ContratoGeneradoInline, HistorialCuñaInline]
    
    actions = [
        'aprobar_cuñas_seleccionadas',
        'activar_cuñas_seleccionadas',
        'pausar_cuñas_seleccionadas',
        'finalizar_cuñas_seleccionadas'
    ]
    
    def cliente_info(self, obj):
        if obj.cliente:
            info = obj.cliente.empresa if hasattr(obj.cliente, 'empresa') and obj.cliente.empresa else obj.cliente.get_full_name()
            url = reverse('admin:authentication_customuser_change', args=[obj.cliente.pk])
            return format_html('<a href="{}">{}</a>', url, info)
        return '-'
    cliente_info.short_description = 'Cliente'
    
    def vendedor_info(self, obj):
        if obj.vendedor_asignado:
            url = reverse('admin:authentication_customuser_change', args=[obj.vendedor_asignado.pk])
            return format_html('<a href="{}">{}</a>', url, obj.vendedor_asignado.get_full_name())
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
    
    def total_contratos(self, obj):
        """Muestra el total de contratos generados"""
        count = obj.contratos.count()
        if count > 0:
            url = reverse('admin:content_management_contratogenerado_changelist')
            return format_html(
                '<a href="{}?cuña__id__exact={}">{}</a>',
                url, obj.pk, count
            )
        return '0'
    total_contratos.short_description = 'Contratos'
    
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


# ==================== PLANTILLAS DE CONTRATO ====================

@admin.register(PlantillaContrato)
class PlantillaContratoAdmin(admin.ModelAdmin):
    """Administración de plantillas de contrato"""
    
    list_display = [
        'nombre',
        'tipo_contrato',
        'version',
        'incluye_iva_badge',
        'porcentaje_iva',
        'is_default_badge',
        'is_active',
        'total_contratos_generados',
        'created_at'
    ]
    
    list_filter = [
        'tipo_contrato',
        'incluye_iva',
        'is_active',
        'is_default',
        'created_at'
    ]
    
    search_fields = [
        'nombre',
        'descripcion',
        'version',
        'instrucciones'
    ]
    
    readonly_fields = [
        'variables_disponibles',
        'created_at',
        'updated_at'
    ]
    
    ordering = ['-is_default', '-is_active', '-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'nombre',
                'tipo_contrato',
                'version',
                'descripcion',
                'is_active',
                'is_default'
            )
        }),
        ('Archivo de Plantilla', {
            'fields': (
                'archivo_plantilla',
                'instrucciones'
            ),
            'description': 'Suba un archivo Word (.docx) con variables en formato {{VARIABLE}}'
        }),
        ('Configuración de IVA', {
            'fields': (
                'incluye_iva',
                'porcentaje_iva'
            )
        }),
        ('Variables Disponibles', {
            'fields': ('variables_disponibles',),
            'classes': ('collapse',),
            'description': 'Variables que se pueden usar en la plantilla'
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'marcar_como_predeterminada',
        'activar_plantillas',
        'desactivar_plantillas'
    ]
    
    def incluye_iva_badge(self, obj):
        """Badge para indicar si incluye IVA"""
        if obj.incluye_iva:
            return format_html(
                '<span class="badge bg-success">✓ Sí</span>'
            )
        return format_html(
            '<span class="badge bg-secondary">✗ No</span>'
        )
    incluye_iva_badge.short_description = 'IVA'
    
    def is_default_badge(self, obj):
        """Badge para plantilla predeterminada"""
        if obj.is_default:
            return format_html(
                '<span class="badge bg-primary">★ Predeterminada</span>'
            )
        return '-'
    is_default_badge.short_description = 'Estado'
    
    def total_contratos_generados(self, obj):
        """Muestra el total de contratos generados con esta plantilla"""
        count = obj.contratos_generados.count()
        if count > 0:
            url = reverse('admin:content_management_contratogenerado_changelist')
            return format_html(
                '<a href="{}?plantilla_usada__id__exact={}">{} contratos</a>',
                url, obj.pk, count
            )
        return '0 contratos'
    total_contratos_generados.short_description = 'Contratos Generados'
    
    # ==================== ACCIONES MASIVAS ====================
    
    def marcar_como_predeterminada(self, request, queryset):
        """Marcar una plantilla como predeterminada"""
        if queryset.count() > 1:
            self.message_user(
                request,
                'Solo puede marcar una plantilla como predeterminada a la vez.',
                level='error'
            )
            return
        
        plantilla = queryset.first()
        
        # Desmarcar otras plantillas del mismo tipo
        PlantillaContrato.objects.filter(
            tipo_contrato=plantilla.tipo_contrato,
            is_default=True
        ).update(is_default=False)
        
        plantilla.is_default = True
        plantilla.save()
        
        self.message_user(
            request,
            f'Plantilla "{plantilla.nombre}" marcada como predeterminada.'
        )
    marcar_como_predeterminada.short_description = "Marcar como predeterminada"
    
    def activar_plantillas(self, request, queryset):
        """Activar plantillas seleccionadas"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{count} plantillas activadas exitosamente.'
        )
    activar_plantillas.short_description = "Activar plantillas seleccionadas"
    
    def desactivar_plantillas(self, request, queryset):
        """Desactivar plantillas seleccionadas"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{count} plantillas desactivadas exitosamente.'
        )
    desactivar_plantillas.short_description = "Desactivar plantillas seleccionadas"
    
    def has_delete_permission(self, request, obj=None):
        """Prevenir eliminación si la plantilla tiene contratos generados"""
        if obj and obj.contratos_generados.exists():
            return False
        return super().has_delete_permission(request, obj)


# ==================== CONTRATOS GENERADOS ====================

@admin.register(ContratoGenerado)
class ContratoGeneradoAdmin(admin.ModelAdmin):
    """Administración de contratos generados - VERSIÓN MEJORADA"""
    
    list_display = [
        'numero_contrato',
        'nombre_cliente',
        'vendedor_info',  # ✅ NUEVO CAMPO
        'ruc_dni_cliente',
        'cuña_link',
        'estado_badge',
        'valor_sin_iva',
        'valor_iva',
        'valor_total',
        'fecha_generacion',
        'fecha_firma',
        'acciones_rapidas'
    ]
    
    list_filter = [
        'estado',
        'vendedor_asignado',  # ✅ NUEVO FILTRO
        'fecha_generacion',
        'fecha_envio',
        'fecha_firma',
        'plantilla_usada',
        'generado_por'
    ]
    
    search_fields = [
        'numero_contrato',
        'nombre_cliente',
        'ruc_dni_cliente',
        'vendedor_asignado__username',  # ✅ NUEVO CAMPO DE BÚSQUEDA
        'vendedor_asignado__first_name',
        'vendedor_asignado__last_name',
        'cuña__codigo',
        'cuña__titulo',
        'cliente__username',
        'cliente__empresa',
        'cliente__ruc_dni'
    ]
    
    readonly_fields = [
        'numero_contrato',
        'vendedor_asignado',  # ✅ HACERLO SOLO LECTURA
        'cuña',
        'plantilla_usada',
        'cliente',
        'nombre_cliente',
        'ruc_dni_cliente',
        'valor_sin_iva',
        'valor_iva',
        'valor_total',
        'datos_generacion',
        'fecha_generacion',
        'generado_por',
        'created_at',
        'updated_at',
        'descargar_archivo',
    ]
    
    ordering = ['-fecha_generacion']
    date_hierarchy = 'fecha_generacion'
    
    fieldsets = (
        ('Información del Contrato', {
            'fields': (
                'numero_contrato',
                'estado',
                'cuña',
                'plantilla_usada'
            )
        }),
        ('Información del Cliente', {
            'fields': (
                'cliente',
                'nombre_cliente',
                'ruc_dni_cliente'
            )
        }),
        ('Valores del Contrato', {
            'fields': (
                'valor_sin_iva',
                'valor_iva',
                'valor_total'
            )
        }),
        ('Archivos Generados', {
            'fields': (
                'archivo_contrato',
                'archivo_contrato_pdf',
                'descargar_archivo'
            )
        }),
        ('Fechas y Estados', {
            'fields': (
                'fecha_generacion',
                'fecha_envio',
                'fecha_firma'
            )
        }),
        ('Datos de Generación', {
            'fields': ('datos_generacion',),
            'classes': ('collapse',),
            'description': 'Datos utilizados para generar el contrato'
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Metadatos', {
            'fields': (
                'generado_por',
                'created_at',
                'updated_at',
                'puede_regenerar'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'marcar_como_enviado',
        'marcar_como_firmado',
        'activar_contratos',
        'regenerar_contratos'
    ]
    
    def cuña_link(self, obj):
        """Enlace a la cuña asociada"""
        if obj.cuña:
            url = reverse('admin:content_management_cuñapublicitaria_change', args=[obj.cuña.pk])
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url,
                obj.cuña.codigo
            )
        return '-'
    cuña_link.short_description = 'Cuña'
    
    def estado_badge(self, obj):
        """Badge visual para el estado"""
        colors = {
            'borrador': 'secondary',
            'generado': 'info',
            'enviado': 'warning',
            'firmado': 'primary',
            'activo': 'success',
            'vencido': 'danger',
            'cancelado': 'dark'
        }
        color = colors.get(obj.estado, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def descargar_archivo(self, obj):
        """Enlace para descargar el contrato"""
        if obj.archivo_contrato:
            return format_html(
                '<a href="{}" class="button" target="_blank">📄 Descargar DOCX</a>',
                obj.archivo_contrato.url
            )
        return 'No generado'
    descargar_archivo.short_description = 'Descargar'
    
    def acciones_rapidas(self, obj):
        """Botones de acciones rápidas"""
        acciones = []
        
        if obj.estado == 'generado':
            acciones.append('<span style="color: #28a745;">✓ Listo</span>')
        elif obj.estado == 'enviado':
            acciones.append('<span style="color: #ffc107;">📧 Enviado</span>')
        elif obj.estado == 'firmado':
            acciones.append('<span style="color: #0d6efd;">✍ Firmado</span>')
        elif obj.estado == 'activo':
            acciones.append('<span style="color: #28a745;">🟢 Activo</span>')
        
        return format_html(' '.join(acciones)) if acciones else '-'
    acciones_rapidas.short_description = 'Estado'
    def vendedor_info(self, obj):
        """Información del vendedor asignado"""
        if obj.vendedor_asignado:
            url = reverse('admin:authentication_customuser_change', args=[obj.vendedor_asignado.pk])
            return format_html('<a href="{}">{}</a>', url, obj.vendedor_asignado.get_full_name())
        return format_html('<span style="color: #6c757d;">No asignado</span>')
    vendedor_info.short_description = 'Vendedor'
    # ==================== ACCIONES MASIVAS ====================
    
    def marcar_como_enviado(self, request, queryset):
        """Marcar contratos como enviados"""
        count = 0
        for contrato in queryset.filter(estado='generado'):
            contrato.marcar_como_enviado()
            count += 1
        
        self.message_user(
            request,
            f'{count} contratos marcados como enviados.'
        )
    marcar_como_enviado.short_description = "Marcar como enviado"
    
    def marcar_como_firmado(self, request, queryset):
        """Marcar contratos como firmados"""
        count = 0
        for contrato in queryset.filter(estado='enviado'):
            contrato.marcar_como_firmado()
            count += 1
        
        self.message_user(
            request,
            f'{count} contratos marcados como firmados.'
        )
    marcar_como_firmado.short_description = "Marcar como firmado"
    
    def activar_contratos(self, request, queryset):
        """Activar contratos"""
        count = 0
        for contrato in queryset.filter(estado='firmado'):
            contrato.activar_contrato()
            count += 1
        
        self.message_user(
            request,
            f'{count} contratos activados.'
        )
    activar_contratos.short_description = "Activar contratos"
    
    def regenerar_contratos(self, request, queryset):
        """Regenerar archivos de contratos"""
        count = 0
        errores = 0
        
        for contrato in queryset:
            if contrato.puede_regenerar:
                if contrato.generar_contrato():
                    count += 1
                else:
                    errores += 1
        
        if count > 0:
            self.message_user(
                request,
                f'{count} contratos regenerados exitosamente.'
            )
        
        if errores > 0:
            self.message_user(
                request,
                f'{errores} contratos no pudieron ser regenerados.',
                level='warning'
            )
    regenerar_contratos.short_description = "Regenerar archivos de contrato"
    
    def get_queryset(self, request):
        """Optimizar queryset con select_related"""
        return super().get_queryset(request).select_related(
            'cuña',
            'cliente',
            'plantilla_usada',
            'generado_por'
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
                reverse('admin:authentication_customuser_change', args=[obj.usuario.pk]),
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
            'contratos_activos': ContratoGenerado.objects.filter(estado='activo').count(),
            'contratos_pendientes': ContratoGenerado.objects.filter(estado='generado').count(),
            'plantillas_activas': PlantillaContrato.objects.filter(is_active=True).count(),
        })
        
        return super().index(request, extra_context)

# Registrar el sitio personalizado si se desea usar
# admin_site = PubliTrackAdminSite(name='publi_admin')