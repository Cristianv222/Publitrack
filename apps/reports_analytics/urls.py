# apps/reports_analytics/urls.py
from django.urls import path
from . import views

app_name = 'reports_analytics'

urlpatterns = [
    path('dashboard-contratos/', views.dashboard_contratos, name='dashboard_contratos'),
    path('api/estadisticas-contratos/', views.api_estadisticas_contratos, name='api_estadisticas_contratos'),
    path('reporte/estado-contratos/', views.reporte_estado_contratos, name='reporte_estado_contratos'),
    path('reporte/vencimiento-contratos/', views.reporte_vencimiento_contratos, name='reporte_vencimiento_contratos'),
    path('reporte/ingresos-contratos/', views.reporte_ingresos_contratos, name='reporte_ingresos_contratos'),
]