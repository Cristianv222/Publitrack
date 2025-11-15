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
    path('reportes/', views.reports_dashboard_principal, name='reportes_dashboard'),
    # Configuración
    path('configuracion/', views.configuracion, name='configuracion'),
    # ==================== NUEVAS URLs PARA PARTE MORTORIOS ====================
    # ==================== ÓRDENES DE TOMA ====================
path('orders/', views.orders_list, name='orders_list'),
path('orders/<int:order_id>/detalle/', views.order_detail_api, name='order_detail_api'),
path('orders/crear/', views.order_create_api, name='order_create_api'),
path('orders/<int:order_id>/editar/', views.order_update_api, name='order_update_api'),
path('orders/<int:order_id>/eliminar/', views.order_delete_api, name='order_delete_api'),
# ==================== URLs PARA ÓRDENES ====================
path('orders/plantillas/', views.plantillas_orden_list, name='plantillas_orden_list'),
path('orders/plantillas/crear/', views.plantilla_orden_crear_api, name='plantilla_orden_crear_api'),

path('orders/<int:orden_toma_id>/generar/', views.orden_generar_api, name='orden_generar_api'),
path('orders/<int:orden_toma_id>/completar-generar/', views.orden_completar_y_generar_api, name='orden_completar_y_generar_api'),
path('orders/generadas/<int:orden_generada_id>/subir-validada/', views.orden_subir_validada_api, name='orden_subir_validada_api'),
path('orders/generadas/<int:orden_generada_id>/descargar/', views.orden_descargar_api, name='orden_descargar_api'),
# ==================== URLs PARA PLANTILLAS DE ORDEN ====================
path('plantillas-orden/', views.plantillas_orden_list, name='plantillas_orden_list'),
path('plantillas-orden/api/crear/', views.plantilla_orden_crear_api, name='plantilla_orden_crear_api'),
path('plantillas-orden/api/<int:id>/', views.plantilla_orden_detalle_api, name='plantilla_orden_detalle_api'),
path('plantillas-orden/api/<int:id>/actualizar/', views.plantilla_orden_actualizar_api, name='plantilla_orden_actualizar_api'),
path('plantillas-orden/api/<int:id>/eliminar/', views.plantilla_orden_eliminar_api, name='plantilla_orden_eliminar_api'),
path('plantillas-orden/api/<int:id>/marcar-default/', views.plantilla_orden_marcar_default_api, name='plantilla_orden_marcar_default_api'),
path('plantillas-orden/api/<int:id>/descargar/', views.plantilla_orden_descargar_api, name='plantilla_orden_descargar_api'),
# Agregar estas URLs en custom_admin/urls.py

# ==================== URLs PARA ÓRDENES GENERADAS ====================
path('orders/generadas/<int:orden_generada_id>/verificar/', views.orden_verificar_api, name='orden_verificar_api'),
path('orders/generadas/<int:orden_generada_id>/subir-validada/', views.orden_subir_validada_api, name='orden_subir_validada_api'),
path('orders/<int:orden_toma_id>/generar/', views.orden_generar_api, name='orden_generar_api'),
path('plantillas-orden/api/', views.api_plantillas_orden, name='api_plantillas_orden'),
# ==================== URLs PARA ÓRDENES DE PRODUCCIÓN ====================
path('ordenes-produccion/', views.ordenes_produccion_list, name='ordenes_produccion_list'),
path('ordenes-produccion/<int:order_id>/detalle/', views.orden_produccion_detail_api, name='orden_produccion_detail_api'),
path('ordenes-produccion/crear/', views.orden_produccion_create_api, name='orden_produccion_create_api'),
path('ordenes-produccion/<int:order_id>/editar/', views.orden_produccion_update_api, name='orden_produccion_update_api'),
path('ordenes-produccion/<int:order_id>/eliminar/', views.orden_produccion_delete_api, name='orden_produccion_delete_api'),
path('ordenes-produccion/<int:order_id>/iniciar/', views.orden_produccion_iniciar_api, name='orden_produccion_iniciar_api'),
path('ordenes-produccion/<int:order_id>/completar/', views.orden_produccion_completar_api, name='orden_produccion_completar_api'),
path('ordenes-produccion/<int:order_id>/validar/', views.orden_produccion_validar_api, name='orden_produccion_validar_api'),
path('ordenes-produccion/<int:order_id>/generar/', views.orden_produccion_generar_api, name='orden_produccion_generar_api'),
path('ordenes-produccion/<int:order_id>/subir-firmada/', views.orden_produccion_subir_firmada_api, name='orden_produccion_subir_firmada_api'),
path('ordenes-produccion/<int:order_id>/descargar-plantilla/', views.orden_produccion_descargar_plantilla_api, name='orden_produccion_descargar_plantilla_api'),
path('ordenes-produccion/<int:order_id>/plantillas/', views.orden_produccion_obtener_plantillas_api, name='orden_produccion_obtener_plantillas_api'),
# ==================== URLs PARA PARTE MORTORIOS ====================
path('parte-mortorios/', views.parte_mortorios_list, name='parte_mortorios_list'),
path('parte-mortorios/<int:parte_id>/detalle/', views.parte_mortorio_detail_api, name='parte_mortorio_detail_api'),
path('parte-mortorios/crear/', views.parte_mortorio_create_api, name='parte_mortorio_create_api'),
path('parte-mortorios/<int:parte_id>/editar/', views.parte_mortorio_update_api, name='parte_mortorio_update_api'),
path('parte-mortorios/<int:parte_id>/eliminar/', views.parte_mortorio_delete_api, name='parte_mortorio_delete_api'),
path('parte-mortorios/<int:parte_id>/programar/', views.parte_mortorio_programar_api, name='parte_mortorio_programar_api'),
path('parte-mortorios/<int:parte_id>/marcar-transmitido/', views.parte_mortorio_marcar_transmitido_api, name='parte_mortorio_marcar_transmitido_api'),
path('parte-mortorios/<int:parte_id>/cancelar/', views.parte_mortorio_cancelar_api, name='parte_mortorio_cancelar_api'),
# ==================== URLs PARA PLANTILLAS DE PARTE MORTORIO ====================
path('parte-mortorios/plantillas/', views.plantillas_parte_mortorio_list, name='plantillas_parte_mortorio_list'),
path('parte-mortorios/plantillas/api/crear/', views.plantilla_parte_mortorio_crear_api, name='plantilla_parte_mortorio_crear_api'),
path('parte-mortorios/plantillas/api/<int:id>/', views.plantilla_parte_mortorio_detalle_api, name='plantilla_parte_mortorio_detalle_api'),
path('parte-mortorios/plantillas/api/<int:id>/actualizar/', views.plantilla_parte_mortorio_actualizar_api, name='plantilla_parte_mortorio_actualizar_api'),
path('parte-mortorios/plantillas/api/<int:id>/eliminar/', views.plantilla_parte_mortorio_eliminar_api, name='plantilla_parte_mortorio_eliminar_api'),
path('parte-mortorios/plantillas/api/<int:id>/marcar-default/', views.plantilla_parte_mortorio_marcar_default_api, name='plantilla_parte_mortorio_marcar_default_api'),
path('parte-mortorios/plantillas/api/<int:id>/descargar/', views.plantilla_parte_mortorio_descargar_api, name='plantilla_parte_mortorio_descargar_api'),

