from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Usuarios
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/crear/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_delete, name='usuario_delete'),
    
    # Cuñas
    path('cunas/', views.cunas_list, name='cunas_list'),
    path('cunas/crear/', views.cuna_create, name='cuna_create'),
    
    # Transmisiones
    path('transmisiones/', views.transmisiones_list, name='transmisiones_list'),
    
    # Semáforos
    path('semaforos/', views.semaforos_list, name='semaforos_list'),
    
    # Reportes
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    
    # Configuración
    path('configuracion/', views.configuracion, name='configuracion'),
]
