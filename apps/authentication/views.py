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
from django.db.models import Count, Sum, Q, F, Avg
from datetime import timedelta, datetime
from decimal import Decimal
import json
from django.conf import settings

# ============================================================================
# FUNCIONES AUXILIARES PARA PERMISOS
# ============================================================================

def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_authenticated and user.es_admin

def is_vendedor_or_admin(user):
    """Verifica si el usuario es vendedor o admin"""
    return user.is_authenticated and user.rol in ['admin', 'vendedor']

def is_productor(user):
    """Verifica si el usuario es productor"""
    return user.is_authenticated and user.rol == 'productor'

def is_productor_or_admin(user):
    """Verifica si el usuario es productor o admin"""
    return user.is_authenticated and user.rol in ['admin', 'productor']
def is_btr(user):
    """Verifica si el usuario es BTR"""
    return user.is_authenticated and user.rol == 'btr'
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
    """Login con redirección directa a los paneles correspondientes"""
    if request.user.is_authenticated:
        if request.user.es_admin: 
            return redirect('/panel/')
        elif request.user.es_vendedor: 
            return redirect('authentication:vendedor_dashboard')
        elif request.user.es_productor: 
            return redirect('authentication:productor_dashboard')
        elif request.user.es_btr: 
            return redirect('authentication:btr_dashboard')
        elif request.user.es_doctor:
            return redirect('authentication:doctor_dashboard')
        else: 
            return redirect('authentication:cliente_dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active and user.esta_activo:
                    login(request, user)
                    UserLoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        session_key=request.session.session_key
                    )
                    user.marcar_ultima_conexion()
                    
                    # Redirección según rol
                    if user.es_admin: 
                        return redirect('/panel/')
                    elif user.es_vendedor: 
                        return redirect('authentication:vendedor_dashboard')
                    elif user.es_productor: 
                        return redirect('authentication:productor_dashboard')
                    elif user.es_btr: 
                        return redirect('authentication:btr_dashboard')
                    elif user.es_doctor:
                        return redirect('authentication:doctor_dashboard')
                    else: 
                        return redirect('authentication:cliente_dashboard')
                else:
                    messages.error(request, 'Cuenta inactiva o suspendida.')
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
    elif request.user.es_productor:
        context.update({
            # TODO: Agregar estadísticas de producción
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
            'productores': CustomUser.objects.filter(rol='productor').count(),
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
        
        elif user.es_productor:
            # TODO: Agregar proyectos en producción, etc.
            pass
        
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
    """Dashboard específico para vendedores con contratos, clientes y contratos activos"""
    user = request.user
    
    # Importar modelos necesarios
    try:
        from apps.content_management.models import (
            ContratoGenerado, 
            CuñaPublicitaria, 
            PlantillaContrato,
            CategoriaPublicitaria
        )
    except ImportError:
        ContratoGenerado = None
        CuñaPublicitaria = None
        PlantillaContrato = None
        CategoriaPublicitaria = None
    
    # Obtener fechas para filtros
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    
    context = {
        'user': user,
        'hoy': hoy,
    }
    
    if user.es_vendedor:
        # ========== CLIENTES DEL VENDEDOR ==========
        clientes = user.get_clientes()
        
        # ========== CONTRATOS DEL VENDEDOR ==========
        contratos_vendedor = []
        contratos_activos = []
        ventas_mes = Decimal('0.00')
        comisiones_mes = Decimal('0.00')
        
        if ContratoGenerado:
            # Todos los contratos del vendedor
            contratos_vendedor = ContratoGenerado.objects.filter(
                vendedor_asignado=user
            ).select_related('cliente', 'cuña', 'plantilla_usada').order_by('-fecha_generacion')
            
            # Contratos activos (validados con cuña asociada)
            contratos_activos = contratos_vendedor.filter(
                estado='validado',
                cuña__isnull=False
            )
            
            # Calcular ventas del mes (contratos generados o validados este mes)
            contratos_mes = contratos_vendedor.filter(
                fecha_generacion__gte=inicio_mes,
                estado__in=['generado', 'validado', 'firmado']
            )
            ventas_mes = contratos_mes.aggregate(
                total=Sum('valor_total')
            )['total'] or Decimal('0.00')
            
            # Calcular comisiones del mes
            if user.comision_porcentaje:
                comisiones_mes = ventas_mes * (user.comision_porcentaje / 100)
        
        # ========== CUÑAS DEL VENDEDOR ==========
        cuñas_activas = 0
        cuñas_pendientes = 0
        
        if CuñaPublicitaria:
            cuñas_activas = CuñaPublicitaria.objects.filter(
                vendedor_asignado=user,
                estado='activa',
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy
            ).count()
            
            cuñas_pendientes = CuñaPublicitaria.objects.filter(
                vendedor_asignado=user,
                estado='pendiente_revision'
            ).count()
        
        # ========== CÁLCULO DE META ==========
        porcentaje_meta = 0
        if user.meta_mensual and user.meta_mensual > 0:
            porcentaje_meta = min(int((ventas_mes / user.meta_mensual) * 100), 100)
        
        # ========== PLANTILLAS Y CATEGORÍAS PARA CONTRATOS ==========
        plantillas = []
        plantillas_activas_count = 0
        categorias = []
        
        if PlantillaContrato:
            plantillas = PlantillaContrato.objects.filter(is_active=True).order_by('-is_default', 'nombre')
            plantillas_activas_count = plantillas.count()
        
        if CategoriaPublicitaria:
            categorias = CategoriaPublicitaria.objects.filter(is_active=True).order_by('nombre')
        
        context.update({
            # Estadísticas generales
            'total_clientes': clientes.count(),
            'total_contratos': contratos_vendedor.count() if ContratoGenerado else 0,
            'contratos_activos_count': contratos_activos.count() if ContratoGenerado else 0,
            'contratos_pendientes': contratos_vendedor.filter(estado='generado').count() if ContratoGenerado else 0,
            'cuñas_activas': cuñas_activas,
            'cuñas_pendientes': cuñas_pendientes,
            'plantillas_activas': plantillas_activas_count,
            
            # Métricas financieras
            'ventas_mes': ventas_mes,
            'comisiones_mes': comisiones_mes,
            'porcentaje_meta': porcentaje_meta,
            'meta_mensual': user.meta_mensual or Decimal('0.00'),
            
            # Listados para la vista
            'clientes': clientes.select_related().order_by('empresa', 'first_name'),  # Todos los clientes para el selector
            'clientes_recientes': clientes.order_by('-created_at')[:10],
            'contratos_recientes': contratos_vendedor[:10] if ContratoGenerado else [],
            'contratos_activos': contratos_activos[:10] if ContratoGenerado else [],
            
            # Para creación de contratos
            'plantillas': plantillas,
            'categorias': categorias,
        })
    
    # Si es admin, mostrar estadísticas generales
    elif user.es_admin:
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
    """Dashboard completo para administradores con datos reales"""
    if not request.user.es_admin:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('authentication:profile')
    
    # Obtener fechas para filtros
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    inicio_mes = hoy.replace(day=1)
    
    # ========== ESTADÍSTICAS DE USUARIOS ==========
    usuarios_stats = {
        'total': CustomUser.objects.count(),
        'activos': CustomUser.objects.filter(status='activo').count(),
        'vendedores': CustomUser.objects.filter(rol='vendedor', status='activo').count(),
        'clientes': CustomUser.objects.filter(rol='cliente', status='activo').count(),
        'admins': CustomUser.objects.filter(rol='admin', status='activo').count(),
        'productores': CustomUser.objects.filter(rol='productor', status='activo').count(),
        'nuevos_mes': CustomUser.objects.filter(created_at__gte=inicio_mes).count(),
        'conectados_hoy': UserLoginHistory.objects.filter(
            login_time__date=hoy
        ).values('user').distinct().count(),
    }
    
    # ========== ESTADÍSTICAS DE CUÑAS (con manejo de errores) ==========
    try:
        from apps.content_management.models import CuñaPublicitaria
        cuñas_stats = {
            'total': CuñaPublicitaria.objects.count(),
            'activas': CuñaPublicitaria.objects.filter(estado='activa').count(),
            'pendientes': CuñaPublicitaria.objects.filter(estado='pendiente_revision').count(),
            'proximas_vencer': CuñaPublicitaria.objects.filter(
                fecha_fin__range=[hoy, hoy + timedelta(days=7)],
                estado__in=['activa', 'aprobada']
            ).count(),
            'creadas_mes': CuñaPublicitaria.objects.filter(created_at__gte=inicio_mes).count(),
        }
        
        ingresos_mes = CuñaPublicitaria.objects.filter(
            created_at__gte=inicio_mes,
            estado__in=['activa', 'aprobada', 'finalizada']
        ).aggregate(Sum('precio_total'))['precio_total__sum'] or Decimal('0.00')
        
        ultimas_cuñas = CuñaPublicitaria.objects.select_related(
            'cliente', 'vendedor_asignado'
        ).order_by('-created_at')[:5]
        
        # Datos para el gráfico
        cuñas_por_dia = []
        for i in range(7):
            dia = hoy - timedelta(days=6-i)
            count = CuñaPublicitaria.objects.filter(created_at__date=dia).count()
            cuñas_por_dia.append({
                'dia': dia.strftime('%d/%m'),
                'cantidad': count
            })
    except:
        cuñas_stats = {'total': 0, 'activas': 0, 'pendientes': 0, 'proximas_vencer': 0, 'creadas_mes': 0}
        ingresos_mes = Decimal('0.00')
        ultimas_cuñas = []
        cuñas_por_dia = []
    
    # ========== ESTADÍSTICAS DE TRANSMISIONES ==========
    try:
        from apps.transmission_control.models import ProgramacionTransmision, TransmisionActual, LogTransmision
        transmisiones_stats = {
            'programadas_hoy': ProgramacionTransmision.objects.filter(
                fecha_inicio__date=hoy,
                estado='programada'
            ).count(),
            'activas_ahora': TransmisionActual.objects.filter(estado='transmitiendo').count(),
            'completadas_hoy': TransmisionActual.objects.filter(
                fin_real__date=hoy,
                estado='completada'
            ).count(),
        }
    except:
        transmisiones_stats = {'programadas_hoy': 0, 'activas_ahora': 0, 'completadas_hoy': 0}
    
    # ========== SISTEMA DE SEMÁFOROS ==========
    try:
        from apps.traffic_light_system.models import EstadoSemaforo, AlertaSemaforo
        semaforos_stats = EstadoSemaforo.objects.aggregate(
            verde=Count('id', filter=Q(color_actual='verde')),
            amarillo=Count('id', filter=Q(color_actual='amarillo')),
            rojo=Count('id', filter=Q(color_actual='rojo')),
            gris=Count('id', filter=Q(color_actual='gris'))
        )
        
        alertas_pendientes = AlertaSemaforo.objects.filter(
            estado='pendiente'
        ).select_related('cuña')[:5]
        
        alertas_count = AlertaSemaforo.objects.filter(estado='pendiente').count()
    except:
        semaforos_stats = {'verde': 0, 'amarillo': 0, 'rojo': 0, 'gris': 0}
        alertas_pendientes = []
        alertas_count = 0
    
    # Últimos usuarios registrados
    ultimos_usuarios = CustomUser.objects.order_by('-created_at')[:5]
    
    # Top vendedores
    top_vendedores = CustomUser.objects.filter(
        rol='vendedor',
        status='activo'
    ).annotate(
        total_clientes=Count('clientes_asignados', filter=Q(clientes_asignados__status='activo'))
    ).order_by('-total_clientes')[:5]
    
    # ========== CONTEXT ==========
    context = {
        'usuarios_stats': usuarios_stats,
        'cuñas_stats': cuñas_stats,
        'transmisiones_stats': transmisiones_stats,
        'semaforos_stats': semaforos_stats,
        'alertas_count': alertas_count,
        'ingresos_mes': ingresos_mes,
        'alertas_pendientes': alertas_pendientes,
        'ultimas_cuñas': ultimas_cuñas,
        'ultimos_usuarios': ultimos_usuarios,
        'top_vendedores': top_vendedores,
        'cuñas_por_dia': json.dumps(cuñas_por_dia),  # Convertir a JSON
        'hoy': hoy,
        'inicio_mes': inicio_mes,
        'debug': settings.DEBUG,  # Para debugging
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

# ============================================================================
# VISTAS PARA PRODUCTORES
# ============================================================================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

@login_required
def productor_dashboard(request):
    """Dashboard específico para productores con proyectos, cuñas y GRILLA PUBLICITARIA"""
    if not request.user.es_productor:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('authentication:profile')
    
    # Importar modelos necesarios
    try:
        from apps.content_management.models import CuñaPublicitaria
        from apps.programacion_canal.models import ProgramacionSemanal, BloqueProgramacion
        from apps.grilla_publicitaria.models import UbicacionPublicitaria, AsignacionCuña
        GRILLA_AVAILABLE = True
    except ImportError as e:
        print(f"Error importando módulos en productor_dashboard: {e}")
        GRILLA_AVAILABLE = False
        CuñaPublicitaria = None
        ProgramacionSemanal = BloqueProgramacion = UbicacionPublicitaria = AsignacionCuña = None
    
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    # ====================================================================
    # GRILLA PUBLICITARIA — 100% A PRUEBA DE ERRORES
    # ====================================================================
    # Horas del día (Intervalos de 30 minutos, 24 horas - IGUAL QUE GRILLA PUBLICITARIA)
    horas_dia = []
    for hora in range(0, 24):
        for minuto in [0, 30]:
            horas_dia.append(f"{hora:02d}:{minuto:02d}")

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    # Inicializar variables
    programaciones = []
    programacion_actual = None
    bloques_semana = []
    ubicaciones = []
    asignaciones = []
    cuñas_disponibles = []
    
    # Estadísticas para el dashboard
    total_cuñas = 0
    cuñas_programadas = 0
    cuñas_pendientes = 0
    ingresos_totales = 0

    if GRILLA_AVAILABLE:
        try:
            # 1. Obtener programaciones
            programaciones = ProgramacionSemanal.objects.all().order_by('-fecha_inicio_semana')
    
            programacion_id = request.GET.get('programacion_id')
            if programacion_id:
                programacion_actual = ProgramacionSemanal.objects.filter(id=programacion_id).first()
    
            if not programacion_actual and programaciones:
                programacion_actual = ProgramacionSemanal.objects.filter(
                    fecha_inicio_semana__lte=hoy,
                    fecha_fin_semana__gte=hoy
                ).first() or programaciones.first()
    
            if programacion_actual:
                # 2. Bloques de programación
                bloques_semana = BloqueProgramacion.objects.filter(
                    programacion_semanal=programacion_actual
                ).select_related('programa').order_by('dia_semana', 'hora_inicio')
    
                # 3. Ubicaciones publicitarias (con prefetch de cuñas para la grilla)
                ubicaciones = UbicacionPublicitaria.objects.filter(
                    bloque_programacion__programacion_semanal=programacion_actual,
                    activo=True
                ).select_related('bloque_programacion', 'bloque_programacion__programa').prefetch_related('asignaciones__cuña')
    
                # 4. Asignaciones (para estadísticas y uso general)
                asignaciones = AsignacionCuña.objects.filter(
                    ubicacion__bloque_programacion__programacion_semanal=programacion_actual
                ).select_related('cuña', 'ubicacion')
                
                # 5. Cuñas disponibles para programar
                if CuñaPublicitaria:
                    cuñas_disponibles = CuñaPublicitaria.objects.filter(
                        estado='activa',
                        fecha_inicio__lte=hoy,
                        fecha_fin__gte=hoy
                    ).select_related('cliente', 'categoria')
                    
                    # Estadísticas
                    total_cuñas = CuñaPublicitaria.objects.filter(estado='activa').count()
                
                cuñas_programadas = asignaciones.count()
                cuñas_pendientes = max(0, total_cuñas - cuñas_programadas)
                
                # Calcular ingresos
                for asignacion in asignaciones:
                    try:
                        ingresos_totales += float(asignacion.cuña.precio_total)
                    except (AttributeError, TypeError, ValueError):
                        continue
                        
        except Exception as e:
            print(f"Error cargando datos del dashboard productor despues de importarlos: {e}")
            pass

    context = {
        'user': request.user,
        'hoy': hoy,
        'inicio_mes': inicio_mes,
        
        # GRILLA
        'programaciones': programaciones,
        'programacion_actual': programacion_actual,
        'bloques_semana': bloques_semana,
        'ubicaciones': ubicaciones,
        'asignaciones': asignaciones,
        'cuñas_disponibles': cuñas_disponibles,
        'horas_dia': horas_dia,
        'dias_semana': dias_semana,
        'grilla_available': GRILLA_AVAILABLE,
        
        # Estadísticas de Grilla
        'total_cuñas': total_cuñas,
        'cuñas_programadas': cuñas_programadas,
        'cuñas_pendientes': cuñas_pendientes,
        'ingresos_totales': ingresos_totales,
    }
    
    if CuñaPublicitaria:
        cuñas_en_produccion = CuñaPublicitaria.objects.filter(estado='en_produccion').count()
        cuñas_pendientes = CuñaPublicitaria.objects.filter(estado='pendiente_revision').count()
        cuñas_completadas_hoy = CuñaPublicitaria.objects.filter(updated_at__date=hoy, estado='aprobada').count()
        cuñas_activas = CuñaPublicitaria.objects.filter(estado='activa', fecha_inicio__lte=hoy, fecha_fin__gte=hoy).count()
        ultimas_cuñas = CuñaPublicitaria.objects.select_related('cliente', 'vendedor_asignado').order_by('-created_at')[:10]

        context.update({
            'cuñas_en_produccion': cuñas_en_produccion,
            'cuñas_pendientes': cuñas_pendientes,
            'cuñas_completadas_hoy': cuñas_completadas_hoy,
            'cuñas_activas': cuñas_activas,
            'ultimas_cuñas': ultimas_cuñas,
            'cuñas_por_estado': {
                'en_produccion': cuñas_en_produccion,
                'pendientes': cuñas_pendientes,
                'completadas_hoy': cuñas_completadas_hoy,
                'activas': cuñas_activas,
            },
        })
    else:
        context.update({
            'cuñas_en_produccion': 0, 'cuñas_pendientes': 0,
            'cuñas_completadas_hoy': 0, 'cuñas_activas': 0,
            'ultimas_cuñas': [], 'cuñas_por_estado': {},
        })

    return render(request, 'dashboard/productor.html', context)

# ============================================================================
# VISTAS PARA GESTIÓN DE CLIENTES POR VENDEDORES
# ============================================================================
@login_required
@user_passes_test(is_vendedor_or_admin)
def vendedor_crear_cliente(request):
    """Crear un nuevo cliente (vendedor o admin) - MODIFICADA"""
    if request.method == 'POST':
        try:
            # DETECTAR SI ES UNA PETICIÓN AJAX (desde el modal)
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
            
            with transaction.atomic():
                # Generar contraseña aleatoria
                import random
                import string
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                
                # Obtener datos
                username = request.POST.get('username')
                email = request.POST.get('email')
                ruc_dni = request.POST.get('ruc_dni')
                
                # VALIDAR UNICIDAD DE RUC/DNI
                if ruc_dni and CustomUser.objects.filter(ruc_dni=ruc_dni).exists():
                    error_msg = 'El RUC/DNI ya está registrado'
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': error_msg
                        }, status=400)
                    else:
                        messages.error(request, error_msg)
                        return redirect('authentication:vendedor_dashboard')
                
                # VALIDAR UNICIDAD DE EMAIL
                if email and CustomUser.objects.filter(email=email).exists():
                    error_msg = 'El correo electrónico ya está registrado'
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': error_msg
                        }, status=400)
                    else:
                        messages.error(request, error_msg)
                        return redirect('authentication:vendedor_dashboard')
                
                # Crear usuario
                cliente = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=request.POST.get('first_name', ''),
                    last_name=request.POST.get('last_name', ''),
                    rol='cliente',
                    status='activo'
                )
                
                # Asignar campos adicionales
                cliente.telefono = request.POST.get('telefono', '')
                cliente.empresa = request.POST.get('empresa', '')
                cliente.ruc_dni = ruc_dni
                cliente.razon_social = request.POST.get('razon_social', '')
                cliente.giro_comercial = request.POST.get('giro_comercial', '')
                cliente.ciudad = request.POST.get('ciudad', '')
                cliente.provincia = request.POST.get('provincia', '')
                cliente.direccion_exacta = request.POST.get('direccion_exacta', '')
                cliente.profesion = request.POST.get('profesion', '')
                cliente.cargo_empresa = request.POST.get('cargo_empresa', '')
                
                # Asignar al vendedor actual si no es admin
                if request.user.es_vendedor:
                    cliente.vendedor_asignado = request.user
                
                cliente.save()
                
                # MENSAJE SIMPLIFICADO
                success_msg = f'Cliente {cliente.empresa} creado exitosamente'
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_msg,
                        'cliente_id': cliente.id
                    })
                else:
                    messages.success(request, success_msg)
                
        except Exception as e:
            error_msg = f'Error al crear el cliente: {str(e)}'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                }, status=500)
            else:
                messages.error(request, error_msg)
    
    # Si es GET, redirigir al dashboard
    return redirect('authentication:vendedor_dashboard')
