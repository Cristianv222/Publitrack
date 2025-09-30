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

    # Grupos
    path('grupos/', views.grupos_list, name='grupos_list'),
    path('grupos/api/crear/', views.grupo_create_api, name='grupo_create_api'),
    path('grupos/api/<int:pk>/', views.grupo_update_api, name='grupo_update_api'),
    path('grupos/api/<int:pk>/eliminar/', views.grupo_delete_api, name='grupo_delete_api'),
    path('grupos/api/<int:pk>/usuarios/', views.grupo_usuarios_api, name='grupo_usuarios_api'),
    # HISTORIAL
    path('historial/', views.historial_list, name='historial_list'),
    # URLs de Cuñas
    path('cunas/', views.cunas_list, name='cunas_list'),
    path('cunas/crear/', views.cuna_create, name='cuna_create'),  # Mantener por compatibilidad
    path('cunas/<int:pk>/editar/', views.cuna_edit, name='cuna_edit'),  # Mantener por compatibilidad
    path('cunas/<int:pk>/detalle/', views.cuna_detail, name='cuna_detail'),  # Mantener por compatibilidad
    path('cunas/<int:pk>/eliminar/', views.cuna_delete, name='cuna_delete'),  # Mantener por compatibilidad

    # APIs de Cuñas
    path('cunas/api/<int:pk>/', views.cuna_detail_api, name='cuna_detail_api'),
    path('cunas/api/crear/', views.cuna_create_api, name='cuna_create_api'),
    path('cunas/api/<int:pk>/actualizar/', views.cuna_update_api, name='cuna_update_api'),
    path('cunas/api/<int:pk>/eliminar/', views.cuna_delete_api, name='cuna_delete_api'),
    # Categorías
    path('categorias/', views.categorias_list, name='categorias_list'),
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
    
    # Reportes
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    
    # Configuración
    path('configuracion/', views.configuracion, name='configuracion'),
]