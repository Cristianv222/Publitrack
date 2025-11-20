from django.contrib import admin
from .models import Programa, ProgramacionSemanal, BloqueProgramacion, CategoriaPrograma

@admin.register(CategoriaPrograma)
class CategoriaProgramaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'color', 'estado', 'orden', 'programas_count']
    list_filter = ['estado']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['created_at', 'updated_at']
    
    def programas_count(self, obj):
        return obj.programas.count()
    programas_count.short_description = 'Nº Programas'

@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'duracion_estandar', 'estado']
    list_filter = ['categoria', 'estado', 'es_serie']
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