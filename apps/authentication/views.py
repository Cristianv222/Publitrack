from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import CustomUser, UserLoginHistory
from .forms import LoginForm, UserRegistrationForm, UserProfileForm, PasswordChangeForm

# ============================================================================
# FUNCIONES AUXILIARES PARA PERMISOS
# ============================================================================

def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_authenticated and user.es_admin

def is_vendedor_or_admin(user):
    """Verifica si el usuario es vendedor o admin"""
    return user.is_authenticated and user.rol in ['admin', 'vendedor']

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# ============================================================================
# VISTAS DE AUTENTICACIÓN
# ============================================================================

def login_view(request):
    """Vista para el login de usuarios"""
    if request.user.is_authenticated:
        if request.user.es_admin:  # CORREGIDO: request.user
            return redirect('authentication:admin_dashboard')
        elif request.user.es_vendedor:  # CORREGIDO: request.user
            return redirect('authentication:vendedor_dashboard')
        else:
            return redirect('authentication:cliente_dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)
            
            # Intentar autenticación
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active and user.esta_activo:
                    login(request, user)
                    
                    # Registrar el login en el historial
                    UserLoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        session_key=request.session.session_key
                    )
                    
                    # Actualizar última conexión
                    user.marcar_ultima_conexion()
                    
                    # Configurar duración de sesión
                    if not remember_me:
                        request.session.set_expiry(0)  # Cerrar al cerrar navegador
                    else:
                        request.session.set_expiry(1209600)  # 2 semanas
                    
                    messages.success(
                        request, 
                        f'¡Bienvenido, {user.nombre_completo}!'
                    )
                    
                    # Redirigir según el rol
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    
                    # CORREGIDO: cada rol a su dashboard correspondiente
                    if user.es_admin:
                        return redirect('authentication:admin_dashboard')
                    elif user.es_vendedor:
                        return redirect('authentication:vendedor_dashboard')
                    else:
                        return redirect('authentication:cliente_dashboard')
                else:
                    if user.status == 'suspendido':
                        messages.error(request, 'Tu cuenta ha sido suspendida. Contacta al administrador.')
                    elif user.status == 'pendiente':
                        messages.error(request, 'Tu cuenta está pendiente de verificación.')
                    else:
                        messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    
    return render(request, 'authentication/login.html', {'form': form})

@login_required
def logout_view(request):
    """Vista para cerrar sesión"""
    # Registrar el logout en el historial
    try:
        last_login = UserLoginHistory.objects.filter(
            user=request.user,
            session_key=request.session.session_key,
            logout_time__isnull=True
        ).first()
        
        if last_login:
            last_login.logout_time = timezone.now()
            last_login.save()
    except:
        pass  # Si hay error, continuar con el logout
    
    username = request.user.nombre_completo
    logout(request)
    messages.success(request, f'¡Hasta luego, {username}!')
    return redirect('authentication:login')

@user_passes_test(is_admin)
def register_user_view(request):
    """Vista para registrar nuevos usuarios (solo admin)"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    
                    messages.success(
                        request, 
                        f'Usuario {user.username} ({user.get_rol_display()}) creado exitosamente.'
                    )
                    return redirect('authentication:user_list')
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {str(e)}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'authentication/register.html', {'form': form})

# ============================================================================
# VISTAS DE PERFIL
# ============================================================================

@login_required
def profile_view(request):
    """Vista del perfil del usuario actual"""
    # Obtener estadísticas según el rol
    context = {
        'user': request.user,
    }
    
    if request.user.es_vendedor:
        context.update({
            'total_clientes': request.user.get_total_clientes(),
            'ventas_mes': request.user.get_ventas_mes_actual(),
            'comisiones_mes': request.user.get_comisiones_mes_actual(),
            'porcentaje_meta': request.user.get_porcentaje_meta(),
        })
    elif request.user.es_cliente:
        context.update({
            'vendedor': request.user.get_vendedor(),
            # TODO: Agregar estadísticas de cuñas, pagos, etc.
        })
    
    return render(request, 'authentication/profile.html', context)

@login_required
def edit_profile_view(request):
    """Vista para editar el perfil del usuario actual"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('authentication:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'authentication/edit_profile.html', {'form': form})

