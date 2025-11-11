from django.contrib import admin
from django.utils.html import format_html
from .models import ParteMortorio, HistorialParteMortorio

@admin.register(ParteMortorio)
class ParteMortorioAdmin(admin.ModelAdmin):
    # Campos a mostrar en la lista - ACTUALIZADO CON TODOS LOS CAMPOS NUEVOS
    list_display = [
        'codigo', 
        'nombre_fallecido',
        'cliente',
        'fecha_fallecimiento',
        'nombre_esposa_display',
        'cantidad_hijos_display',
        'hijos_info_display',  # NUEVO: Info de hijos vivos/fallecidos
        'familiares_adicionales_display',  # NUEVO
        'tipo_ceremonia',
        'fecha_misa_display',  # NUEVO
        'transmision_info_display',  # NUEVO
        'estado',
        'urgencia',
        'precio_total_display',
        'fecha_solicitud'
    ]
    
    # Filtros disponibles en el sidebar - ACTUALIZADO
    list_filter = [
        'estado', 
        'urgencia', 
        'fecha_solicitud',
        'tipo_ceremonia',
        'fecha_fallecimiento',
        'fecha_inicio_transmision'
    ]
    
    # Campos de búsqueda - ACTUALIZADO
    search_fields = [
        'codigo', 
        'nombre_fallecido', 
        'dni_fallecido',
        'nombre_esposa',
        'nombres_hijos',
        'familiares_adicionales',
        'lugar_misa',
        'mensaje_personalizado',
        'cliente__username',
        'cliente__first_name', 
        'cliente__last_name'
    ]
    
    # Campos de solo lectura
    readonly_fields = [
        'codigo',
        'fecha_solicitud',
        'fecha_programacion',
        'fecha_transmision_completada',
        'precio_total',
        'created_at',
        'updated_at',
        'dias_desde_solicitud',
        'necesita_atencion',
        'dias_transmision',
        'resumen_familia'
    ]
    
    # Campos para edición rápida desde la lista
    list_editable = ['estado', 'urgencia']
    
    # Paginación
    list_per_page = 20
    
    # Ordenamiento por defecto
    ordering = ['-fecha_solicitud']
    
    # Agrupar campos en el formulario de edición - CON TODOS LOS CAMPOS
    fieldsets = (
        ('INFORMACIÓN BÁSICA', {
            'fields': (
                'codigo',
                'cliente',
                'fecha_solicitud',
                'estado',
                'urgencia',
                'creado_por'
            )
        }),
        ('INFORMACIÓN DEL FALLECIDO', {
            'fields': (
                'nombre_fallecido',
                'dni_fallecido',
                'fecha_nacimiento',
                'fecha_fallecimiento',
            )
        }),
        ('INFORMACIÓN FAMILIAR', {
            'fields': (
                'nombre_esposa',
                'cantidad_hijos',
                'hijos_vivos',
                'hijos_fallecidos',
                'nombres_hijos',
                'familiares_adicionales',
                'resumen_familia'
            )
        }),
        ('INFORMACIÓN DE LA CEREMONIA', {
            'fields': (
                'tipo_ceremonia',
                'fecha_misa',
                'hora_misa',
                'lugar_misa',
            )
        }),
        ('INFORMACIÓN DE TRANSMISIÓN', {
            'fields': (
                'fecha_inicio_transmision',
                'fecha_fin_transmision',
                'hora_transmision',
                'duracion_transmision',
                'repeticiones_dia',
                'precio_total',
            )
        }),
        ('OBSERVACIONES Y MENSAJES', {
            'fields': (
                'mensaje_personalizado',
                'observaciones',
            )
        }),
        ('INFORMACIÓN DEL SISTEMA', {
            'fields': (
                'necesita_atencion',
                'dias_desde_solicitud',
                'dias_transmision',
                'fecha_programacion',
                'fecha_transmision_completada',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    # ========== MÉTODOS PERSONALIZADOS PARA LA LISTA ==========
    
    def precio_total_display(self, obj):
        return f"${obj.precio_total:.2f}"
    precio_total_display.short_description = 'Precio Total'
    
    def nombre_esposa_display(self, obj):
        return obj.nombre_esposa if obj.nombre_esposa else "—"
    nombre_esposa_display.short_description = 'Esposa/Esposo'
    
    def cantidad_hijos_display(self, obj):
        return obj.cantidad_hijos if obj.cantidad_hijos > 0 else "0"
    cantidad_hijos_display.short_description = 'Hijos'
    
    def hijos_info_display(self, obj):
        if obj.cantidad_hijos > 0:
            return f"V:{obj.hijos_vivos} F:{obj.hijos_fallecidos}"
        return "—"
    hijos_info_display.short_description = 'Hijos V/F'
    
    def familiares_adicionales_display(self, obj):
        if obj.familiares_adicionales:
            # Mostrar solo los primeros 30 caracteres
            if len(obj.familiares_adicionales) > 30:
                return obj.familiares_adicionales[:30] + '...'
            return obj.familiares_adicionales
        return "—"
    familiares_adicionales_display.short_description = 'Familiares Adicionales'
    
    def fecha_misa_display(self, obj):
        if obj.fecha_misa:
            return obj.fecha_misa.strftime('%d/%m/%Y')
        return "—"
    fecha_misa_display.short_description = 'Fecha Misa'
    
    def transmision_info_display(self, obj):
        if obj.fecha_inicio_transmision:
            return f"{obj.duracion_transmision}min × {obj.repeticiones_dia}/día"
        return "No prog."
    transmision_info_display.short_description = 'Transmisión'
    
    def nombres_hijos_display(self, obj):
        if obj.nombres_hijos:
            if len(obj.nombres_hijos) > 50:
                return obj.nombres_hijos[:50] + '...'
            return obj.nombres_hijos
        return "—"
    nombres_hijos_display.short_description = 'Nombres Hijos'

    # Autocompletar el campo 'creado_por' con el usuario actual
    def save_model(self, request, obj, form, change):
        if not obj.creado_por:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    # Mostrar información adicional en la lista
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'creado_por')

@admin.register(HistorialParteMortorio)
class HistorialParteMortorioAdmin(admin.ModelAdmin):
    list_display = [
        'parte_mortorio', 
        'accion', 
        'usuario', 
        'fecha',
        'descripcion_corta'
    ]
    
    list_filter = [
        'accion', 
        'fecha',
        'usuario'
    ]
    
    search_fields = [
        'parte_mortorio__codigo',
        'parte_mortorio__nombre_fallecido',
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'descripcion'
    ]
    
    readonly_fields = [
        'parte_mortorio',
        'accion',
        'usuario',
        'descripcion',
        'datos_anteriores',
        'datos_nuevos',
        'fecha'
    ]
    
    list_per_page = 20
    ordering = ['-fecha']
    
    def descripcion_corta(self, obj):
        if obj.descripcion and len(obj.descripcion) > 50:
            return obj.descripcion[:50] + '...'
        return obj.descripcion or '—'
    descripcion_corta.short_description = 'Descripción'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# Acciones personalizadas
def marcar_como_programado(modeladmin, request, queryset):
    for parte in queryset:
        parte.programar(request.user)
    modeladmin.message_user(request, f"{queryset.count()} partes mortorios programados exitosamente")
marcar_como_programado.short_description = "Marcar como programado"

def marcar_como_transmitido(modeladmin, request, queryset):
    for parte in queryset:
        parte.marcar_transmitido(request.user)
    modeladmin.message_user(request, f"{queryset.count()} partes mortorios marcados como transmitidos")
marcar_como_transmitido.short_description = "Marcar como transmitido"

def marcar_como_cancelado(modeladmin, request, queryset):
    for parte in queryset:
        parte.cancelar(request.user)
    modeladmin.message_user(request, f"{queryset.count()} partes mortorios cancelados")
marcar_como_cancelado.short_description = "Cancelar partes mortorios"

# Agregar las acciones al admin
ParteMortorioAdmin.actions = [
    marcar_como_programado,
    marcar_como_transmitido,
    marcar_como_cancelado
]