# ==================== URLs PARA GENERAR PARTES MORTORIOS ====================
path('parte-mortorios/api/plantillas/', views.api_plantillas_parte_mortorio, name='api_plantillas_parte_mortorio'),
path('parte-mortorios/<int:parte_id>/generar/', views.parte_mortorio_generar_api, name='parte_mortorio_generar_api'),
path('parte-mortorios/generados/<int:parte_generado_id>/verificar/', views.parte_mortorio_verificar_api, name='parte_mortorio_verificar_api'),
path('parte-mortorios/generados/<int:parte_generado_id>/descargar/', views.parte_mortorio_descargar_api, name='parte_mortorio_descargar_api'),
path('parte-mortorios/<int:parte_id>/cambiar-estado/', views.parte_mortorio_cambiar_estado_api, name='parte_mortorio_cambiar_estado'),
# ==================== REPORTES DE CONTRATOS ====================
    path('reports/contratos/dashboard/', views.reports_dashboard_contratos, name='reports_dashboard_contratos'),
    path('reports/contratos/api/estadisticas/', views.reports_api_estadisticas_contratos, name='reports_api_estadisticas_contratos'),
    path('reports/contratos/estado/', views.reports_estado_contratos, name='reports_estado_contratos'),
    path('reports/contratos/vencimiento/', views.reports_vencimiento_contratos, name='reports_vencimiento_contratos'),
    path('reports/contratos/ingresos/', views.reports_ingresos_contratos, name='reports_ingresos_contratos'),
# ==================== REPORTES DE VENDEDORES ====================
path('reports/vendedores/dashboard/', views.reports_dashboard_vendedores, name='reports_dashboard_vendedores'),
path('reports/vendedores/<int:vendedor_id>/detalle/', views.reports_detalle_vendedor, name='reports_detalle_vendedor'),
# Detalles de contratos por cliente/vendedor
path('clientes/<int:cliente_id>/contratos/', views.cliente_contratos_api, name='cliente_contratos_api'),
path('vendedores/<int:vendedor_id>/contratos/', views.vendedor_contratos_api, name='vendedor_contratos_api'),
# ==================== REPORTES DE PARTES MORTUORIOS ====================
path('reports/partes-mortuorios/dashboard/', views.reports_dashboard_partes_mortuorios, name='reports_dashboard_partes_mortuorios'),
path('reports/partes-mortuorios/api/estado/', views.reports_partes_estado_api, name='reports_partes_estado_api'),
path('reports/partes-mortuorios/api/urgencia/', views.reports_partes_urgencia_api, name='reports_partes_urgencia_api'),
path('reports/partes-mortuorios/api/ingresos/', views.reports_partes_ingresos_api, name='reports_partes_ingresos_api'),
path('reports/partes-mortuorios/api/<int:parte_id>/detalle/', views.reports_partes_detalle_api, name='reports_partes_detalle_api'),
path('reports/partes-mortuorios/dashboard/', views.reports_dashboard_partes_mortuorios, name='reports_dashboard_partes_mortuorios'),
]