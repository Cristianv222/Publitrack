"""
Configuración de Django Admin para el módulo de Control de Transmisiones
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import (
    ConfiguracionTransmision,
    ProgramacionTransmision,
    TransmisionActual,
    LogTransmision,
    EventoSistema
)


@admin.register(ConfiguracionTransmision)
class ConfiguracionTransmisionAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_configuracion',
        'modo_operacion',
        'estado_sistema_badge',
        'horario_transmision',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'modo_operacion',
        'estado_sistema',
        'is_active',
        'permitir_solapamiento',
        'reproducir_solo_activas'
    ]
    
    search_fields = [
        'nombre_configuracion',
        'created_by__username'
    ]
    
    readonly_fields = [
        'created_by',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'nombre_configuracion',
                'modo_operacion',
                'estado_sistema',
                'is_active'
            )
        }),
        ('Configuración de Horarios', {
            'fields': (
                'hora_inicio_transmision',
                'hora_fin_transmision',
                'intervalo_minimo_segundos',
                'duracion_maxima_bloque'
            )
        }),
        ('Comportamiento del Sistema', {
            'fields': (
                'permitir_solapamiento',
                'priorizar_por_pago',
                'reproducir_solo_activas',
                'verificar_fechas_vigencia'
            )
        }),
        ('Configuración de Alertas', {
            'fields': (
                'notificar_errores',
                'notificar_inicio_fin'
            )
        }),
        ('Configuración Técnica', {
            'fields': (
                'volumen_base',
                'tiempo_fade_in',
                'tiempo_fade_out'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def estado_sistema_badge(self, obj):
        """Muestra el estado del sistema con color"""
        colors = {
            'activo': 'green',
            'pausado': 'orange',
            'detenido': 'red',
            'error': 'red',
            'mantenimiento': 'blue'
        }
        color = colors.get(obj.estado_sistema, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_sistema_display()
        )
    estado_sistema_badge.short_description = 'Estado'
    
    def horario_transmision(self, obj):
        """Muestra el horario de transmisión"""
        return f"{obj.hora_inicio_transmision.strftime('%H:%M')} - {obj.hora_fin_transmision.strftime('%H:%M')}"
    horario_transmision.short_description = 'Horario'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProgramacionTransmision)
class ProgramacionTransmisionAdmin(admin.ModelAdmin):
    list_display = [
        'codigo',
        'nombre',
        'cuña_info',
        'tipo_programacion',
        'estado_badge',
        'proxima_reproduccion',
        'estadisticas',
        'created_at'
    ]
    
    list_filter = [
        'tipo_programacion',
        'estado',
        'prioridad',
        'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo',
        'created_at'
    ]
    
    search_fields = [
        'codigo',
        'nombre',
        'cuña__titulo',
        'cuña__codigo',
        'created_by__username'
    ]
    
    readonly_fields = [
        'codigo',
        'total_reproducciones_programadas',
        'total_reproducciones_ejecutadas',
        'ultima_reproduccion',
        'proxima_reproduccion',
        'created_by',
        'created_at',
        'updated_at'
    ]
    
    raw_id_fields = ['cuña', 'configuracion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'codigo',
                'nombre',
                'descripcion',
                'cuña',
                'configuracion'
            )
        }),
        ('Estado y Prioridad', {
            'fields': (
                'estado',
                'prioridad'
            )
        }),
        ('Configuración Temporal', {
            'fields': (
                'tipo_programacion',
                'fecha_inicio',
                'fecha_fin',
                'repeticiones_por_dia',
                'intervalo_entre_repeticiones'
            )
        }),
        ('Días de la Semana', {
            'fields': (
                ('lunes', 'martes', 'miercoles', 'jueves'),
                ('viernes', 'sabado', 'domingo')
            ),
            'description': 'Selecciona los días en que se debe transmitir (para programación semanal)'
        }),
        ('Horarios Específicos', {
            'fields': (
                'horarios_especificos',
            ),
            'description': 'Lista de horarios específicos en formato ["HH:MM", "HH:MM", ...]'
        }),
        ('Configuración Avanzada', {
            'fields': (
                'permitir_ajuste_automatico',
                'respetar_intervalos_minimos'
            ),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': (
                'total_reproducciones_programadas',
                'total_reproducciones_ejecutadas',
                'ultima_reproduccion',
                'proxima_reproduccion'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activar_programaciones', 'cancelar_programaciones', 'recalcular_proximas']
    
    def cuña_info(self, obj):
        """Información de la cuña asociada"""
        if obj.cuña:
            url = reverse('admin:content_management_cuñapublicitaria_change', args=[obj.cuña.pk])
            return format_html(
                '<a href="{}">{}</a><br><small>{}</small>',
                url,
                obj.cuña.titulo,
                obj.cuña.codigo
            )
        return '-'
    cuña_info.short_description = 'Cuña'
    
    def estado_badge(self, obj):
        """Estado con color"""
        colors = {
            'programada': 'blue',
            'activa': 'green',
            'completada': 'gray',
            'cancelada': 'red',
            'error': 'red'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def estadisticas(self, obj):
        """Estadísticas de reproducción"""
        if obj.total_reproducciones_programadas > 0:
            porcentaje = (obj.total_reproducciones_ejecutadas / obj.total_reproducciones_programadas) * 100
            return format_html(
                '{}/{} ({}%)',
                obj.total_reproducciones_ejecutadas,
                obj.total_reproducciones_programadas,
                round(porcentaje, 1)
            )
        return f"{obj.total_reproducciones_ejecutadas}/0"
    estadisticas.short_description = 'Ejecutadas/Programadas'
    
    def activar_programaciones(self, request, queryset):
        """Activa las programaciones seleccionadas"""
        count = 0
        for programacion in queryset:
            if programacion.estado == 'programada':
                programacion.activar()
                count += 1
        
        if count:
            messages.success(request, f'{count} programaciones activadas.')
        else:
            messages.warning(request, 'No hay programaciones válidas para activar.')
    
    activar_programaciones.short_description = "Activar programaciones seleccionadas"
    
    def cancelar_programaciones(self, request, queryset):
        """Cancela las programaciones seleccionadas"""
        count = queryset.exclude(estado='cancelada').count()
        queryset.exclude(estado='cancelada').update(estado='cancelada', proxima_reproduccion=None)
        
        if count:
            messages.success(request, f'{count} programaciones canceladas.')
    
    cancelar_programaciones.short_description = "Cancelar programaciones seleccionadas"
    
    def recalcular_proximas(self, request, queryset):
        """Recalcula las próximas reproducciones"""
        count = 0
        for programacion in queryset.filter(estado='activa'):
            programacion.calcular_proxima_reproduccion()
            count += 1
        
        if count:
            messages.success(request, f'Próximas reproducciones recalculadas para {count} programaciones.')
    
    recalcular_proximas.short_description = "Recalcular próximas reproducciones"
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TransmisionActual)
class TransmisionActualAdmin(admin.ModelAdmin):
    list_display = [
        'session_id_short',
        'cuña_info',
        'estado_badge',
        'progreso_info',
        'inicio_info',
        'duracion_info',
        'control_manual'
    ]
    
    list_filter = [
        'estado',
        'pausado_manualmente',
        'calidad_transmision',
        'created_at'
    ]
    
    search_fields = [
        'session_id',
        'cuña__titulo',
        'cuña__codigo',
        'programacion__codigo'
    ]
    
    readonly_fields = [
        'session_id',
        'duracion_segundos',
        'inicio_real',
        'fin_real',
        'retraso_inicio_calc',
        'progreso_porcentaje_calc',
        'tiempo_restante_calc',
        'created_at',
        'updated_at'
    ]
    
    raw_id_fields = ['programacion', 'cuña', 'pausado_por']
    
    fieldsets = (
        ('Información de la Transmisión', {
            'fields': (
                'session_id',
                'programacion',
                'cuña',
                'estado'
            )
        }),
        ('Tiempo y Duración', {
            'fields': (
                'inicio_programado',
                'inicio_real',
                'fin_programado',
                'fin_real',
                'duracion_segundos',
                'posicion_actual'
            )
        }),
        ('Control Manual', {
            'fields': (
                'pausado_manualmente',
                'pausado_por',
                'pausado_en',
                'tiempo_total_pausado'
            )
        }),
        ('Configuración Técnica', {
            'fields': (
                'volumen',
                'fade_in_aplicado',
                'fade_out_aplicado',
                'calidad_transmision'
            )
        }),
        ('Información Adicional', {
            'fields': (
                'errores_detectados',
                'metadatos_transmision'
            ),
            'classes': ('collapse',)
        }),
        ('Cálculos Automáticos', {
            'fields': (
                'retraso_inicio_calc',
                'progreso_porcentaje_calc',
                'tiempo_restante_calc'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['pausar_transmisiones', 'reanudar_transmisiones', 'finalizar_transmisiones']
    
    def session_id_short(self, obj):
        """ID de sesión abreviado"""
        return str(obj.session_id)[:8] + '...'
    session_id_short.short_description = 'Session ID'
    
    def cuña_info(self, obj):
        """Información de la cuña"""
        if obj.cuña:
            url = reverse('admin:content_management_cuñapublicitaria_change', args=[obj.cuña.pk])
            return format_html(
                '<a href="{}">{}</a><br><small>{}</small>',
                url,
                obj.cuña.titulo[:30] + ('...' if len(obj.cuña.titulo) > 30 else ''),
                obj.cuña.codigo
            )
        return '-'
    cuña_info.short_description = 'Cuña'
    
    def estado_badge(self, obj):
        """Estado con color"""
        colors = {
            'preparando': 'blue',
            'transmitiendo': 'green',
            'pausada': 'orange',
            'completada': 'gray',
            'error': 'red',
            'cancelada': 'red'
        }
        color = colors.get(obj.estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = 'Estado'
    
    def progreso_info(self, obj):
        """Información de progreso"""
        if obj.esta_transmitiendo or obj.esta_pausada:
            porcentaje = obj.progreso_porcentaje
            return format_html(
                '{}% ({}/{}s)',
                round(porcentaje, 1),
                obj.posicion_actual,
                obj.duracion_segundos or 0
            )
        return '-'
    progreso_info.short_description = 'Progreso'
    
    def inicio_info(self, obj):
        """Información de inicio"""
        if obj.inicio_real:
            retraso = obj.retraso_inicio
            color = 'red' if retraso > 10 else 'orange' if retraso > 0 else 'green'
            return format_html(
                '{}<br><small style="color: {};">Retraso: {}s</small>',
                obj.inicio_real.strftime('%H:%M:%S'),
                color,
                round(retraso, 1)
            )
        elif obj.inicio_programado:
            return format_html(
                '<small>Programado: {}</small>',
                obj.inicio_programado.strftime('%H:%M:%S')
            )
        return '-'
    inicio_info.short_description = 'Inicio'
    
    def duracion_info(self, obj):
        """Información de duración"""
        if obj.duracion_segundos:
            minutos = obj.duracion_segundos // 60
            segundos = obj.duracion_segundos % 60
            return f"{minutos:02d}:{segundos:02d}"
        return '-'
    duracion_info.short_description = 'Duración'
    
    def control_manual(self, obj):
        """Indicadores de control manual"""
        badges = []
        if obj.pausado_manualmente:
            badges.append('<span style="color: orange;">⏸ Pausado</span>')
        if obj.errores_detectados:
            badges.append(f'<span style="color: red;">⚠ {len(obj.errores_detectados)} errores</span>')
        return format_html('<br>'.join(badges)) if badges else '-'
    control_manual.short_description = 'Control'
    
    def retraso_inicio_calc(self, obj):
        """Cálculo del retraso de inicio"""
        return f"{obj.retraso_inicio:.1f} segundos"
    retraso_inicio_calc.short_description = 'Retraso de Inicio'
    
    def progreso_porcentaje_calc(self, obj):
        """Cálculo del porcentaje de progreso"""
        return f"{obj.progreso_porcentaje:.1f}%"
    progreso_porcentaje_calc.short_description = 'Progreso %'
    
    def tiempo_restante_calc(self, obj):
        """Cálculo del tiempo restante"""
        restante = obj.tiempo_restante
        minutos = restante // 60
        segundos = restante % 60
        return f"{minutos:02d}:{segundos:02d}"
    tiempo_restante_calc.short_description = 'Tiempo Restante'
    
    def pausar_transmisiones(self, request, queryset):
        """Pausa las transmisiones seleccionadas"""
        count = 0
        for transmision in queryset.filter(estado='transmitiendo'):
            transmision.pausar_transmision(request.user)
            count += 1
        
        if count:
            messages.success(request, f'{count} transmisiones pausadas.')
        else:
            messages.warning(request, 'No hay transmisiones válidas para pausar.')
    
    pausar_transmisiones.short_description = "Pausar transmisiones seleccionadas"
    
    def reanudar_transmisiones(self, request, queryset):
        """Reanuda las transmisiones seleccionadas"""
        count = 0
        for transmision in queryset.filter(estado='pausada'):
            transmision.reanudar_transmision(request.user)
            count += 1
        
        if count:
            messages.success(request, f'{count} transmisiones reanudadas.')
        else:
            messages.warning(request, 'No hay transmisiones válidas para reanudar.')
    
    reanudar_transmisiones.short_description = "Reanudar transmisiones seleccionadas"
    
    def finalizar_transmisiones(self, request, queryset):
        """Finaliza las transmisiones seleccionadas"""
        count = 0
        for transmision in queryset.filter(estado__in=['transmitiendo', 'pausada']):
            transmision.finalizar_transmision(request.user, 'cancelada')
            count += 1
        
        if count:
            messages.success(request, f'{count} transmisiones finalizadas.')
        else:
            messages.warning(request, 'No hay transmisiones válidas para finalizar.')
    
    finalizar_transmisiones.short_description = "Finalizar transmisiones seleccionadas"


@admin.register(LogTransmision)
class LogTransmisionAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'accion_badge',
        'descripcion_short',
        'usuario',
        'transmision_info',
        'nivel_badge'
    ]
    
    list_filter = [
        'accion',
        'nivel',
        'timestamp',
        'usuario'
    ]
    
    search_fields = [
        'descripcion',
        'usuario__username',
        'transmision__session_id',
        'cuña__titulo',
        'programacion__codigo'
    ]
    
    readonly_fields = [
        'timestamp',
        'transmision',
        'programacion',
        'cuña',
        'accion',
        'nivel',
        'descripcion',
        'usuario',
        'datos',
        'ip_address',
        'user_agent'
    ]
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información del Evento', {
            'fields': (
                'timestamp',
                'accion',
                'nivel',
                'descripcion'
            )
        }),
        ('Relaciones', {
            'fields': (
                'transmision',
                'programacion',
                'cuña',
                'usuario'
            )
        }),
        ('Datos Técnicos', {
            'fields': (
                'datos',
                'ip_address',
                'user_agent'
            ),
            'classes': ('collapse',)
        })
    )
    
    def accion_badge(self, obj):
        """Acción con color"""
        colors = {
            'iniciada': 'green',
            'finalizada': 'blue',
            'pausada': 'orange',
            'reanudada': 'green',
            'error': 'red',
            'cancelada': 'red'
        }
        color = colors.get(obj.accion, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_accion_display()
        )
    accion_badge.short_description = 'Acción'
    
    def nivel_badge(self, obj):
        """Nivel con color"""
        colors = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'red'
        }
        color = colors.get(obj.nivel, 'gray')
        return format_html(
            '<span style="color: {};">●</span>',
            color
        )
    nivel_badge.short_description = 'Nivel'
    
    def descripcion_short(self, obj):
        """Descripción abreviada"""
        if len(obj.descripcion) > 50:
            return obj.descripcion[:50] + '...'
        return obj.descripcion
    descripcion_short.short_description = 'Descripción'
    
    def transmision_info(self, obj):
        """Información de la transmisión"""
        if obj.transmision:
            return format_html(
                '<small>{}...</small>',
                str(obj.transmision.session_id)[:8]
            )
        elif obj.cuña:
            return format_html(
                '<small>{}</small>',
                obj.cuña.codigo
            )
        return '-'
    transmision_info.short_description = 'Transmisión/Cuña'
    
    def has_add_permission(self, request):
        """Los logs no se pueden crear manualmente"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Los logs son de solo lectura"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo los admins pueden eliminar logs"""
        return request.user.is_superuser


@admin.register(EventoSistema)
class EventoSistemaAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'tipo_evento_badge',
        'descripcion_short',
        'usuario',
        'resuelto_badge'
    ]
    
    list_filter = [
        'tipo_evento',
        'resuelto',
        'timestamp',
        'usuario'
    ]
    
    search_fields = [
        'descripcion',
        'usuario__username'
    ]
    
    readonly_fields = [
        'timestamp'
    ]
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información del Evento', {
            'fields': (
                'tipo_evento',
                'descripcion',
                'usuario',
                'timestamp',
                'resuelto'
            )
        }),
        ('Datos del Sistema', {
            'fields': (
                'datos_sistema',
            ),
            'classes': ('collapse',)
        }),
        ('Configuraciones (Solo para cambios de configuración)', {
            'fields': (
                'configuracion_antes',
                'configuracion_despues'
            ),
            'classes': ('collapse',)
        })
    )
    
    def tipo_evento_badge(self, obj):
        """Tipo de evento con color"""
        colors = {
            'inicio_sistema': 'green',
            'parada_sistema': 'red',
            'reinicio_sistema': 'orange',
            'mantenimiento_inicio': 'blue',
            'mantenimiento_fin': 'blue',
            'cambio_configuracion': 'orange',
            'error_critico': 'red',
            'recuperacion_error': 'green'
        }
        color = colors.get(obj.tipo_evento, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_tipo_evento_display()
        )
    tipo_evento_badge.short_description = 'Tipo de Evento'
    
    def descripcion_short(self, obj):
        """Descripción abreviada"""
        if len(obj.descripcion) > 60:
            return obj.descripcion[:60] + '...'
        return obj.descripcion
    descripcion_short.short_description = 'Descripción'
    
    def resuelto_badge(self, obj):
        """Estado de resolución con color"""
        if obj.resuelto:
            return format_html('<span style="color: green;">✓ Resuelto</span>')
        else:
            return format_html('<span style="color: red;">✗ Pendiente</span>')
    resuelto_badge.short_description = 'Estado'


# Configuración adicional del admin
admin.site.site_header = "PubliTrack - Control de Transmisiones"
admin.site.site_title = "PubliTrack Admin"
admin.site.index_title = "Administración del Sistema"