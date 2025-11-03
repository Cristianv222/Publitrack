"""
URLs del módulo de Órdenes
NOTA: Actualmente no se usa porque las URLs están en custom_admin
"""

from django.urls import path
from apps.custom_admin import views

app_name = 'orders'

urlpatterns = [
    # Lista de órdenes
    path('', views.orders_list, name='list'),
    
    # APIs CRUD
    path('<int:order_id>/detalle/', views.order_detail_api, name='detail_api'),
    path('crear/', views.order_create_api, name='create_api'),
    path('<int:order_id>/editar/', views.order_update_api, name='update_api'),
    path('<int:order_id>/eliminar/', views.order_delete_api, name='delete_api'),
]