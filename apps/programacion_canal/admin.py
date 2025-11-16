from django.contrib import admin
from .models import Programa, ProgramacionSemanal, BloqueProgramacion

@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'tipo', 'duracion_estandar', 'estado']
    list_filter = ['tipo', 'estado', 'es_serie']
    search_fields = ['nombre', 'codigo', 'descripcion']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ProgramacionSemanal)
class ProgramacionSemanalAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'fecha_inicio_semana', 'fecha_fin_semana', 'estado', 'created_by']
    list_filter = ['estado', 'fecha_inicio_semana']
    search_fields = ['nombre', 'codigo']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(BloqueProgramacion)
class BloqueProgramacionAdmin(admin.ModelAdmin):
    list_display = ['get_dia_semana', 'hora_inicio', 'get_hora_fin', 'programa', 'programacion_semanal']
    list_filter = ['dia_semana', 'programacion_semanal', 'es_repeticion']
    search_fields = ['programa__nombre', 'programacion_semanal__nombre', 'notas']
    
    def get_dia_semana(self, obj):
        return obj.get_dia_semana_display()
    get_dia_semana.short_description = 'Día'
    
    def get_hora_fin(self, obj):
        return obj.hora_fin
    get_hora_fin.short_description = 'Hora Fin'