@login_required
@user_passes_test(is_vendedor_or_admin)
def vendedor_editar_cliente(request, cliente_id):
    """Editar un cliente existente - MODIFICADA"""
    cliente = get_object_or_404(CustomUser, pk=cliente_id, rol='cliente')
    
    # Verificar permisos
    if request.user.es_vendedor and cliente.vendedor_asignado != request.user:
        error_msg = 'No tienes permisos para editar este cliente.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': error_msg
            }, status=403)
        else:
            messages.error(request, error_msg)
            return redirect('authentication:vendedor_dashboard')
    
    if request.method == 'POST':
        try:
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
            with transaction.atomic():
                # VALIDAR UNICIDAD DE RUC/DNI (excluyendo cliente actual)
                ruc_dni = request.POST.get('ruc_dni')
                if ruc_dni and CustomUser.objects.filter(
                    ruc_dni=ruc_dni
                ).exclude(pk=cliente_id).exists():
                    error_msg = 'El RUC/DNI ya está registrado por otro cliente'
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': error_msg
                        }, status=400)
                    else:
                        messages.error(request, error_msg)
                        return redirect('authentication:vendedor_dashboard')
                
                # VALIDAR UNICIDAD DE EMAIL (excluyendo cliente actual)
                email = request.POST.get('email')
                if email and CustomUser.objects.filter(
                    email=email
                ).exclude(pk=cliente_id).exists():
                    error_msg = 'El correo electrónico ya está registrado por otro cliente'
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': error_msg
                        }, status=400)
                    else:
                        messages.error(request, error_msg)
                        return redirect('authentication:vendedor_dashboard')
                
                # Actualizar datos básicos
                cliente.first_name = request.POST.get('first_name', '')
                cliente.last_name = request.POST.get('last_name', '')
                cliente.email = email
                cliente.telefono = request.POST.get('telefono', '')
                cliente.empresa = request.POST.get('empresa', '')
                cliente.ruc_dni = ruc_dni
                cliente.razon_social = request.POST.get('razon_social', '')
                cliente.giro_comercial = request.POST.get('giro_comercial', '')
                cliente.ciudad = request.POST.get('ciudad', '')
                cliente.provincia = request.POST.get('provincia', '')
                cliente.direccion_exacta = request.POST.get('direccion_exacta', '')
                cliente.profesion = request.POST.get('profesion', '')
                cliente.cargo_empresa = request.POST.get('cargo_empresa', '')
                
                cliente.save()
                
                success_msg = f'Cliente {cliente.empresa} actualizado exitosamente.'
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_msg
                    })
                else:
                    messages.success(request, success_msg)
                
        except Exception as e:
            error_msg = f'Error al actualizar el cliente: {str(e)}'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': error_msg
                }, status=500)
            else:
                messages.error(request, error_msg)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)
    else:
        return redirect('authentication:vendedor_dashboard')
    

