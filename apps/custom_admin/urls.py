from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Usuarios
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
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
    path('categorias/api/<int:categoria_id>/', views.categoria_detail_api, name='categoria_detail_api'),
    path('categorias/api/create/', views.categoria_create_api, name='categoria_create_api'),
    path('categorias/api/<int:pk>/update/', views.categoria_update_api, name='categoria_update_api'),
    path('categorias/api/<int:pk>/delete/', views.categoria_delete_api, name='categoria_delete_api'),
    
    # Contratos
    path('contratos/', views.contratos_generados_list, name='contratos_list'),
    path('contratos/api/create/', views.contrato_create_api, name='contrato_create_api'),
    path('contratos/api/<int:pk>/', views.contrato_detail_api, name='contrato_detail_api'),
    path('contratos/api/<int:pk>/update/', views.contrato_update_api, name='contrato_update_api'),
    
    # ==================== CONTRATOS GENERADOS ====================
    path('contratos-generados/', views.contratos_generados_list, name='contratos_generados_list'),
    path('contratos/api/generar/', views.contrato_generar_api, name='contrato_generar_api'),
    path('contratos/api/<int:id>/eliminar/', views.contrato_eliminar_api, name='contrato_eliminar_api'),
    path('contratos/api/<int:id>/subir-validado/', views.contrato_subir_validado_api, name='contrato_subir_validado_api'),
    
    # ==================== APIs PARA OBTENER DATOS ====================
    path('api/plantillas-contrato/', views.api_plantillas_contrato, name='api_plantillas_contrato'),
    path('api/clientes-activos/', views.api_clientes_activos, name='api_clientes_activos'),
    path('api/plantilla/<int:id>/detalle/', views.api_plantilla_detalle, name='api_plantilla_detalle'),
    path('api/cliente/<int:id>/detalle/', views.api_cliente_detalle, name='api_cliente_detalle'),
    
    # ==================== NUEVAS URLs PARA ÓRDENES ====================
    path('ordenes-toma/', views.ordenes_toma_list, name='ordenes_toma_list'),
    path('ordenes-produccion/', views.ordenes_produccion_list, name='ordenes_produccion_list'),
    path('ordenes-finalizacion/', views.ordenes_finalizacion_list, name='ordenes_finalizacion_list'),
    
    # APIs para órdenes
    path('api/ordenes-toma/', views.api_ordenes_toma, name='api_ordenes_toma'),
    path('api/ordenes-produccion/', views.api_ordenes_produccion, name='api_ordenes_produccion'),
    path('api/ordenes-finalizacion/', views.api_ordenes_finalizacion, name='api_ordenes_finalizacion'),
    
    # ==================== NUEVAS URLs PARA PANTEONES ====================
    path('panteones/', views.panteones_list, name='panteones_list'),
    path('api/panteones/', views.api_panteones, name='api_panteones'),
    
    # Transmisiones
    path('transmisiones/', views.transmisiones_list, name='transmisiones_list'),
    path('transmisiones/api/programacion/', views.programacion_list_api, name='programacion_list_api'),
    path('transmisiones/api/programacion/create/', views.programacion_create_api, name='programacion_create_api'),
    
    # ==================== PLANTILLAS DE CONTRATO ====================
    path('plantillas-contrato/', views.plantillas_contrato_list, name='plantillas_contrato_list'),
    path('plantillas-contrato/api/crear/', views.plantilla_contrato_crear_api, name='plantilla_contrato_crear_api'),
    path('plantillas-contrato/api/<int:id>/', views.plantilla_contrato_detalle_api, name='plantilla_contrato_detalle_api'),
    path('plantillas-contrato/api/<int:id>/actualizar/', views.plantilla_contrato_actualizar_api, name='plantilla_contrato_actualizar_api'),
    path('plantillas-contrato/api/<int:id>/eliminar/', views.plantilla_contrato_eliminar_api, name='plantilla_contrato_eliminar_api'),
    path('plantillas-contrato/api/<int:id>/marcar-default/', views.plantilla_contrato_marcar_default_api, name='plantilla_contrato_marcar_default_api'),
    path('plantillas-contrato/api/<int:id>/descargar/', views.plantilla_contrato_descargar_api, name='plantilla_contrato_descargar_api'),
 
    # Semáforos
    path('semaforos/', views.semaforos_list, name='semaforos_list'),
    path('semaforos/api/estados/', views.semaforos_estados_api, name='semaforos_estados_api'),
    path('semaforos/api/<int:estado_id>/', views.semaforo_detail_api, name='semaforo_detail_api'),
    path('semaforos/api/<int:estado_id>/recalcular/', views.semaforo_recalcular_api, name='semaforo_recalcular_api'),
    path('semaforos/configuracion/', views.configuracion_semaforos, name='configuracion_semaforos'),
    
    # Reportes
    path('reportes/', views.reportes_dashboard, name='reportes_dashboard'),
    
    # Configuración
    path('configuracion/', views.configuracion, name='configuracion'),

    # ==================== NUEVAS URLs PARA ÓRDENES ====================
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<int:order_id>/detalle/', views.order_detail_api, name='order_detail_api'),
    path('orders/crear/', views.order_create_api, name='order_create_api'),
    path('orders/<int:order_id>/editar/', views.order_update_api, name='order_update_api'),
    path('orders/<int:order_id>/eliminar/', views.order_delete_api, name='order_delete_api'),
    
    # ==================== NUEVAS URLs PARA PARTE MORTORIOS ====================
    path('parte-mortorios/', views.parte_mortorios_list, name='parte_mortorios_list'),
    path('parte-mortorios/<int:parte_id>/detalle/', views.parte_mortorio_detail_api, name='parte_mortorio_detail_api'),
    path('parte-mortorios/crear/', views.parte_mortorio_create_api, name='parte_mortorio_create_api'),
    path('parte-mortorios/<int:parte_id>/editar/', views.parte_mortorio_update_api, name='parte_mortorio_update_api'),
    path('parte-mortorios/<int:parte_id>/eliminar/', views.parte_mortorio_delete_api, name='parte_mortorio_delete_api'),

]