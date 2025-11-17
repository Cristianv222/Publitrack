# grilla_publicitaria/admin.py
from django.contrib import admin
from django.utils.html import format_html

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

    @admin.register(UbicacionPublicitaria)
    class UbicacionPublicitariaAdmin(admin.ModelAdmin):
        list_display = [
            'nombre', 'bloque_programacion', 'tipo_ubicacion', 
            'hora_inicio_relativa', 'duracion_disponible', 'activo'
        ]
        list_filter = ['tipo_ubicacion', 'activo', 'bloque_programacion__programacion_semanal']
        search_fields = ['nombre', 'bloque_programacion__programa__nombre']

    @admin.register(AsignacionCuña)
    class AsignacionCuñaAdmin(admin.ModelAdmin):
        list_display = [
            'cuña', 'ubicacion', 'fecha_emision', 'hora_emision',
            'estado_badge', 'orden_en_ubicacion'
        ]
        
        list_filter = ['estado', 'fecha_emision', 'ubicacion__tipo_ubicacion']
        search_fields = ['cuña__codigo', 'cuña__titulo', 'ubicacion__nombre']
        date_hierarchy = 'fecha_emision'
        
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

    @admin.register(GrillaPublicitaria)
    class GrillaPublicitariaAdmin(admin.ModelAdmin):
        list_display = [
            'programacion_semanal', 'fecha_generacion', 
            'total_cuñas_programadas', 'total_ingresos_proyectados'
        ]
        list_filter = ['programacion_semanal__fecha_inicio_semana']
        readonly_fields = ['fecha_generacion', 'total_cuñas_programadas', 'total_ingresos_proyectados']