@login_required
@user_passes_test(is_vendedor_or_admin)
def vendedor_clientes_api(request):
    """API para obtener lista de clientes (JSON)"""
    try:
        queryset = CustomUser.objects.filter(rol='cliente', is_active=True)
        
        # Si es vendedor, filtrar solo sus clientes asignados
        if request.user.es_vendedor:
            queryset = queryset.filter(vendedor_asignado=request.user)
            
        clientes = list(queryset.values(
            'id', 'username', 'first_name', 'last_name', 'empresa', 'ruc_dni'
        ).order_by('-date_joined'))
        
        # Añadir nombre completo manualmente ya que no es un campo de base de datos directo en values
        for c in clientes:
            nombre = f"{c['first_name']} {c['last_name']}".strip()
            c['nombre'] = nombre if nombre else c['username']

        return JsonResponse({
            'success': True,
            'clientes': clientes
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_vendedor_or_admin)
def vendedor_detalle_cliente_api(request, cliente_id):
    """API para obtener detalles de un cliente (JSON)"""
    try:
        cliente = get_object_or_404(CustomUser, pk=cliente_id, rol='cliente')
        
        # Verificar permisos
        if request.user.es_vendedor and cliente.vendedor_asignado != request.user:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = {
            'id': cliente.id,
            'username': cliente.username,
            'first_name': cliente.first_name,
            'last_name': cliente.last_name,
            'email': cliente.email,
            'telefono': cliente.telefono or '',
            'empresa': cliente.empresa or '',
            'ruc_dni': cliente.ruc_dni or '',
            'razon_social': cliente.razon_social or '',
            'giro_comercial': cliente.giro_comercial or '',
            'ciudad': cliente.ciudad or '',
            'provincia': cliente.provincia or '',
            'direccion_exacta': cliente.direccion_exacta or '',
            'profesion': cliente.profesion or '',
            'cargo_empresa': cliente.cargo_empresa or '',
            'status': cliente.status,
            'fecha_registro': cliente.created_at.strftime('%d/%m/%Y'),
            'vendedor_asignado_nombre': cliente.vendedor_asignado.get_full_name() if cliente.vendedor_asignado else None,
        }
        
        return JsonResponse(data)
        
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============================================================================
# VISTAS PARA GESTIÓN DE CONTRATOS POR VENDEDORES
# ============================================================================

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def vendedor_crear_contrato(request):
    """Crear un nuevo contrato (vendedor o admin) - Lógica espejo de Admin"""
    # Verificación manual de autenticación para evitar redirecciones HTML en AJAX
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Su sesión ha expirado. Por favor recargue la página.'}, status=401)
    
    if not (request.user.es_vendedor or request.user.es_admin):
        return JsonResponse({'success': False, 'error': 'No tiene permisos para realizar esta acción.'}, status=403)

    if request.method == 'POST':
        try:
            # Importar modelos necesarios
            from apps.content_management.models import PlantillaContrato, ContratoGenerado, CategoriaPublicitaria
            from datetime import datetime
            
            data = json.loads(request.body)
            
            # Obtener plantilla y cliente
            plantilla = get_object_or_404(PlantillaContrato, pk=data['plantilla_id'])
            
            try:
                cliente = CustomUser.objects.get(pk=data['cliente_id'], rol='cliente')
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
            
            # Verificar permisos de vendedor
            if request.user.es_vendedor:
                if hasattr(cliente, 'vendedor_asignado') and cliente.vendedor_asignado and cliente.vendedor_asignado != request.user:
                     return JsonResponse({'success': False, 'error': 'Este cliente está asignado a otro vendedor'}, status=403)
            
            # Determinar vendedor asignado
            vendedor_asignado = request.user if request.user.es_vendedor else getattr(cliente, 'vendedor_asignado', None)

            # Obtener Categoría
            categoria_id = data.get('categoria_id')
            categoria = None
            if categoria_id:
                try:
                    categoria = CategoriaPublicitaria.objects.get(id=categoria_id, is_active=True)
                except CategoriaPublicitaria.DoesNotExist:
                    pass

            with transaction.atomic():
                # Procesar fechas excluidas: convertir array JSON a string separado por comas si es necesario
                # El modelo espera TextField default '', así que guardaremos el JSON string para preservar estructura
                fechas_excluidas_raw = data.get('fechas_excluidas', [])
                fechas_excluidas_str = json.dumps(fechas_excluidas_raw) if isinstance(fechas_excluidas_raw, list) else str(fechas_excluidas_raw)
                
                # Crear contrato usando campos explícitos del modelo
                contrato = ContratoGenerado.objects.create(
                    plantilla_usada=plantilla,
                    cliente=cliente,
                    vendedor_asignado=vendedor_asignado,
                    nombre_cliente=cliente.empresa or cliente.get_full_name(),
                    ruc_dni_cliente=cliente.ruc_dni or '',
                    valor_sin_iva=Decimal(str(data['valor_total'])),
                    generado_por=request.user,
                    estado='borrador',
                    observaciones=data.get('observaciones', ''),
                    
                    # Campos de compromisos y exclusiones
                    spots_por_mes=int(data.get('spots_mes', 0)) if data.get('spots_mes') else 0,
                    
                    compromiso_spot_texto=data.get('compromiso_spot', ''),
                    
                    compromiso_transmision_texto=data.get('compromiso_transmision_texto', ''),
                    compromiso_transmision_cantidad=int(data.get('compromiso_transmision_cantidad', 0)) if data.get('compromiso_transmision_cantidad') else 0,
                    compromiso_transmision_valor=Decimal(str(data.get('compromiso_transmision_valor', '0.00'))),
                    
                    compromiso_notas_texto=data.get('compromiso_notas_texto', ''),
                    compromiso_notas_cantidad=int(data.get('compromiso_notas_cantidad', 0)) if data.get('compromiso_notas_cantidad') else 0,
                    compromiso_notas_valor=Decimal(str(data.get('compromiso_notas_valor', '0.00'))),
                    
                    excluir_fines_semana=data.get('excluir_fines_semana', False),
                    fechas_excluidas=fechas_excluidas_str
                )
                
                # Guardar datos de generación para el PDF
                contrato.datos_generacion = {
                    'FECHA_INICIO_RAW': data['fecha_inicio'],
                    'FECHA_FIN_RAW': data['fecha_fin'],
                    'SPOTS_DIA': data.get('spots_dia', 1),
                    'DURACION_SPOT': data.get('duracion_spot', 30),
                    'VALOR_POR_SEGUNDO': data.get('valor_por_segundo', 0),
                    'OBSERVACIONES': data.get('observaciones', ''),
                    'VENDEDOR_ASIGNADO_ID': vendedor_asignado.id if vendedor_asignado else None,
                    'VENDEDOR_ASIGNADO_NOMBRE': vendedor_asignado.get_full_name() if vendedor_asignado else None,
                    'CATEGORIA_ID': categoria.id if categoria else None,
                    'CATEGORIA_NOMBRE': categoria.nombre if categoria else None
                }
                
                contrato.save()
                
                # Generar el PDF del contrato
                if contrato.generar_contrato():
                    return JsonResponse({
                        'success': True,
                        'message': 'Contrato generado exitosamente',
                        'contrato_id': contrato.id,
                        'numero_contrato': contrato.numero_contrato,
                        'archivo_url': contrato.archivo_contrato_pdf.url if contrato.archivo_contrato_pdf else None
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Error al generar el PDF del contrato'
                    }, status=500)
                
        except Exception as e:
            print(f"Error creando contrato VENDEDOR: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'Error técnico: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
@login_required
@user_passes_test(is_vendedor_or_admin)
def vendedor_categorias_api(request):
    """API para obtener categorías publicitarias (para vendedor)"""
    try:
        from apps.content_management.models import CategoriaPublicitaria
        
        categorias = CategoriaPublicitaria.objects.filter(
            is_active=True
        ).order_by('nombre')
        
        data = []
        for categoria in categorias:
            data.append({
                'id': categoria.id,
                'nombre': categoria.nombre,
                'descripcion': categoria.descripcion or '',
                'color_codigo': categoria.color_codigo,
                'tarifa_base': str(categoria.tarifa_base),
            })
        
        return JsonResponse({'success': True, 'categorias': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_vendedor_or_admin)
def vendedor_plantillas_api(request):
    """API para obtener plantillas activas"""
    try:
        from apps.content_management.models import PlantillaContrato
        
        plantillas = PlantillaContrato.objects.filter(is_active=True).order_by('-is_default', 'nombre')
        
        data = {
            'success': True,
            'plantillas': [
                {
                    'id': p.id,
                    'nombre': p.nombre,
                    'tipo_contrato': p.tipo_contrato,
                    'tipo_contrato_display': p.get_tipo_contrato_display(),
                    'version': p.version,
                    'incluye_iva': p.incluye_iva,
                    'porcentaje_iva': float(p.porcentaje_iva),
                    'is_default': p.is_default
                }
                for p in plantillas
            ]
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_vendedor_or_admin)
def vendedor_plantilla_detalle_api(request, plantilla_id):
    """API para obtener detalles de una plantilla"""
    try:
        from apps.content_management.models import PlantillaContrato
        
        plantilla = get_object_or_404(PlantillaContrato, pk=plantilla_id, is_active=True)
        
        data = {
            'success': True,
            'plantilla': {
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'tipo_contrato': plantilla.tipo_contrato,
                'tipo_contrato_display': plantilla.get_tipo_contrato_display(),
                'version': plantilla.version,
                'incluye_iva': plantilla.incluye_iva,
                'porcentaje_iva': float(plantilla.porcentaje_iva),
                'is_default': plantilla.is_default,
                'descripcion': plantilla.descripcion
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@login_required
@user_passes_test(is_btr)
def btr_dashboard(request):
    """NUEVO: Panel exclusivo para BTR"""
    # Importar modelos aquí para evitar importaciones circulares
    try:
        from apps.orders.models import OrdenToma, OrdenProduccion
        
        # Obtener todas las órdenes ordenadas por fecha reciente
        ordenes_toma = OrdenToma.objects.all().order_by('-created_at')
        ordenes_produccion = OrdenProduccion.objects.all().order_by('-created_at')
    except ImportError:
        ordenes_toma = []
        ordenes_produccion = []
    
    # Obtener clientes activos para el modal de creación de órdenes
    clientes = CustomUser.objects.filter(rol='cliente', is_active=True).order_by('empresa', 'first_name')
        
    context = {
        'user': request.user,
        'hoy': timezone.now().date(),
        'ordenes_toma': ordenes_toma,
        'ordenes_produccion': ordenes_produccion,
        'clientes': clientes,  # Para el dropdown de clientes en modales
        'btr_active': True  # Flag para identificar el dashboard activo
    }
    return render(request, 'dashboard/btr.html', context)

# ============================================================================
# VISTA PARA DOCTOR (PÁGINA DE BIENVENIDA)
# ============================================================================
@login_required
def doctor_dashboard(request):
    """Dashboard de bienvenida para el Doctor"""
    if not request.user.es_doctor and not request.user.es_admin:
        messages.error(request, 'No tienes permisos para ver esta página.')
        return redirect('authentication:profile')
    
    context = {
        'user': request.user,
        'segment_doctor_dashboard': True,
    }

    return render(request, 'dashboard/doctor.html', context)