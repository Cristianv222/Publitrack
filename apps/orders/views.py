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
