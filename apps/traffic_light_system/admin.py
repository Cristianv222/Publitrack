"""
Configuración Django Admin para el Sistema de Semáforos
Sistema PubliTrack - Gestión administrativa de estados y configuraciones
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect
from django.contrib import messages
from datetime import timedelta

from .models import (
    ConfiguracionSemaforo, EstadoSemaforo, HistorialEstadoSemaforo,
    AlertaSemaforo, ResumenEstadosSemaforo
)
from .utils.status_calculator import StatusCalculator, AlertasManager


class ColorEstadoFilter(SimpleListFilter):
    """Filtro personalizado para color de estado"""
    title = 'Color del Semáforo'
    parameter_name = 'color'
    
    def lookups(self, request, model_admin):
        return (
            ('verde', '🟢 Verde'),
            ('amarillo', '🟡 Amarillo'),
            ('rojo', '🔴 Rojo'),
            ('gris', '⚫ Gris'),
        )
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(color_actual=self.value())
        return queryset


class RequiereAlertaFilter(SimpleListFilter):
    """Filtro para estados que requieren alerta"""
    title = 'Requiere Alerta'
    parameter_name = 'alerta'
    
    def lookups(self, request, model_admin):
        return (
            ('si', 'Sí requiere alerta'),
            ('no', 'No requiere alerta'),
            ('pendiente', 'Alerta pendiente de envío'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'si':
            return queryset.filter(requiere_alerta=True)
        elif self.value() == 'no':
            return queryset.filter(requiere_alerta=False)
        elif self.value() == 'pendiente':
            return queryset.filter(requiere_alerta=True, alerta_enviada=False)
        return queryset


class CuñaVencidaFilter(SimpleListFilter):
    """Filtro para cuñas vencidas"""
    title = 'Estado de Vencimiento'
    parameter_name = 'vencimiento'
    
    def lookups(self, request, model_admin):
        return (
            ('vencida', 'Vencida'),
            ('proximo', 'Próxima a vencer (7 días)'),
            ('vigente', 'Vigente'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'vencida':
            return queryset.filter(dias_restantes__lt=0)
        elif self.value() == 'proximo':
            return queryset.filter(dias_restantes__gte=0, dias_restantes__lte=7)
        elif self.value() == 'vigente':
            return queryset.filter(dias_restantes__gt=7)
        return queryset


@admin.register(ConfiguracionSemaforo)
class ConfiguracionSemaforoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_calculo', 'estado_configuracion', 
        'dias_verde_min', 'dias_amarillo_min', 'enviar_alertas', 
        'created_at', 'acciones_admin'
    ]
    list_filter = ['is_active', 'is_default', 'tipo_calculo', 'enviar_alertas']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'tipo_calculo')
        }),
        ('Configuración por Días', {
            'fields': ('dias_verde_min', 'dias_amarillo_min'),
            'classes': ('collapse',)
        }),
        ('Configuración por Porcentaje', {
            'fields': ('porcentaje_verde_max', 'porcentaje_amarillo_max'),
            'classes': ('collapse',)
        }),
        ('Estados por Color', {
            'fields': ('estados_verde', 'estados_amarillo', 'estados_rojo', 'estados_gris'),
            'classes': ('collapse',)
        }),
        ('Configuración de Alertas', {
            'fields': ('enviar_alertas', 'alertas_solo_empeoramiento')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_default')
        }),
        ('Metadatos', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activar_configuracion', 'recalcular_con_configuracion']
    
    def estado_configuracion(self, obj):
        """Muestra el estado de la configuración con íconos"""
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Activa</span>')
        elif obj.is_default:
            return format_html('<span style="color: blue;">🔵 Por Defecto</span>')
        else:
            return format_html('<span style="color: gray;">⚫ Inactiva</span>')
    estado_configuracion.short_description = 'Estado'
    
    def acciones_admin(self, obj):
        """Botones de acción personalizada"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">CONFIGURACIÓN ACTIVA</span>'
            )
        else:
            activate_url = reverse('admin:traffic_light_system_configuracionsemaforo_change', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}?activate=true">Activar</a>',
                activate_url
            )
    acciones_admin.short_description = 'Acciones'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nueva
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def response_change(self, request, obj):
        """Maneja activación desde el botón personalizado"""
        if 'activate' in request.GET:
            # Desactivar todas las demás configuraciones
            ConfiguracionSemaforo.objects.update(is_active=False)
            obj.is_active = True
            obj.save()
            
            # Recalcular estados con la nueva configuración
            calculator = StatusCalculator(obj)
            stats = calculator.actualizar_todas_las_cuñas()
            
            self.message_user(
                request,
                f'Configuración "{obj.nombre}" activada. '
                f'Se recalcularon {stats["total_procesadas"]} cuñas.',
                messages.SUCCESS
            )
            
            return HttpResponseRedirect(reverse('admin:traffic_light_system_configuracionsemaforo_changelist'))
        
        return super().response_change(request, obj)
    
    def activar_configuracion(self, request, queryset):
        """Acción para activar una configuración"""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Selecciona exactamente una configuración para activar.',
                messages.ERROR
            )
            return
        
        config = queryset.first()
        ConfiguracionSemaforo.objects.update(is_active=False)
        config.is_active = True
        config.save()
        
        self.message_user(
            request,
            f'Configuración "{config.nombre}" activada exitosamente.',
            messages.SUCCESS
        )
    activar_configuracion.short_description = 'Activar configuración seleccionada'
    
    def recalcular_con_configuracion(self, request, queryset):
        """Recalcula estados con las configuraciones seleccionadas"""
        for config in queryset:
            calculator = StatusCalculator(config)
            stats = calculator.actualizar_todas_las_cuñas()
            
            self.message_user(
                request,
                f'Recalculado con "{config.nombre}": {stats["total_procesadas"]} cuñas procesadas.',
                messages.INFO
            )
    recalcular_con_configuracion.short_description = 'Recalcular estados con esta configuración'


