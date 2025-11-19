from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'authentication'

urlpatterns = [
    # ============================================================================
    # AUTENTICACIÓN BÁSICA
    # ============================================================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ============================================================================
    # GESTIÓN DE PERFILES
    # ============================================================================
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    
    # ============================================================================
    # GESTIÓN DE USUARIOS (SOLO ADMIN)
    # ============================================================================
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/register/', views.register_user_view, name='register_user'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # ============================================================================
    # DASHBOARD Y VENDEDORES
    # ============================================================================
    path('dashboard/admin/', lambda request: redirect('/panel/'), name='admin_dashboard'),
    path('dashboard/vendedor/', views.vendedor_dashboard, name='vendedor_dashboard'),
    path('dashboard/cliente/', views.cliente_dashboard, name='cliente_dashboard'),
    
    # ============================================================================
    # GESTIÓN DE CLIENTES PARA VENDEDORES
    # ============================================================================
    path('vendedor/clientes/crear/', views.vendedor_crear_cliente, name='vendedor_crear_cliente'),
    path('vendedor/clientes/<int:cliente_id>/editar/', views.vendedor_editar_cliente, name='vendedor_editar_cliente'),
    path('vendedor/clientes/<int:cliente_id>/detalle/', views.vendedor_detalle_cliente_api, name='vendedor_detalle_cliente_api'),
    
    # ============================================================================
    # GESTIÓN DE CONTRATOS PARA VENDEDORES
    # ============================================================================
    path('vendedor/contratos/crear/', views.vendedor_crear_contrato, name='vendedor_crear_contrato'),
    path('vendedor/api/plantillas/', views.vendedor_plantillas_api, name='vendedor_plantillas_api'),
    path('vendedor/api/plantilla/<int:plantilla_id>/detalle/', views.vendedor_plantilla_detalle_api, name='vendedor_plantilla_detalle_api'),
    
    # ============================================================================
    # REPORTES Y API
    # ============================================================================
    path('reports/', views.user_reports_view, name='user_reports'),
    path('api/stats/', views.user_stats_api, name='user_stats_api'),
]