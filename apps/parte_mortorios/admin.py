from django.contrib import admin
from .models import ParteMortorio, HistorialParteMortorio

@admin.register(ParteMortorio)
class ParteMortorioAdmin(admin.ModelAdmin):
    # Campos a mostrar en la lista
    list_display = [
        'codigo', 
        'nombre_fallecido',
        'edad_fallecido',
        'cliente',
        'fecha_fallecimiento',
        'nombre_esposa',
        'cantidad_hijos',
        'estado',
        'urgencia',
        'precio_total',
        'fecha_solicitud'
    ]
    
    # Filtros disponibles en el sidebar
    list_filter = [
        'estado', 
        'urgencia', 
        'fecha_solicitud',
        'tipo_ceremonia',
        'fecha_fallecimiento'
    ]
    
    # Campos de búsqueda
    search_fields = [
        'codigo', 
        'nombre_fallecido', 
        'dni_fallecido',
        'nombre_esposa',
        'nombres_hijos',
        'cliente__username',
        'cliente__first_name', 
        'cliente__last_name',
        'cliente__empresa'
    ]
    
    # Campos de solo lectura
    readonly_fields = [
        'codigo',
        'fecha_solicitud',
        'fecha_programacion',
        'fecha_transmision_completada',
        'precio_total',
        'created_at',
        'updated_at'
    ]
    
    # Campos para edición rápida desde la lista
    list_editable = ['estado', 'urgencia']
    
    # Paginación
    list_per_page = 20
    
    # Ordenamiento por defecto
    ordering = ['-fecha_solicitud']
    
    # Agrupar campos en el formulario de edición
    fieldsets = (
        ('INFORMACIÓN BÁSICA', {
            'fields': (
                'codigo',
                'cliente',
                'fecha_solicitud',
                'estado',
                'urgencia'
            )
        }),
        ('INFORMACIÓN DEL FALLECIDO', {
            'fields': (
                'nombre_fallecido',
                'edad_fallecido',
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
                'precio_por_segundo',
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
                'creado_por',
                'fecha_programacion',
                'fecha_transmision_completada',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)  # Se puede colapsar
        }),
    )
    
    # Autocompletar el campo 'creado_por' con el usuario actual
    def save_model(self, request, obj, form, change):
        if not obj.creado_por:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    # Mostrar información adicional en la lista
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'creado_por')
    
    # Personalizar cómo se muestran algunos campos en la lista
    def precio_total_display(self, obj):
        return f"S/ {obj.precio_total:.2f}"
    precio_total_display.short_description = 'Precio Total'
    
    def familia_info(self, obj):
        info = []
        if obj.nombre_esposa:
            info.append(f"💍 {obj.nombre_esposa}")
        if obj.cantidad_hijos > 0:
            info.append(f"👨‍👩‍👧‍👦 {obj.cantidad_hijos} hijos")
        return " | ".join(info) if info else "—"
    familia_info.short_description = 'Información Familiar'

@admin.register(HistorialParteMortorio)
class HistorialParteMortorioAdmin(admin.ModelAdmin):
    # Campos a mostrar en la lista
    list_display = [
        'parte_mortorio', 
        'accion', 
        'usuario', 
        'fecha',
        'descripcion_corta'
    ]
    
    # Filtros disponibles
    list_filter = [
        'accion', 
        'fecha',
        'usuario'
    ]
    
    # Campos de búsqueda
    search_fields = [
        'parte_mortorio__codigo',
        'parte_mortorio__nombre_fallecido',
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'descripcion'
    ]
    
    # Campos de solo lectura
    readonly_fields = [
        'parte_mortorio',
        'accion',
        'usuario',
        'descripcion',
        'datos_anteriores',
        'datos_nuevos',
        'fecha'
    ]
    
    # Paginación
    list_per_page = 20
    
    # Ordenamiento por defecto
    ordering = ['-fecha']
    
    # Método personalizado para descripción corta
    def descripcion_corta(self, obj):
        if obj.descripcion and len(obj.descripcion) > 50:
            return obj.descripcion[:50] + '...'
        return obj.descripcion or '—'
    descripcion_corta.short_description = 'Descripción'
    
    # Evitar que se puedan crear historiales manualmente
    def has_add_permission(self, request):
        return False
    
    # Evitar que se puedan editar historiales manualmente
    def has_change_permission(self, request, obj=None):
        return False
    
    # Permitir solo la eliminación (si es necesario)
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# También puedes registrar acciones personalizadas para el admin
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