@login_required
def change_password_view(request):
    """Vista para cambiar contraseña"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña cambiada exitosamente.')
            return redirect('authentication:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'authentication/change_password.html', {'form': form})

# ============================================================================
# VISTAS ADMINISTRATIVAS
# ============================================================================

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Lista de usuarios (solo admin)"""
    model = CustomUser
    template_name = 'authentication/user_list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def test_func(self):
        return is_admin(self.request.user)
    
    def get_queryset(self):
        queryset = CustomUser.objects.select_related('vendedor_asignado', 'supervisor')
        
        # Filtros
        rol = self.request.GET.get('rol')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        vendedor = self.request.GET.get('vendedor')
        
        if rol:
            queryset = queryset.filter(rol=rol)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if vendedor:
            queryset = queryset.filter(vendedor_asignado_id=vendedor)
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(empresa__icontains=search) |
                Q(ruc_dni__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = CustomUser.ROLE_CHOICES
        context['statuses'] = CustomUser.STATUS_CHOICES
        context['vendedores'] = CustomUser.objects.filter(rol='vendedor', status='activo')
        
        # Estadísticas rápidas
        context['stats'] = {
            'total_usuarios': CustomUser.objects.count(),
            'usuarios_activos': CustomUser.objects.filter(status='activo').count(),
            'vendedores': CustomUser.objects.filter(rol='vendedor').count(),
            'clientes': CustomUser.objects.filter(rol='cliente').count(),
        }
        
        return context

class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalle de usuario"""
    model = CustomUser
    template_name = 'authentication/user_detail.html'
    context_object_name = 'user_detail'
    
    def test_func(self):
        user = self.get_object()
        # Admin puede ver todo, otros solo su propio perfil
        return is_admin(self.request.user) or self.request.user == user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Información adicional según el rol
        if user.es_vendedor:
            context['clientes'] = user.get_clientes()[:10]  # Últimos 10 clientes
            context['total_clientes'] = user.get_total_clientes()
            context['ventas_mes'] = user.get_ventas_mes_actual()
            context['comisiones_mes'] = user.get_comisiones_mes_actual()
            
        elif user.es_cliente:
            context['vendedor'] = user.get_vendedor()
            # TODO: Agregar cuñas, pagos pendientes, etc.
        
        # Historial de conexiones (últimas 10)
        if is_admin(self.request.user) or self.request.user == user:
            context['login_history'] = user.login_history.all()[:10]
        
        return context

@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    """Cambiar estado del usuario (solo admin)"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # No permitir desactivar al último admin
        if user.es_admin and CustomUser.objects.filter(rol='admin', status='activo').count() <= 1:
            return JsonResponse({
                'success': False,
                'message': 'No se puede desactivar al último administrador.'
            })
        
        # Cambiar estado
        if user.status == 'activo':
            user.desactivar()
            action = 'desactivado'
        else:
            user.activar()
            action = 'activado'
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {action} exitosamente.',
            'new_status': user.status,
            'new_status_display': user.get_status_display()
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@user_passes_test(is_admin)
def user_stats_api(request):
    """API para estadísticas de usuarios"""
    stats = {
        'usuarios_por_rol': dict(
            CustomUser.objects.values('rol').annotate(count=Count('id')).values_list('rol', 'count')
        ),
        'usuarios_por_estado': dict(
            CustomUser.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        ),
        'registros_ultimos_30_dias': CustomUser.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
        'conexiones_hoy': UserLoginHistory.objects.filter(
            login_time__date=timezone.now().date()
        ).count()
    }
    
    return JsonResponse(stats)

# ============================================================================
# VISTAS PARA VENDEDORES
# ============================================================================

@user_passes_test(is_vendedor_or_admin)
def vendedor_dashboard(request):
    """Dashboard específico para vendedores"""
    user = request.user
    
    context = {
        'user': user,
    }
    
    if user.es_vendedor:
        clientes = user.get_clientes()
        context.update({
            'total_clientes': clientes.count(),
            'clientes_recientes': clientes[:5],
            'ventas_mes': user.get_ventas_mes_actual(),
            'comisiones_mes': user.get_comisiones_mes_actual(),
            'porcentaje_meta': user.get_porcentaje_meta(),
            'meta_mensual': user.meta_mensual,
        })
    
    # Si es admin, mostrar estadísticas generales
    if user.es_admin:
        context.update({
            'total_usuarios': CustomUser.objects.filter(status='activo').count(),
            'total_vendedores': CustomUser.objects.filter(rol='vendedor', status='activo').count(),
            'total_clientes_sistema': CustomUser.objects.filter(rol='cliente', status='activo').count(),
            'usuarios_recientes': CustomUser.objects.filter(status='activo').order_by('-created_at')[:5],
        })
    
    return render(request, 'dashboard/vendedor.html', context)

@login_required
def mis_clientes_view(request):
    """Lista de clientes del vendedor actual"""
    if not request.user.es_vendedor:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('authentication:profile')
    
    clientes = request.user.get_clientes()
    
    # Filtros
    search = request.GET.get('search')
    if search:
        clientes = clientes.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(empresa__icontains=search) |
            Q(ruc_dni__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(clientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'authentication/mis_clientes.html', {
        'clientes': page_obj,
        'total_clientes': clientes.count()
    })

# ============================================================================
# VISTAS DE REPORTES
# ============================================================================

@user_passes_test(is_admin)
def user_reports_view(request):
    """Reportes de usuarios (solo admin)"""
    # Estadísticas generales
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(status='activo').count()
    
    # Usuarios por rol
    users_by_role = dict(
        CustomUser.objects.values('rol').annotate(count=Count('id')).values_list('rol', 'count')
    )
    
    # Usuarios por estado
    users_by_status = dict(
        CustomUser.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
    )
    
    # Registros por mes (últimos 6 meses)
    from django.db.models import TruncMonth
    monthly_registrations = CustomUser.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=180)
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'users_by_role': users_by_role,
        'users_by_status': users_by_status,
        'monthly_registrations': list(monthly_registrations),
    }
    
    return render(request, 'authentication/user_reports.html', context)
@login_required
def admin_dashboard(request):
    """Dashboard para administradores"""
    if not request.user.es_admin:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('authentication:profile')
    
    context = {
        'total_usuarios': CustomUser.objects.filter(status='activo').count(),
        'total_vendedores': CustomUser.objects.filter(rol='vendedor', status='activo').count(),
        'total_clientes': CustomUser.objects.filter(rol='cliente', status='activo').count(),
        'usuarios_recientes': CustomUser.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/admin.html', context)

@login_required
def cliente_dashboard(request):
    """Dashboard para clientes"""
    if not request.user.es_cliente:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('authentication:profile')
    
    context = {
        'user': request.user,
        'vendedor': request.user.get_vendedor(),
    }
    return render(request, 'dashboard/cliente.html', context)