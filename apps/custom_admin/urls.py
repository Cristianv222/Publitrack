from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Usuarios
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    # path('usuarios/crear/', views.usuario_create, name='usuario_create'),  # Comentar
    # path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),  # Comentar
    # path('usuarios/<int:pk>/eliminar/', views.usuario_delete, name='usuario_delete'),  # Comentar
    
    # APIs de Usuarios (estas sí las necesitas)
    path('usuarios/api/<int:pk>/', views.usuario_detail_api, name='usuario_detail_api'),
    path('usuarios/api/crear/', views.usuario_create_api, name='usuario_create_api'),
    path('usuarios/api/<int:pk>/actualizar/', views.usuario_update_api, name='usuario_update_api'),
    path('usuarios/api/<int:pk>/eliminar/', views.usuario_delete_api, name='usuario_delete_api'),
    path('usuarios/api/<int:pk>/cambiar-password/', views.usuario_change_password_api, name='usuario_change_password_api'),
    
    # Gestión de Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/<int:cliente_id>/detalle/', views.cliente_detail_api, name='cliente_detail_api'),
    path('clientes/crear/', views.cliente_create_api, name='cliente_create_api'),
    path('clientes/<int:cliente_id>/editar/', views.cliente_update_api, name='cliente_update_api'),
    path('clientes/<int:cliente_id>/eliminar/', views.cliente_delete_api, name='cliente_delete_api'),
    
    # Grupos
    path('grupos/', views.grupos_list, name='grupos_list'),
    path('grupos/api/crear/', views.grupo_create_api, name='grupo_create_api'),
    path('grupos/api/<int:pk>/', views.grupo_update_api, name='grupo_update_api'),
    path('grupos/api/<int:pk>/eliminar/', views.grupo_delete_api, name='grupo_delete_api'),
    path('grupos/api/<int:pk>/usuarios/', views.grupo_usuarios_api, name='grupo_usuarios_api'),
    
    # HISTORIAL
    path('historial/', views.historial_list, name='historial_list'),
    
    # ============================
    # URLs DE CUÑAS PUBLICITARIAS
    # ============================
    path('cunas/', views.cunas_list, name='cunas_list'),
    path('cunas/api/<int:cuna_id>/', views.cunas_detail_api, name='cunas_detail_api'),
    path('cunas/api/crear/', views.cunas_create_api, name='cunas_create_api'),
    path('cunas/api/<int:cuna_id>/actualizar/', views.cunas_update_api, name='cunas_update_api'),
    path('cunas/api/<int:cuna_id>/eliminar/', views.cunas_delete_api, name='cunas_delete_api'),
    
    # Categorías
    path('categorias/', views.categorias_list, name='categorias_list'),
    path('categorias/api/<int:categoria_id>/', views.categoria_detail_api, name='categoria_detail_api'),  # ✅ AGREGAR ESTA LÍNEA
    path('categorias/api/create/', views.categoria_create_api, name='categoria_create_api'),
    path('categorias/api/<int:pk>/update/', views.categoria_update_api, name='categoria_update_api'),
    path('categorias/api/<int:pk>/delete/', views.categoria_delete_api, name='categoria_delete_api'),
    # Contratos
    path('contratos/', views.contratos_list, name='contratos_list'),
    path('contratos/api/create/', views.contrato_create_api, name='contrato_create_api'),
    path('contratos/api/<int:pk>/', views.contrato_detail_api, name='contrato_detail_api'),
    path('contratos/api/<int:pk>/update/', views.contrato_update_api, name='contrato_update_api'),
    
    # Transmisiones
    path('transmisiones/', views.transmisiones_list, name='transmisiones_list'),
    path('transmisiones/api/programacion/', views.programacion_list_api, name='programacion_list_api'),
    path('transmisiones/api/programacion/create/', views.programacion_create_api, name='programacion_create_api'),
    
    # Semáforos
    path('semaforos/', views.semaforos_list, name='semaforos_list'),
    path('semaforos/api/estados/', views.semaforos_estados_api, name='semaforos_estados_api'),
    path('semaforos/', views.semaforos_list, name='semaforos_list'),
path('semaforos/api/<int:estado_id>/', views.semaforo_detail_api, name='semaforo_detail_api'),
path('semaforos/api/<int:estado_id>/recalcular/', views.semaforo_recalcular_api, name='semaforo_recalcular_api'),
path('semaforos/configuracion/', views.configuracion_semaforos, name='configuracion_semaforos'),
    # Reportes
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    
    # Configuración
    path('configuracion/', views.configuracion, name='configuracion'),
]