# ==================== VISTAS DE ÓRDENES ====================

@login_required
@user_passes_test(is_admin)
def orders_list(request):
    from apps.orders.models import OrdenToma
    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    prioridad_filter = request.GET.get('prioridad', '')
    ordenes = OrdenToma.objects.select_related('cliente', 'vendedor_asignado').all()
    # ...aplicar filtros igual...
    # ...paginación...
    context = {
        'ordenes': ordenes_paginadas,
        'total_ordenes': total_ordenes,
        'ordenes_generadas': ordenes_generadas,
        'ordenes_validadas': ordenes_validadas,
        'ordenes_completadas': ordenes_completadas,
        'search': search,
        'estado_filter': estado_filter,
        'prioridad_filter': prioridad_filter,
        'clientes': clientes,  # si usas formulario
    }
    return render(request, 'custom_admin/orders/list.html', context)


@login_required
@user_passes_test(is_admin)
def order_detail_api(request, order_id):
    """API para obtener detalle de orden"""
    try:
        from apps.orders.models import OrdenToma
        
        orden = get_object_or_404(OrdenToma, pk=order_id)
        
        return JsonResponse({
            'success': True,
            'orden': {
                'id': orden.id,
                'codigo': orden.codigo,
                'nombre_cliente': orden.nombre_cliente,
                'ruc_dni_cliente': orden.ruc_dni_cliente,
                'empresa_cliente': orden.empresa_cliente,
                'ciudad_cliente': orden.ciudad_cliente,
                'direccion_cliente': orden.direccion_cliente,
                'telefono_cliente': orden.telefono_cliente,
                'email_cliente': orden.email_cliente,
                'detalle_productos': orden.detalle_productos,
                'cantidad': orden.cantidad,
                'total': str(orden.total),
                'estado': orden.estado,
                'prioridad': orden.prioridad,
                'observaciones': orden.observaciones,
                'fecha_orden': orden.fecha_orden.strftime('%Y-%m-%d %H:%M:%S'),
                'vendedor': orden.vendedor_asignado.get_full_name() if orden.vendedor_asignado else None,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def order_create_api(request):
    """API para crear orden manualmente"""
    try:
        from apps.orders.models import OrdenToma
        
        data = json.loads(request.body)
        
        cliente_id = data.get('cliente_id')
        if not cliente_id:
            return JsonResponse({'success': False, 'error': 'Cliente requerido'}, status=400)
        
        cliente = get_object_or_404(CustomUser, pk=cliente_id, rol='cliente')
        
        orden = OrdenToma.objects.create(
            cliente=cliente,
            detalle_productos=data.get('detalle_productos', ''),
            cantidad=int(data.get('cantidad', 1)),
            total=Decimal(data.get('total', '0.00')),
            prioridad=data.get('prioridad', 'normal'),
            observaciones=data.get('observaciones', ''),
            created_by=request.user,
        )
        
        # Registrar en LogEntry
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=orden.codigo,
            action_flag=ADDITION,
            change_message=f'Orden creada manualmente'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden creada exitosamente',
            'orden_id': orden.id,
            'codigo': orden.codigo
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "POST"])
def order_update_api(request, order_id):
    """API para actualizar orden"""
    try:
        from apps.orders.models import OrdenToma
        
        orden = get_object_or_404(OrdenToma, pk=order_id)
        data = json.loads(request.body)
        
        # Actualizar campos
        orden.detalle_productos = data.get('detalle_productos', orden.detalle_productos)
        orden.cantidad = int(data.get('cantidad', orden.cantidad))
        orden.total = Decimal(data.get('total', orden.total))
        orden.prioridad = data.get('prioridad', orden.prioridad)
        orden.observaciones = data.get('observaciones', orden.observaciones)
        
        # Cambio de estado
        nuevo_estado = data.get('estado')
        if nuevo_estado and nuevo_estado != orden.estado:
            if nuevo_estado == 'validado':
                orden.validar(request.user)
            elif nuevo_estado == 'en_produccion':
                orden.enviar_a_produccion()
            elif nuevo_estado == 'completado':
                orden.completar(request.user)
            elif nuevo_estado == 'cancelado':
                orden.cancelar()
        else:
            orden.save()
        
        # Registrar en LogEntry
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=orden.codigo,
            action_flag=CHANGE,
            change_message=f'Orden actualizada'
        )
        
        return JsonResponse({'success': True, 'message': 'Orden actualizada exitosamente'})
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE", "POST"])
def order_delete_api(request, order_id):
    """API para eliminar orden"""
    try:
        from apps.orders.models import OrdenToma
        
        orden = get_object_or_404(OrdenToma, pk=order_id)
        codigo = orden.codigo
        
        # Registrar en LogEntry antes de eliminar
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=codigo,
            action_flag=DELETION,
            change_message=f'Orden eliminada'
        )
        
        orden.delete()
        
        return JsonResponse({'success': True, 'message': f'Orden {codigo} eliminada exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== VISTAS DE AUTORIZACIÓN ====================

@login_required
@user_passes_test(is_admin)
def ordenes_autorizacion_list(request):
    from apps.orders.models import OrdenAutorizacion
    from apps.authentication.models import CustomUser
    from django.db.models import Q
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    
    ordenes = OrdenAutorizacion.objects.select_related('cliente', 'vendedor').all()
    
    if search:
        ordenes = ordenes.filter(
            Q(codigo__icontains=search) |
            Q(nombre_cliente__icontains=search) |
            Q(empresa_cliente__icontains=search) |
            Q(campania__icontains=search)
        )
    
    if estado_filter:
        ordenes = ordenes.filter(estado=estado_filter)
        
    ordenes = ordenes.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(ordenes, 10)
    page = request.GET.get('page')
    try:
        ordenes_paginadas = paginator.page(page)
    except PageNotAnInteger:
        ordenes_paginadas = paginator.page(1)
    except EmptyPage:
        ordenes_paginadas = paginator.page(paginator.num_pages)

    context = {
        'ordenes': ordenes_paginadas,
        'search': search,
        'estado_filter': estado_filter,
        'clientes': CustomUser.objects.filter(rol='cliente', is_active=True),
        'vendedores': CustomUser.objects.filter(rol='vendedor', is_active=True)
    }
    return render(request, 'custom_admin/orders/autorizacion_list.html', context)


@login_required
@user_passes_test(is_admin)
def orden_autorizacion_detail_api(request, order_id):
    try:
        from apps.orders.models import OrdenAutorizacion
        orden = get_object_or_404(OrdenAutorizacion, pk=order_id)
        
        return JsonResponse({
            'success': True,
            'orden': {
                'id': orden.id,
                'codigo': orden.codigo,
                'cliente_id': orden.cliente.id,
                'nombre_cliente': orden.nombre_cliente,
                'campania': orden.campania,
                'detalle_transmision': orden.detalle_transmision,
                'fecha_inicio': orden.fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': orden.fecha_fin.strftime('%Y-%m-%d'),
                'vendedor_id': orden.vendedor.id if orden.vendedor else None,
                'valor_total': str(orden.valor_total),
                'estado': orden.estado,
                'observaciones': orden.observaciones
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_autorizacion_create_api(request):
    try:
        from apps.orders.models import OrdenAutorizacion
        from apps.authentication.models import CustomUser
        from decimal import Decimal
        
        data = json.loads(request.body)
        cliente = get_object_or_404(CustomUser, pk=data.get('cliente_id'))
        
        orden = OrdenAutorizacion.objects.create(
            cliente=cliente,
            campania=data.get('campania'),
            detalle_transmision=data.get('detalle_transmision'),
            fecha_inicio=data.get('fecha_inicio'),
            fecha_fin=data.get('fecha_fin'),
            vendedor_id=data.get('vendedor_id'),
            valor_total=Decimal(data.get('valor_total', '0.00')),
            observaciones=data.get('observaciones', ''),
            created_by=request.user
        )
        
        return JsonResponse({'success': True, 'message': 'Autorización creada', 'id': orden.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT"])
def orden_autorizacion_update_api(request, order_id):
    try:
        from apps.orders.models import OrdenAutorizacion
        from decimal import Decimal
        
        orden = get_object_or_404(OrdenAutorizacion, pk=order_id)
        data = json.loads(request.body)
        
        orden.campania = data.get('campania', orden.campania)
        orden.detalle_transmision = data.get('detalle_transmision', orden.detalle_transmision)
        orden.fecha_inicio = data.get('fecha_inicio', orden.fecha_inicio)
        orden.fecha_fin = data.get('fecha_fin', orden.fecha_fin)
        orden.valor_total = Decimal(data.get('valor_total', orden.valor_total))
        orden.observaciones = data.get('observaciones', orden.observaciones)
        
        if 'vendedor_id' in data:
            orden.vendedor_id = data.get('vendedor_id')
            
        if 'estado' in data:
            orden.estado = data.get('estado')
            
        orden.save()
        
        return JsonResponse({'success': True, 'message': 'Autorización actualizada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE", "POST"])
def orden_autorizacion_delete_api(request, order_id):
    try:
        from apps.orders.models import OrdenAutorizacion
        orden = get_object_or_404(OrdenAutorizacion, pk=order_id)
        orden.delete()
        return JsonResponse({'success': True, 'message': 'Orden eliminada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ==================== VISTAS DE SUSPENSIÓN ====================

@login_required
@user_passes_test(is_admin)
def ordenes_suspension_list(request):
    from apps.orders.models import OrdenSuspension
    from apps.authentication.models import CustomUser
    from django.db.models import Q
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    
    ordenes = OrdenSuspension.objects.select_related('cliente').all()
    
    if search:
        ordenes = ordenes.filter(
            Q(codigo__icontains=search) |
            Q(nombre_cliente__icontains=search) |
            Q(campania__icontains=search)
        )
    
    if estado_filter:
        ordenes = ordenes.filter(estado=estado_filter)
        
    ordenes = ordenes.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(ordenes, 10)
    page = request.GET.get('page')
    try:
        ordenes_paginadas = paginator.page(page)
    except PageNotAnInteger:
        ordenes_paginadas = paginator.page(1)
    except EmptyPage:
        ordenes_paginadas = paginator.page(paginator.num_pages)

    context = {
        'ordenes': ordenes_paginadas,
        'search': search,
        'estado_filter': estado_filter,
        'clientes': CustomUser.objects.filter(rol='cliente', is_active=True),
    }
    return render(request, 'custom_admin/orders/suspension_list.html', context)


@login_required
@user_passes_test(is_admin)
def orden_suspension_detail_api(request, order_id):
    try:
        from apps.orders.models import OrdenSuspension
        orden = get_object_or_404(OrdenSuspension, pk=order_id)
        
        return JsonResponse({
            'success': True,
            'orden': {
                'id': orden.id,
                'codigo': orden.codigo,
                'cliente_id': orden.cliente.id,
                'nombre_cliente': orden.nombre_cliente,
                'campania': orden.campania,
                'fecha_salida_aire': orden.fecha_salida_aire.strftime('%Y-%m-%d'),
                'motivo': orden.motivo,
                'estado': orden.estado,
                'autorizacion_relacionada_id': orden.autorizacion_relacionada.id if orden.autorizacion_relacionada else None
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_suspension_create_api(request):
    try:
        from apps.orders.models import OrdenSuspension
        from apps.authentication.models import CustomUser
        
        data = json.loads(request.body)
        cliente = get_object_or_404(CustomUser, pk=data.get('cliente_id'))
        
        orden = OrdenSuspension.objects.create(
            cliente=cliente,
            campania=data.get('campania'),
            fecha_salida_aire=data.get('fecha_salida_aire'),
            motivo=data.get('motivo', ''),
            autorizacion_relacionada_id=data.get('autorizacion_relacionada_id'),
            created_by=request.user
        )
        
        return JsonResponse({'success': True, 'message': 'Suspensión creada', 'id': orden.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT"])
def orden_suspension_update_api(request, order_id):
    try:
        from apps.orders.models import OrdenSuspension
        orden = get_object_or_404(OrdenSuspension, pk=order_id)
        data = json.loads(request.body)
        
        orden.campania = data.get('campania', orden.campania)
        orden.fecha_salida_aire = data.get('fecha_salida_aire', orden.fecha_salida_aire)
        orden.motivo = data.get('motivo', orden.motivo)
        
        if 'autorizacion_relacionada_id' in data:
            orden.autorizacion_relacionada_id = data.get('autorizacion_relacionada_id')
            
        if 'estado' in data:
            orden.estado = data.get('estado')
            
        orden.save()
        
        return JsonResponse({'success': True, 'message': 'Suspensión actualizada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE", "POST"])
def orden_suspension_delete_api(request, order_id):
    try:
        from apps.orders.models import OrdenSuspension
        orden = get_object_or_404(OrdenSuspension, pk=order_id)
        orden.delete()
        return JsonResponse({'success': True, 'message': 'Orden eliminada'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
