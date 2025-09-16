from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q

# Obtener el modelo de usuario correcto
User = get_user_model()

def is_admin(user):
    return user.is_superuser or user.is_staff or user.rol == 'admin'

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    context = {
        'total_usuarios': User.objects.count(),
        'usuarios_activos': User.objects.filter(is_active=True).count(),
        'total_cunas': 0,  # Por implementar
        'alertas_pendientes': 0,  # Por implementar
    }
    return render(request, 'custom_admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def usuarios_list(request):
    # Búsqueda
    query = request.GET.get('q')
    usuarios = User.objects.all().order_by('-date_joined')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Paginación
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
            # Obtener datos del formulario
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            password = request.POST.get('password')
            rol = request.POST.get('rol')
            is_active = request.POST.get('is_active') == 'on'
            is_staff = request.POST.get('is_staff') == 'on'
            is_superuser = request.POST.get('is_superuser') == 'on'
            
            # Datos adicionales según el rol
            telefono = request.POST.get('telefono')
            direccion = request.POST.get('direccion')
            empresa = request.POST.get('empresa')
            ruc_dni = request.POST.get('ruc_dni')
            
            # Verificar si el usuario ya existe
            if User.objects.filter(username=username).exists():
                messages.error(request, f'El usuario {username} ya existe')
                return render(request, 'custom_admin/usuario_form.html')
            
            # Crear el usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            
            # Asignar campos adicionales
            user.rol = rol
            user.is_active = is_active
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.telefono = telefono
            user.direccion = direccion
            
            # Si es admin, automáticamente es staff
            if rol == 'admin':
                user.is_staff = True
            
            # Campos específicos para clientes
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
            # Actualizar datos del usuario
            usuario.username = request.POST.get('username', usuario.username)
            usuario.email = request.POST.get('email', usuario.email)
            usuario.first_name = request.POST.get('first_name', usuario.first_name)
            usuario.last_name = request.POST.get('last_name', usuario.last_name)
            usuario.rol = request.POST.get('rol', usuario.rol)
            usuario.is_active = request.POST.get('is_active') == 'on'
            usuario.is_staff = request.POST.get('is_staff') == 'on'
            usuario.is_superuser = request.POST.get('is_superuser') == 'on'
            
            # Actualizar campos adicionales
            usuario.telefono = request.POST.get('telefono', usuario.telefono)
            usuario.direccion = request.POST.get('direccion', usuario.direccion)
            
            # Si es admin, automáticamente es staff
            if usuario.rol == 'admin':
                usuario.is_staff = True
            
            # Campos específicos para clientes
            if usuario.rol == 'cliente':
                usuario.empresa = request.POST.get('empresa', usuario.empresa)
                usuario.ruc_dni = request.POST.get('ruc_dni', usuario.ruc_dni)
            
            # Si se proporciona una nueva contraseña
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

@login_required
@user_passes_test(is_admin)
def cunas_list(request):
    context = {
        'mensaje': 'Módulo de Cuñas Publicitarias - En desarrollo'
    }
    return render(request, 'custom_admin/en_desarrollo.html', context)

@login_required
@user_passes_test(is_admin)
def cuna_create(request):
    return render(request, 'custom_admin/en_desarrollo.html')

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
