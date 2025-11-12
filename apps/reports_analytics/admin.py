# apps/reports_analytics/admin.py
from django.contrib import admin
from .models import ReporteContratos, DashboardContratos

@admin.register(ReporteContratos)
class ReporteContratosAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_reporte', 'fecha_generacion', 'generado_por']
    list_filter = ['tipo_reporte', 'fecha_generacion']
    readonly_fields = ['fecha_generacion']
    search_fields = ['nombre']

@admin.register(DashboardContratos)
class DashboardContratosAdmin(admin.ModelAdmin):
    list_display = ['fecha_actualizacion', 'total_contratos', 'contratos_activos', 'ingresos_totales']
    readonly_fields = ['fecha_actualizacion']