@admin.register(EstadoSemaforo)
class EstadoSemaforoAdmin(admin.ModelAdmin):
    list_display = [
        'cuña_codigo', 'cuña_titulo', 'cliente_nombre', 'color_visual',
        'prioridad_visual', 'dias_restantes', 'porcentaje_tiempo_visual',
        'requiere_alerta_visual', 'ultimo_calculo'
    ]
    list_filter = [
        ColorEstadoFilter, 'prioridad', RequiereAlertaFilter, 
        CuñaVencidaFilter, 'configuracion_utilizada'
    ]
    search_fields = [
        'cuña__codigo', 'cuña__titulo', 'cuña__cliente__first_name',
        'cuña__cliente__last_name', 'cuña__cliente__empresa'
    ]
    readonly_fields = [
        'cuña', 'color_anterior', 'configuracion_utilizada',
        'calculado_en', 'ultimo_calculo', 'metadatos_calculo'
    ]
    
    fieldsets = (
        ('Cuña Asociada', {
            'fields': ('cuña',)
        }),
        ('Estado Actual', {
            'fields': ('color_actual', 'color_anterior', 'prioridad', 'razon_color')
        }),
        ('Métricas Calculadas', {
            'fields': (
                'dias_restantes', 'porcentaje_tiempo_transcurrido',
                'metadatos_calculo'
            )
        }),
        ('Alertas', {
            'fields': (
                'requiere_alerta', 'alerta_enviada', 'fecha_alerta_enviada'
            )
        }),
        ('Configuración y Fechas', {
            'fields': ('configuracion_utilizada', 'calculado_en', 'ultimo_calculo'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['recalcular_estados_seleccionados', 'generar_alertas_seleccionadas']
    
    def cuña_codigo(self, obj):
        """Link al código de la cuña"""
        url = reverse('admin:content_management_cuñapublicitaria_change', args=[obj.cuña.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cuña.codigo)
    cuña_codigo.short_description = 'Código'
    cuña_codigo.admin_order_field = 'cuña__codigo'
    
    def cuña_titulo(self, obj):
        """Título de la cuña"""
        return obj.cuña.titulo[:50] + '...' if len(obj.cuña.titulo) > 50 else obj.cuña.titulo
    cuña_titulo.short_description = 'Título'
    cuña_titulo.admin_order_field = 'cuña__titulo'
    
    def cliente_nombre(self, obj):
        """Nombre del cliente"""
        return obj.cuña.cliente.get_full_name() or obj.cuña.cliente.empresa
    cliente_nombre.short_description = 'Cliente'
    cliente_nombre.admin_order_field = 'cuña__cliente__first_name'
    
    def color_visual(self, obj):
        """Muestra el color con ícono visual"""
        iconos = {
            'verde': '🟢',
            'amarillo': '🟡',
            'rojo': '🔴',
            'gris': '⚫'
        }
        return format_html(
            '{} {}',
            iconos.get(obj.color_actual, '❓'),
            obj.get_color_actual_display()
        )
    color_visual.short_description = 'Color'
    color_visual.admin_order_field = 'color_actual'
    
    def prioridad_visual(self, obj):
        """Muestra la prioridad con colores"""
        colores = {
            'baja': 'green',
            'media': 'orange',
            'alta': 'red',
            'critica': 'darkred'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colores.get(obj.prioridad, 'black'),
            obj.get_prioridad_display()
        )
    prioridad_visual.short_description = 'Prioridad'
    prioridad_visual.admin_order_field = 'prioridad'
    
    def porcentaje_tiempo_visual(self, obj):
        """Muestra el porcentaje con barra visual"""
        if obj.porcentaje_tiempo_transcurrido is None:
            return '-'
        
        porcentaje = float(obj.porcentaje_tiempo_transcurrido)
        color = 'green' if porcentaje < 50 else 'orange' if porcentaje < 85 else 'red'
        
        return format_html(
            '<div style="width: 100px; background-color: #eee; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">'
            '{}%'
            '</div></div>',
            min(porcentaje, 100), color, round(porcentaje, 1)
        )
    porcentaje_tiempo_visual.short_description = 'Tiempo Transcurrido'
    porcentaje_tiempo_visual.admin_order_field = 'porcentaje_tiempo_transcurrido'
    
    def requiere_alerta_visual(self, obj):
        """Muestra si requiere alerta con íconos"""
        if obj.requiere_alerta:
            if obj.alerta_enviada:
                return format_html('<span style="color: orange;">⚠️ Enviada</span>')
            else:
                return format_html('<span style="color: red;">🚨 Pendiente</span>')
        return format_html('<span style="color: green;">✅ No</span>')
    requiere_alerta_visual.short_description = 'Alerta'
    
    def recalcular_estados_seleccionados(self, request, queryset):
        """Recalcula los estados seleccionados"""
        calculator = StatusCalculator()
        actualizados = 0
        
        for estado in queryset:
            calculator.actualizar_estado_cuña(estado.cuña)
            actualizados += 1
        
        self.message_user(
            request,
            f'Se recalcularon {actualizados} estados exitosamente.',
            messages.SUCCESS
        )
    recalcular_estados_seleccionados.short_description = 'Recalcular estados seleccionados'
    
    def generar_alertas_seleccionadas(self, request, queryset):
        """Genera alertas para los estados seleccionados que las requieren"""
        manager = AlertasManager()
        alertas_generadas = 0
        
        for estado in queryset.filter(requiere_alerta=True, alerta_enviada=False):
            try:
                manager._crear_alerta_para_estado(estado)
                alertas_generadas += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error generando alerta para {estado.cuña.codigo}: {str(e)}',
                    messages.ERROR
                )
        
        self.message_user(
            request,
            f'Se generaron {alertas_generadas} alertas exitosamente.',
            messages.SUCCESS
        )
    generar_alertas_seleccionadas.short_description = 'Generar alertas para seleccionados'


@admin.register(HistorialEstadoSemaforo)
class HistorialEstadoSemaforoAdmin(admin.ModelAdmin):
    list_display = [
        'cuña_codigo', 'cambio_visual', 'prioridad_cambio',
        'dias_restantes', 'alerta_generada', 'fecha_cambio', 'usuario_trigger'
    ]
    list_filter = [
        'color_nuevo', 'color_anterior', 'alerta_generada',
        'configuracion_utilizada', 'fecha_cambio'
    ]
    search_fields = [
        'cuña__codigo', 'cuña__titulo', 'razon_cambio',
        'usuario_trigger__username'
    ]
    readonly_fields = [
        'cuña', 'color_anterior', 'color_nuevo', 'prioridad_anterior',
        'prioridad_nueva', 'razon_cambio', 'fecha_cambio', 'metadatos'
    ]
    date_hierarchy = 'fecha_cambio'
    
    def cuña_codigo(self, obj):
        """Link al código de la cuña"""
        url = reverse('admin:content_management_cuñapublicitaria_change', args=[obj.cuña.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cuña.codigo)
    cuña_codigo.short_description = 'Código'
    
    def cambio_visual(self, obj):
        """Muestra el cambio de color visualmente"""
        iconos = {
            'verde': '🟢', 'amarillo': '🟡', 'rojo': '🔴', 'gris': '⚫'
        }
        
        anterior = iconos.get(obj.color_anterior, '❓') if obj.color_anterior else '➕'
        nuevo = iconos.get(obj.color_nuevo, '❓')
        
        return format_html('{} → {}', anterior, nuevo)
    cambio_visual.short_description = 'Cambio'
    
    def prioridad_cambio(self, obj):
        """Muestra el cambio de prioridad"""
        if obj.prioridad_anterior:
            return format_html(
                '{} → {}',
                obj.get_prioridad_anterior_display(),
                obj.get_prioridad_nueva_display()
            )
        return obj.get_prioridad_nueva_display()
    prioridad_cambio.short_description = 'Prioridad'


@admin.register(AlertaSemaforo)
class AlertaSemaforoAdmin(admin.ModelAdmin):
    list_display = [
        'titulo_corto', 'cuña_codigo', 'tipo_alerta', 'severidad_visual',
        'estado_visual', 'canales_envio', 'created_at', 'fecha_enviada'
    ]
    list_filter = [
        'tipo_alerta', 'severidad', 'estado', 'enviar_email',
        'enviar_sms', 'enviar_push', 'created_at'
    ]
    search_fields = [
        'titulo', 'mensaje', 'cuña__codigo', 'cuña__titulo'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'fecha_enviada', 'reintentos'
    ]
    
    fieldsets = (
        ('Información de la Alerta', {
            'fields': ('cuña', 'estado_semaforo', 'tipo_alerta', 'severidad')
        }),
        ('Contenido', {
            'fields': ('titulo', 'mensaje')
        }),
        ('Destinatarios', {
            'fields': ('usuarios_destino', 'roles_destino')
        }),
        ('Canales de Envío', {
            'fields': (
                'enviar_email', 'enviar_sms', 'enviar_push', 'mostrar_dashboard'
            )
        }),
        ('Estado y Programación', {
            'fields': (
                'estado', 'fecha_programada', 'fecha_enviada',
                'fecha_vencimiento'
            )
        }),
        ('Control de Errores', {
            'fields': ('reintentos', 'max_reintentos', 'error_mensaje'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('metadatos', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marcar_como_enviada', 'reintentar_envio', 'marcar_como_ignorada']
    
    def titulo_corto(self, obj):
        """Título truncado"""
        return obj.titulo[:50] + '...' if len(obj.titulo) > 50 else obj.titulo
    titulo_corto.short_description = 'Título'
    
    def cuña_codigo(self, obj):
        """Código de la cuña si existe"""
        if obj.cuña:
            url = reverse('admin:content_management_cuñapublicitaria_change', args=[obj.cuña.pk])
            return format_html('<a href="{}">{}</a>', url, obj.cuña.codigo)
        return '-'
    cuña_codigo.short_description = 'Cuña'
    
    def severidad_visual(self, obj):
        """Severidad con colores"""
        colores = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colores.get(obj.severidad, 'black'),
            obj.get_severidad_display()
        )
    severidad_visual.short_description = 'Severidad'
    
    def estado_visual(self, obj):
        """Estado con íconos"""
        iconos = {
            'pendiente': '⏳',
            'enviada': '✅',
            'error': '❌',
            'ignorada': '🚫'
        }
        return format_html(
            '{} {}',
            iconos.get(obj.estado, '❓'),
            obj.get_estado_display()
        )
    estado_visual.short_description = 'Estado'
    
    def canales_envio(self, obj):
        """Muestra los canales de envío activos"""
        canales = []
        if obj.enviar_email:
            canales.append('📧')
        if obj.enviar_sms:
            canales.append('📱')
        if obj.enviar_push:
            canales.append('🔔')
        if obj.mostrar_dashboard:
            canales.append('📊')
        
        return format_html(' '.join(canales)) if canales else '-'
    canales_envio.short_description = 'Canales'
    
    def marcar_como_enviada(self, request, queryset):
        """Marca alertas como enviadas"""
        updated = 0
        for alerta in queryset:
            if alerta.estado in ['pendiente', 'error']:
                alerta.marcar_como_enviada()
                updated += 1
        
        self.message_user(
            request,
            f'Se marcaron {updated} alertas como enviadas.',
            messages.SUCCESS
        )
    marcar_como_enviada.short_description = 'Marcar como enviadas'
    
    def reintentar_envio(self, request, queryset):
        """Reinicia el envío de alertas con error"""
        updated = 0
        for alerta in queryset.filter(estado='error'):
            if alerta.puede_reintentarse:
                alerta.estado = 'pendiente'
                alerta.fecha_programada = timezone.now() + timedelta(minutes=5)
                alerta.save()
                updated += 1
        
        self.message_user(
            request,
            f'Se programaron {updated} alertas para reintento.',
            messages.SUCCESS
        )
    reintentar_envio.short_description = 'Reintentar envío'
    
    def marcar_como_ignorada(self, request, queryset):
        """Marca alertas como ignoradas"""
        updated = queryset.update(estado='ignorada')
        
        self.message_user(
            request,
            f'Se marcaron {updated} alertas como ignoradas.',
            messages.SUCCESS
        )
    marcar_como_ignorada.short_description = 'Marcar como ignoradas'


@admin.register(ResumenEstadosSemaforo)
class ResumenEstadosSemaforoAdmin(admin.ModelAdmin):
    list_display = [
        'fecha', 'periodo', 'total_cuñas', 'distribucion_visual',
        'porcentaje_problemas', 'alertas_generadas', 'cambios_estado'
    ]
    list_filter = ['periodo', 'fecha', 'configuracion_utilizada']
    search_fields = ['fecha']
    readonly_fields = [
        'total_cuñas', 'cuñas_verde', 'cuñas_amarillo', 'cuñas_rojo', 'cuñas_gris',
        'porcentaje_verde', 'porcentaje_problemas', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'fecha'
    
    def distribucion_visual(self, obj):
        """Muestra la distribución de colores visualmente"""
        if obj.total_cuñas == 0:
            return '-'
        
        return format_html(
            '🟢{} 🟡{} 🔴{} ⚫{}',
            obj.cuñas_verde,
            obj.cuñas_amarillo,
            obj.cuñas_rojo,
            obj.cuñas_gris
        )
    distribucion_visual.short_description = 'Distribución'


# Configuración general del admin
admin.site.site_header = 'PubliTrack - Sistema de Semáforos'
admin.site.site_title = 'Administración de Semáforos'
admin.site.index_title = 'Gestión del Sistema de Semáforos'