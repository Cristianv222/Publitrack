"""
URLs para el Sistema de Semáforos
Sistema PubliTrack - Rutas y patrones de URL
"""

from django.urls import path, include
from . import views

app_name = 'traffic_light'

# URLs principales
urlpatterns = [
    # Dashboard principal
    path('', views.DashboardSemaforoView.as_view(), name='dashboard'),
    
    # Gestión de Estados
    path('estados/', views.ListaEstadosView.as_view(), name='lista_estados'),
    path('estados/<int:pk>/', views.DetalleEstadoView.as_view(), name='detalle_estado'),
    
    # Configuraciones
    path('configuraciones/', views.ConfiguracionSemaforoListView.as_view(), name='configuraciones'),
    path('configuraciones/nueva/', views.ConfiguracionSemaforoCreateView.as_view(), name='nueva_configuracion'),
    path('configuraciones/<int:pk>/editar/', views.ConfiguracionSemaforoUpdateView.as_view(), name='editar_configuracion'),
    
    # Alertas
    path('alertas/', views.AlertasListView.as_view(), name='alertas'),
    
    # Historial
    path('historial/', views.HistorialEstadosView.as_view(), name='historial'),
    
    # Widgets para incluir en otras páginas
    path('widgets/estados/', views.WidgetEstadosView.as_view(), name='widget_estados'),
    path('widgets/alertas/', views.WidgetAlertasView.as_view(), name='widget_alertas'),
]

# URLs de API y acciones AJAX
api_patterns = [
    # Recálculo de estados
    path('api/recalcular/<int:cuña_id>/', views.recalcular_estado_cuña, name='api_recalcular_cuña'),
    path('api/recalcular-todos/', views.recalcular_todos_estados, name='api_recalcular_todos'),
    
    # Configuraciones
    path('api/activar-config/<int:config_id>/', views.activar_configuracion, name='api_activar_configuracion'),
    
    # Alertas
    path('api/generar-alertas/', views.generar_alertas, name='api_generar_alertas'),
    path('api/alerta/<int:alerta_id>/leida/', views.marcar_alerta_leida, name='api_marcar_alerta_leida'),
    
    # Estadísticas y datos
    path('api/estadisticas/', views.api_estadisticas_dashboard, name='api_estadisticas'),
    path('api/cuñas/<str:color>/', views.api_cuñas_por_estado, name='api_cuñas_por_estado'),
    
    # Exportación
    path('api/exportar/estados/', views.exportar_reporte_estados, name='api_exportar_estados'),
]

# Agregar las URLs de API al patrón principal
urlpatterns += api_patterns