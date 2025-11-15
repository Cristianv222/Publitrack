# apps/reports_analytics/admin.py
from django.contrib import admin
from .models import ReporteContratos, DashboardContratos, ReporteVendedores, ReportePartesMortuorios, DashboardPartesMortuorios

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

@admin.register(ReporteVendedores)
class ReporteVendedoresAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'fecha_inicio', 'fecha_fin', 'fecha_generacion', 'generado_por']
    list_filter = ['fecha_generacion']
    readonly_fields = ['fecha_generacion']
    search_fields = ['nombre']
@admin.register(ReportePartesMortuorios)
class ReportePartesMortuoriosAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_reporte', 'fecha_generacion', 'generado_por']
    list_filter = ['tipo_reporte', 'fecha_generacion']
    readonly_fields = ['fecha_generacion']
    search_fields = ['nombre']

@admin.register(DashboardPartesMortuorios)
class DashboardPartesMortuoriosAdmin(admin.ModelAdmin):
    list_display = ['fecha_actualizacion', 'total_partes', 'partes_programados', 'ingresos_totales']
    readonly_fields = ['fecha_actualizacion']