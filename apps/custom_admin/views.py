from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from apps.content_management.models import CuñaPublicitaria, CategoriaPublicitaria, TipoContrato
from decimal import Decimal
from django.db.models.signals import post_save, pre_save

# Obtener el modelo de usuario correcto
User = get_user_model()

def is_admin(user):
    return user.is_superuser or user.is_staff or user.rol == 'admin'

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    try:
        total_cunas = CuñaPublicitaria.objects.count()
        cunas_activas = CuñaPublicitaria.objects.filter(estado='activa').count()
    except:
        total_cunas = 0
        cunas_activas = 0
    
    context = {
        'total_usuarios': User.objects.count(),
        'usuarios_activos': User.objects.filter(is_active=True).count(),
        'total_cunas': total_cunas,
        'cunas_activas': cunas_activas,
        'alertas_pendientes': 0,
    }
    return render(request, 'custom_admin/dashboard.html', context)

# ============= VISTAS DE USUARIOS (sin cambios) =============
@login_required
@user_passes_test(is_admin)
def usuarios_list(request):
    query = request.GET.get('q')
    usuarios = User.objects.all().order_by('-date_joined')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'usuarios': page_obj,
        'query': query,
    }
    return render(request, 'custom_admin/usuarios_list.html', context)

@login_required
@user_passes_test(is_admin)
def usuario_create(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            rol = request.POST.get('rol')
            is_active = request.POST.get('is_active') == 'on'
            is_staff = request.POST.get('is_staff') == 'on'
            is_superuser = request.POST.get('is_superuser') == 'on'
            
            telefono = request.POST.get('telefono')
            direccion = request.POST.get('direccion')
            empresa = request.POST.get('empresa')
            ruc_dni = request.POST.get('ruc_dni')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f'El usuario {username} ya existe')
                return render(request, 'custom_admin/usuario_form.html')
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            user.rol = rol
            user.is_active = is_active
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.telefono = telefono
            user.direccion = direccion
            
            if rol == 'admin':
                user.is_staff = True
            
            if rol == 'cliente':
                user.empresa = empresa
                user.ruc_dni = ruc_dni
            
            user.save()
            
            messages.success(request, f'Usuario {username} creado exitosamente como {user.get_rol_display()}')
            return redirect('custom_admin:usuarios_list')
            
        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
            return render(request, 'custom_admin/usuario_form.html')
    
    return render(request, 'custom_admin/usuario_form.html')

