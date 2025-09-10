"""
URLs para el módulo de Control de Transmisiones
Sistema PubliTrack - Gestión y programación de transmisiones de publicidad radial
"""

from django.urls import path, include
from . import views

app_name = 'transmission_control'

# URLs principales del módulo
urlpatterns = [
    
    # ==================== DASHBOARD Y MONITOR ====================
    
    # Dashboard principal
    path('', views.dashboard_transmisiones, name='dashboard'),
    
    # Monitor en tiempo real
    path('monitor/', views.MonitorTiempoRealView.as_view(), name='monitor_tiempo_real'),
    
    # APIs para actualización en tiempo real
    path('api/estado-transmision/', views.api_estado_transmision, name='api_estado_transmision'),
    path('api/transmisiones-hoy/', views.api_transmisiones_hoy, name='api_transmisiones_hoy'),
    path('api/estadisticas-tiempo-real/', views.api_estadisticas_tiempo_real, name='api_estadisticas_tiempo_real'),
    
    
    # ==================== CONTROL MANUAL ====================
    
    # Controles de transmisión
    path('control/pausar/', views.pausar_transmision, name='pausar_transmision'),
    path('control/reanudar/', views.reanudar_transmision, name='reanudar_transmision'),
    path('control/detener/', views.detener_transmision, name='detener_transmision'),
    path('control/ajustar-volumen/', views.ajustar_volumen, name='ajustar_volumen'),
    
    
    # ==================== PROGRAMACIONES ====================
    
    # Lista y CRUD de programaciones
    path('programaciones/', views.ProgramacionListView.as_view(), name='programacion_list'),
    path('programaciones/<int:pk>/', views.ProgramacionDetailView.as_view(), name='programacion_detail'),
    path('programaciones/nueva/', views.ProgramacionCreateView.as_view(), name='programacion_create'),
    path('programaciones/<int:pk>/editar/', views.ProgramacionUpdateView.as_view(), name='programacion_edit'),
    
    # Acciones sobre programaciones
    path('programaciones/<int:pk>/activar/', views.activar_programacion, name='activar_programacion'),
    path('programaciones/<int:pk>/cancelar/', views.cancelar_programacion, name='cancelar_programacion'),
    
    
    # ==================== CALENDARIO ====================
    
    # Vistas de calendario
    path('calendario/', views.calendario_transmisiones, name='calendario_semanal'),
    path('calendario/mes/', views.calendario_mes, name='calendario_mensual'),
    
    
    # ==================== TRANSMISIONES ====================
    
    # Detalle de transmisión actual
    path('transmisiones/actual/', views.MonitorTiempoRealView.as_view(), name='transmision_actual'),
    
    
    # ==================== LOGS Y REPORTES ====================
    
    # Logs
    path('logs/', views.LogsListView.as_view(), name='logs_list'),
    path('logs/exportar/', views.exportar_logs, name='exportar_logs'),
    path('logs/limpiar/', views.limpiar_logs_antiguos, name='limpiar_logs'),
    
    # Reportes
    path('reportes/', views.reporte_transmisiones, name='reporte_transmisiones'),
    
    
    # ==================== CONFIGURACIÓN ====================
    
    # Configuración del sistema
    path('configuracion/', views.ConfiguracionUpdateView.as_view(), name='configuracion'),
    
]

# URLs adicionales para APIs específicas
api_patterns = [
    # APIs REST para integración externa
    path('status/', views.api_estado_transmision, name='api_status'),
    path('current/', views.api_estado_transmision, name='api_current'),
    path('today/', views.api_transmisiones_hoy, name='api_today'),
    path('stats/', views.api_estadisticas_tiempo_real, name='api_stats'),
]

# Incluir URLs de API con prefijo
urlpatterns += [
    path('api/', include((api_patterns, 'transmission_control'), namespace='api')),
]