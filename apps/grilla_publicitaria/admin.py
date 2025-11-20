# grilla_publicitaria/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# IMPORTS CONDICIONALES
try:
    from .models import (
        TipoUbicacionPublicitaria, UbicacionPublicitaria, 
        AsignacionCuña, GrillaPublicitaria
    )
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando modelos de grilla: {e}")
    MODELS_AVAILABLE = False

if MODELS_AVAILABLE:
    @admin.register(TipoUbicacionPublicitaria)
    class TipoUbicacionPublicitariaAdmin(admin.ModelAdmin):
        list_display = ['nombre', 'codigo', 'duracion_maxima', 'prioridad']
        list_filter = ['prioridad']
        search_fields = ['nombre', 'codigo']
        list_editable = ['prioridad']
        
        fieldsets = (
            ('Información Básica', {
                'fields': ('nombre', 'codigo', 'descripcion')
            }),
            ('Configuración', {
                'fields': ('duracion_maxima', 'prioridad')
            }),
        )

    @admin.register(UbicacionPublicitaria)
    class UbicacionPublicitariaAdmin(admin.ModelAdmin):
        list_display = [
            'nombre', 
            'bloque_programacion_display', 
            'hora_pausa',
            'tipo_pausa_badge',
            'duracion_pausa',
            'capacidad_cuñas',
            'espacios_disponibles_badge',
            'cuñas_asignadas_count',
            'acciones_rapidas'
        ]
        
        list_filter = [
            'activo', 
            'tipo_pausa',
            'bloque_programacion__programacion_semanal',
            'bloque_programacion__dia_semana'
        ]
        
        search_fields = [
            'nombre', 
            'bloque_programacion__programa__nombre',
            'bloque_programacion__programacion_semanal__nombre'
        ]
        
        readonly_fields = ['cuñas_asignadas_count', 'espacios_disponibles_badge']
        
        fieldsets = (
            ('Información Básica', {
                'fields': (
                    'bloque_programacion', 
                    'nombre',
                    'tipo_pausa'
                )
            }),
            ('Configuración de Tiempo', {
                'fields': (
                    'hora_pausa',
                    'duracion_pausa',
                    'capacidad_cuñas'
                )
            }),
            ('Estado', {
                'fields': ('activo',)
            }),
        )
        
        def bloque_programacion_display(self, obj):
            return f"{obj.bloque_programacion.programa.nombre} - {obj.bloque_programacion.get_dia_semana_display()}"
        bloque_programacion_display.short_description = 'Bloque'
        
        def tipo_pausa_badge(self, obj):
            colors = {
                'corta': 'success',
                'media': 'warning', 
                'larga': 'danger'
            }
            color = colors.get(obj.tipo_pausa, 'secondary')
            return format_html(
                '<span class="badge bg-{}">{}</span>',
                color, obj.get_tipo_pausa_display()
            )
        tipo_pausa_badge.short_description = 'Tipo'
        
        def espacios_disponibles_badge(self, obj):
            disponibles = obj.espacios_disponibles
            color = 'success' if disponibles > 0 else 'warning'
            return format_html(
                '<span class="badge bg-{}">{}/{} espacios</span>',
                color, disponibles, obj.capacidad_cuñas
            )
        espacios_disponibles_badge.short_description = 'Espacios'
        
        def cuñas_asignadas_count(self, obj):
            count = obj.asignaciones.count()
            return format_html(
                '<span class="badge bg-{}">{}</span>',
                'primary' if count > 0 else 'secondary', 
                count
            )
        cuñas_asignadas_count.short_description = 'Cuñas Asignadas'
        
        def acciones_rapidas(self, obj):
            return format_html(
                '<a href="/admin/grilla_publicitaria/asignacioncuna/?ubicacion__id__exact={}" class="button">Ver Cuñas</a>',
                obj.id
            )
        acciones_rapidas.short_description = 'Acciones'

    # ✅ CORREGIDO: Este decorador debe estar al mismo nivel que los otros
    @admin.register(AsignacionCuña)
    class AsignacionCuñaAdmin(admin.ModelAdmin):
        list_display = [
            'cuña_display', 
            'ubicacion_display', 
            'fecha_emision', 
            'hora_emision',
            'duracion_cuña',
            'estado_badge', 
            'orden_en_ubicacion',
            'creado_por_display'
        ]
        
        list_filter = [
            'estado', 
            'fecha_emision', 
            'ubicacion__bloque_programacion__programacion_semanal'
        ]
        
        search_fields = [
            'cuña__codigo', 
            'cuña__titulo', 
            'ubicacion__nombre',
            'creado_por__username',
            'creado_por__first_name',
            'creado_por__last_name'
        ]
        
        date_hierarchy = 'fecha_emision'
        
        readonly_fields = [
            'fecha_creacion', 
            'fecha_actualizacion', 
            'creado_por'
        ]
        
        fieldsets = (
            ('Información de Asignación', {
                'fields': (
                    'ubicacion',
                    'cuña',
                    'fecha_emision',
                    'hora_emision',
                    'orden_en_ubicacion'
                )
            }),
            ('Estado', {
                'fields': ('estado',)
            }),
            ('Metadatos', {
                'fields': (
                    'creado_por',
                    'fecha_creacion',
                    'fecha_actualizacion'
                ),
                'classes': ('collapse',)
            }),
        )
        
        def cuña_display(self, obj):
            return f"{obj.cuña.codigo} - {obj.cuña.titulo}"
        cuña_display.short_description = 'Cuña Publicitaria'
        
        def ubicacion_display(self, obj):
            return f"{obj.ubicacion.bloque_programacion.programa.nombre} - {obj.ubicacion.nombre}"
        ubicacion_display.short_description = 'Ubicación'
        
        def duracion_cuña(self, obj):
            return f"{obj.cuña.duracion_planeada}s"
        duracion_cuña.short_description = 'Duración'
        
        def estado_badge(self, obj):
            colors = {
                'programada': 'secondary',
                'confirmada': 'success', 
                'transmitida': 'info',
                'cancelada': 'danger'
            }
            color = colors.get(obj.estado, 'secondary')
            return format_html(
                '<span class="badge bg-{}">{}</span>',
                color, obj.get_estado_display()
            )
        estado_badge.short_description = 'Estado'
        
        def creado_por_display(self, obj):
            if obj.creado_por:
                return obj.creado_por.get_full_name() or obj.creado_por.username
            return '-'
        creado_por_display.short_description = 'Creado por'
        
        def save_model(self, request, obj, form, change):
            if not obj.creado_por:
                obj.creado_por = request.user
            super().save_model(request, obj, form, change)

    @admin.register(GrillaPublicitaria)
    class GrillaPublicitariaAdmin(admin.ModelAdmin):
        list_display = [
            'programacion_semanal_display', 
            'fecha_generacion', 
            'total_cuñas_programadas_badge',
            'total_ingresos_proyectados_format',
            'generada_por_display'
        ]
        
        list_filter = [
            'programacion_semanal__fecha_inicio_semana',
            'fecha_generacion'
        ]
        
        search_fields = [
            'programacion_semanal__nombre',
            'programacion_semanal__codigo',
            'generada_por__username'
        ]
        
        readonly_fields = [
            'fecha_generacion', 
            'total_cuñas_programadas', 
            'total_ingresos_proyectados',
            'generada_por'
        ]
        
        fieldsets = (
            ('Información de la Grilla', {
                'fields': (
                    'programacion_semanal',
                    'generada_por',
                    'fecha_generacion'
                )
            }),
            ('Estadísticas', {
                'fields': (
                    'total_cuñas_programadas',
                    'total_ingresos_proyectados',
                )
            }),
        )
        
        def programacion_semanal_display(self, obj):
            return f"{obj.programacion_semanal.nombre} ({obj.programacion_semanal.fecha_inicio_semana} - {obj.programacion_semanal.fecha_fin_semana})"
        programacion_semanal_display.short_description = 'Programación Semanal'
        
        def total_cuñas_programadas_badge(self, obj):
            color = 'success' if obj.total_cuñas_programadas > 0 else 'secondary'
            return format_html(
                '<span class="badge bg-{}">{}</span>',
                color, obj.total_cuñas_programadas
            )
        total_cuñas_programadas_badge.short_description = 'Cuñas Programadas'
        
        def total_ingresos_proyectados_format(self, obj):
            return f"${obj.total_ingresos_proyectados:,.2f}"
        total_ingresos_proyectados_format.short_description = 'Ingresos Proyectados'
        
        def generada_por_display(self, obj):
            if obj.generada_por:
                return obj.generada_por.get_full_name() or obj.generada_por.username
            return '-'
        generada_por_display.short_description = 'Generada por'
        
        def save_model(self, request, obj, form, change):
            if not obj.generada_por:
                obj.generada_por = request.user
            super().save_model(request, obj, form, change)
        
        actions = ['actualizar_estadisticas']
        
        def actualizar_estadisticas(self, request, queryset):
            for grilla in queryset:
                grilla.actualizar_estadisticas()
            self.message_user(
                request, 
                f"Estadísticas actualizadas para {queryset.count()} grilla(s)"
            )
        actualizar_estadisticas.short_description = "Actualizar estadísticas de las grillas seleccionadas"