@login_required
@user_passes_test(is_admin)
def usuario_edit(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        try:
            usuario.username = request.POST.get('username', usuario.username)
            usuario.email = request.POST.get('email', usuario.email)
            usuario.first_name = request.POST.get('first_name', usuario.first_name)
            usuario.last_name = request.POST.get('last_name', usuario.last_name)
            usuario.rol = request.POST.get('rol', usuario.rol)
            usuario.is_active = request.POST.get('is_active') == 'on'
            usuario.is_staff = request.POST.get('is_staff') == 'on'
            usuario.is_superuser = request.POST.get('is_superuser') == 'on'
            
            usuario.telefono = request.POST.get('telefono', usuario.telefono)
            usuario.direccion = request.POST.get('direccion', usuario.direccion)
            
            if usuario.rol == 'admin':
                usuario.is_staff = True
            
            if usuario.rol == 'cliente':
                usuario.empresa = request.POST.get('empresa', usuario.empresa)
                usuario.ruc_dni = request.POST.get('ruc_dni', usuario.ruc_dni)
            
            new_password = request.POST.get('password')
            if new_password:
                usuario.set_password(new_password)
            
            usuario.save()
            
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente')
            return redirect('custom_admin:usuarios_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
    
    context = {'usuario': usuario}
    return render(request, 'custom_admin/usuario_form.html', context)

@login_required
@user_passes_test(is_admin)
def usuario_delete(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        try:
            username = usuario.username
            usuario.delete()
            messages.success(request, f'Usuario {username} eliminado exitosamente')
            return redirect('custom_admin:usuarios_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar usuario: {str(e)}')
    
    context = {'usuario': usuario}
    return render(request, 'custom_admin/usuario_confirm_delete.html', context)

# ============= VISTAS DE CUÑAS =============
@login_required
@user_passes_test(is_admin)
def cunas_list(request):
    query = request.GET.get('q')
    estado = request.GET.get('estado')
    cliente = request.GET.get('cliente')
    
    cunas = CuñaPublicitaria.objects.all().order_by('-created_at')
    
    # Filtros
    if query:
        cunas = cunas.filter(
            Q(titulo__icontains=query) |
            Q(codigo__icontains=query) |
            Q(cliente__empresa__icontains=query)
        )
    
    if estado:
        cunas = cunas.filter(estado=estado)
    
    if cliente:
        cunas = cunas.filter(cliente__id=cliente)
    
    # Paginación
    paginator = Paginator(cunas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener datos para los filtros
    estados = [
        ('borrador', 'Borrador'),
        ('pendiente_revision', 'Pendiente de Revisión'),
        ('en_produccion', 'En Producción'),
        ('aprobada', 'Aprobada'),
        ('activa', 'Activa'),
        ('pausada', 'Pausada'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    clientes = User.objects.filter(rol='cliente')
    
    context = {
        'cunas': page_obj,
        'query': query,
        'estados': estados,
        'clientes': clientes,
        'estado_seleccionado': estado,
        'cliente_seleccionado': cliente,
    }
    return render(request, 'custom_admin/cunas/list.html', context)

@login_required
@user_passes_test(is_admin)
def cuna_create(request):
    if request.method == 'POST':
        try:
            # Desconectar temporalmente las señales para evitar el error del historial
            from apps.content_management.models import cuña_pre_save, cuña_post_save
            pre_save.disconnect(cuña_pre_save, sender=CuñaPublicitaria)
            post_save.disconnect(cuña_post_save, sender=CuñaPublicitaria)
            
            # Obtener datos del formulario
            titulo = request.POST.get('titulo', '').strip()
            descripcion = request.POST.get('descripcion', '')
            cliente_id = request.POST.get('cliente')
            vendedor_id = request.POST.get('vendedor')
            categoria_id = request.POST.get('categoria')
            tipo_contrato_id = request.POST.get('tipo_contrato')
            duracion_planeada = request.POST.get('duracion_planeada', '30')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            repeticiones_dia = request.POST.get('repeticiones_dia', '1')
            precio_total_str = request.POST.get('precio_total', '0')
            observaciones = request.POST.get('observaciones', '')
            
            # Convertir y validar valores
            try:
                duracion_planeada = int(duracion_planeada)
            except:
                duracion_planeada = 30
                
            try:
                repeticiones_dia = int(repeticiones_dia)
            except:
                repeticiones_dia = 1
                
            try:
                precio_total = Decimal(precio_total_str)
            except:
                precio_total = Decimal('0')
            
            # Crear la cuña
            cuna = CuñaPublicitaria(
                titulo=titulo,
                descripcion=descripcion,
                cliente_id=cliente_id,
                vendedor_asignado_id=vendedor_id if vendedor_id else None,
                categoria_id=categoria_id if categoria_id else None,
                tipo_contrato_id=tipo_contrato_id if tipo_contrato_id else None,
                duracion_planeada=duracion_planeada,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                repeticiones_dia=repeticiones_dia,
                precio_total=precio_total,
                observaciones=observaciones,
                created_by=request.user,
                estado='borrador'
            )
            cuna.save()
            
            # Reconectar las señales
            pre_save.connect(cuña_pre_save, sender=CuñaPublicitaria)
            post_save.connect(cuña_post_save, sender=CuñaPublicitaria)
            
            messages.success(request, f'Cuña "{titulo}" creada exitosamente con código {cuna.codigo}')
            return redirect('custom_admin:cunas_list')
            
        except Exception as e:
            # Reconectar las señales en caso de error
            try:
                from apps.content_management.models import cuña_pre_save, cuña_post_save
                pre_save.connect(cuña_pre_save, sender=CuñaPublicitaria)
                post_save.connect(cuña_post_save, sender=CuñaPublicitaria)
            except:
                pass
                
            messages.error(request, f'Error al crear la cuña: {str(e)}')
            
            # Pasar los datos de vuelta al formulario para no perderlos
            context = {
                'clientes': User.objects.filter(rol='cliente', is_active=True),
                'vendedores': User.objects.filter(rol='vendedor', is_active=True),
                'categorias': CategoriaPublicitaria.objects.filter(is_active=True),
                'tipos_contrato': TipoContrato.objects.filter(is_active=True),
                'form_data': request.POST
            }
            return render(request, 'custom_admin/cunas/form.html', context)
            
    # GET - Mostrar formulario vacío
    clientes = User.objects.filter(rol='cliente', is_active=True)
    vendedores = User.objects.filter(rol='vendedor', is_active=True)
    categorias = CategoriaPublicitaria.objects.filter(is_active=True)
    tipos_contrato = TipoContrato.objects.filter(is_active=True)
    
    context = {
        'clientes': clientes,
        'vendedores': vendedores,
        'categorias': categorias,
        'tipos_contrato': tipos_contrato,
    }
    return render(request, 'custom_admin/cunas/form.html', context)

@login_required
@user_passes_test(is_admin)
def cuna_edit(request, pk):
    cuna = get_object_or_404(CuñaPublicitaria, pk=pk)
    
    if request.method == 'POST':
        try:
            # Desconectar temporalmente las señales
            from apps.content_management.models import cuña_pre_save, cuña_post_save
            pre_save.disconnect(cuña_pre_save, sender=CuñaPublicitaria)
            post_save.disconnect(cuña_post_save, sender=CuñaPublicitaria)
            
            # Actualizar datos
            cuna.titulo = request.POST.get('titulo', cuna.titulo)
            cuna.descripcion = request.POST.get('descripcion', cuna.descripcion)
            cuna.cliente_id = request.POST.get('cliente', cuna.cliente_id)
            cuna.vendedor_asignado_id = request.POST.get('vendedor') if request.POST.get('vendedor') else None
            categoria_id = request.POST.get('categoria')
            cuna.categoria_id = categoria_id if categoria_id else None
            tipo_contrato_id = request.POST.get('tipo_contrato')
            cuna.tipo_contrato_id = tipo_contrato_id if tipo_contrato_id else None
            cuna.duracion_planeada = request.POST.get('duracion_planeada', cuna.duracion_planeada)
            cuna.fecha_inicio = request.POST.get('fecha_inicio', cuna.fecha_inicio)
            cuna.fecha_fin = request.POST.get('fecha_fin', cuna.fecha_fin)
            cuna.repeticiones_dia = request.POST.get('repeticiones_dia', cuna.repeticiones_dia)
            
            precio_total_str = request.POST.get('precio_total')
            if precio_total_str:
                try:
                    cuna.precio_total = Decimal(precio_total_str)
                except:
                    pass
            
            cuna.observaciones = request.POST.get('observaciones', cuna.observaciones)
            cuna.estado = request.POST.get('estado', cuna.estado)
            
            cuna.save()
            
            # Reconectar las señales
            pre_save.connect(cuña_pre_save, sender=CuñaPublicitaria)
            post_save.connect(cuña_post_save, sender=CuñaPublicitaria)
            
            messages.success(request, f'Cuña "{cuna.titulo}" actualizada exitosamente')
            return redirect('custom_admin:cunas_list')
            
        except Exception as e:
            # Reconectar las señales
            try:
                from apps.content_management.models import cuña_pre_save, cuña_post_save
                pre_save.connect(cuña_pre_save, sender=CuñaPublicitaria)
                post_save.connect(cuña_post_save, sender=CuñaPublicitaria)
            except:
                pass
                
            messages.error(request, f'Error al actualizar la cuña: {str(e)}')
    
    # Obtener datos para el formulario
    clientes = User.objects.filter(rol='cliente', is_active=True)
    vendedores = User.objects.filter(rol='vendedor', is_active=True)
    categorias = CategoriaPublicitaria.objects.filter(is_active=True)
    tipos_contrato = TipoContrato.objects.filter(is_active=True)
    estados = [
        ('borrador', 'Borrador'),
        ('pendiente_revision', 'Pendiente de Revisión'),
        ('en_produccion', 'En Producción'),
        ('aprobada', 'Aprobada'),
        ('activa', 'Activa'),
        ('pausada', 'Pausada'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    context = {
        'cuna': cuna,
        'clientes': clientes,
        'vendedores': vendedores,
        'categorias': categorias,
        'tipos_contrato': tipos_contrato,
        'estados': estados,
    }
    return render(request, 'custom_admin/cunas/form.html', context)

@login_required
@user_passes_test(is_admin)
def cuna_detail(request, pk):
    cuna = get_object_or_404(CuñaPublicitaria, pk=pk)
    
    context = {
        'cuna': cuna,
    }
    return render(request, 'custom_admin/cunas/detail.html', context)

@login_required
@user_passes_test(is_admin)
def cuna_delete(request, pk):
    cuna = get_object_or_404(CuñaPublicitaria, pk=pk)
    
    if request.method == 'POST':
        try:
            titulo = cuna.titulo
            cuna.delete()
            messages.success(request, f'Cuña "{titulo}" eliminada exitosamente')
            return redirect('custom_admin:cunas_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar la cuña: {str(e)}')
    
    context = {'cuna': cuna}
    return render(request, 'custom_admin/cunas/confirm_delete.html', context)

# ============= OTRAS VISTAS =============
@login_required
@user_passes_test(is_admin)
def transmisiones_list(request):
    context = {
        'mensaje': 'Módulo de Transmisiones - En desarrollo'
    }
    return render(request, 'custom_admin/en_desarrollo.html', context)

@login_required
@user_passes_test(is_admin)
def semaforos_list(request):
    context = {
        'mensaje': 'Sistema de Semáforos - En desarrollo'
    }
    return render(request, 'custom_admin/en_desarrollo.html', context)

@login_required
@user_passes_test(is_admin)
def reportes_dashboard(request):
    context = {
        'mensaje': 'Módulo de Reportes - En desarrollo'
    }
    return render(request, 'custom_admin/en_desarrollo.html', context)

@login_required
@user_passes_test(is_admin)
def configuracion(request):
    context = {
        'mensaje': 'Configuración del Sistema - En desarrollo'
    }
    return render(request, 'custom_admin/en_desarrollo.html', context)
