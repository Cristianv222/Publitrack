"""
URLs para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Rutas para cuñas publicitarias, archivos de audio y CONTRATOS
"""

from django.urls import path, include
from . import views

app_name = 'content_management'

# Patrones de URL principales
urlpatterns = [
    
    # ==================== DASHBOARD ====================
    path('', views.dashboard_content, name='dashboard'),
    
    # ==================== CATEGORIAS PUBLICITARIAS ====================
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/nueva/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='categoria_detail'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.categoria_delete, name='categoria_delete'),
    
    # ==================== TIPOS DE CONTRATO ====================
    path('tipos-contrato/', views.TipoContratoListView.as_view(), name='tipo_contrato_list'),
    path('tipos-contrato/nuevo/', views.TipoContratoCreateView.as_view(), name='tipo_contrato_create'),
    path('tipos-contrato/<int:pk>/editar/', views.TipoContratoUpdateView.as_view(), name='tipo_contrato_update'),
    
    # ==================== ARCHIVOS DE AUDIO ====================
    path('audios/', views.ArchivoAudioListView.as_view(), name='audio_list'),
    path('audios/subir/', views.ArchivoAudioCreateView.as_view(), name='audio_create'),
    path('audios/<int:pk>/', views.ArchivoAudioDetailView.as_view(), name='audio_detail'),
    path('audios/<int:pk>/eliminar/', views.audio_delete, name='audio_delete'),
    
    # ==================== CUÑAS PUBLICITARIAS ====================
    path('cuñas/', views.CuñaListView.as_view(), name='cuña_list'),
    path('cuñas/nueva/', views.CuñaCreateView.as_view(), name='cuña_create'),
    path('cuñas/<int:pk>/', views.CuñaDetailView.as_view(), name='cuña_detail'),
    path('cuñas/<int:pk>/editar/', views.CuñaUpdateView.as_view(), name='cuña_update'),
    
    # ==================== ACCIONES DE CUÑAS ====================
    path('cuñas/<int:pk>/aprobar/', views.cuña_aprobar, name='cuña_aprobar'),
    path('cuñas/<int:pk>/activar/', views.cuña_activar, name='cuña_activar'),
    path('cuñas/<int:pk>/pausar/', views.cuña_pausar, name='cuña_pausar'),
    path('cuñas/<int:pk>/finalizar/', views.cuña_finalizar, name='cuña_finalizar'),
    
    # ==================== PLANTILLAS DE CONTRATO ====================
    path('plantillas-contrato/', views.PlantillaContratoListView.as_view(), name='plantilla_contrato_list'),
    path('plantillas-contrato/nueva/', views.PlantillaContratoCreateView.as_view(), name='plantilla_contrato_create'),
    path('plantillas-contrato/<int:pk>/', views.PlantillaContratoDetailView.as_view(), name='plantilla_contrato_detail'),
    path('plantillas-contrato/<int:pk>/editar/', views.PlantillaContratoUpdateView.as_view(), name='plantilla_contrato_update'),
    path('plantillas-contrato/<int:pk>/eliminar/', views.plantilla_contrato_delete, name='plantilla_contrato_delete'),
    
    # ==================== CONTRATOS GENERADOS ====================
    path('contratos/', views.ContratoGeneradoListView.as_view(), name='contrato_list'),
    path('contratos/<int:pk>/', views.ContratoGeneradoDetailView.as_view(), name='contrato_detail'),
    path('contratos/generar/<int:cuña_id>/', views.generar_contrato, name='generar_contrato'),
    path('contratos/<int:pk>/regenerar/', views.regenerar_contrato, name='regenerar_contrato'),
    path('contratos/<int:pk>/descargar/', views.descargar_contrato, name='descargar_contrato'),
    
    # ==================== ACCIONES DE CONTRATOS ====================
    path('contratos/<int:pk>/marcar-enviado/', views.contrato_marcar_enviado, name='contrato_marcar_enviado'),
    path('contratos/<int:pk>/marcar-firmado/', views.contrato_marcar_firmado, name='contrato_marcar_firmado'),
    path('contratos/<int:pk>/activar/', views.contrato_activar, name='contrato_activar'),
    
    # ==================== VISTAS AJAX ====================
    path('ajax/', include([
        path('cuña/<int:pk>/estado/', views.cuña_estado_ajax, name='cuña_estado_ajax'),
        path('audio/<int:pk>/metadatos/', views.audio_metadatos_ajax, name='audio_metadatos_ajax'),
        path('estadisticas/dashboard/', views.estadisticas_dashboard_ajax, name='estadisticas_dashboard_ajax'),
    ])),
    
    # ==================== REPORTES ====================
    path('reportes/', include([
        path('cuñas/', views.reporte_cuñas, name='reporte_cuñas'),
        path('contratos/', views.reporte_contratos, name='reporte_contratos'),
    ])),
    
    # ==================== HISTORIAL ====================
    path('historial/', views.HistorialCuñaListView.as_view(), name='historial_list'),
]