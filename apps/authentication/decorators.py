"""
Decoradores personalizados para el sistema de permisos de PubliTrack
"""

from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.urls import reverse

def permission_required(permission_codename, raise_exception=False, redirect_url=None):
    """
    Decorador que verifica si el usuario tiene un permiso específico
    
    Args:
        permission_codename (str): Código del permiso requerido
        raise_exception (bool): Si lanzar excepción o redirigir
        redirect_url (str): URL de redirección si no tiene permisos
    
    Usage:
        @permission_required('view_users')
        def my_view(request):
            return render(request, 'template.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_permission(permission_codename):
                if request.headers.get('Content-Type') == 'application/json' or request.META.get('HTTP_ACCEPT') == 'application/json':
                    return JsonResponse({
                        'error': 'No tienes permisos para realizar esta acción',
                        'permission_required': permission_codename
                    }, status=403)
                
                if raise_exception:
                    raise PermissionDenied(f"Se requiere el permiso '{permission_codename}'")
                
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                
                if redirect_url:
                    return redirect(redirect_url)
                
                # Redirigir según el rol del usuario
                if request.user.es_admin:
                    return redirect('admin:index')
                elif request.user.es_vendedor:
                    return redirect('authentication:vendedor_dashboard')
                else:
                    return redirect('authentication:profile')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def module_access_required(module_name, raise_exception=False):
    """
    Decorador que verifica si el usuario tiene acceso a un módulo específico
    
    Args:
        module_name (str): Nombre del módulo
        raise_exception (bool): Si lanzar excepción o redirigir
    
    Usage:
        @module_access_required('financial_management')
        def financial_view(request):
            return render(request, 'financial.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_module_access(module_name):
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'error': f'No tienes acceso al módulo {module_name}',
                        'module_required': module_name
                    }, status=403)
                
                if raise_exception:
                    raise PermissionDenied(f"Se requiere acceso al módulo '{module_name}'")
                
                messages.error(request, f'No tienes acceso al módulo {module_name}.')
                return redirect('authentication:profile')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def role_required(*roles, raise_exception=False):
    """
    Decorador que verifica si el usuario tiene uno de los roles especificados
    
    Args:
        *roles: Roles permitidos
        raise_exception (bool): Si lanzar excepción o redirigir
    
    Usage:
        @role_required('admin', 'vendedor')
        def admin_or_seller_view(request):
            return render(request, 'template.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.rol not in roles:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'error': 'No tienes el rol necesario para esta acción',
                        'roles_required': list(roles),
                        'user_role': request.user.rol
                    }, status=403)
                
                if raise_exception:
                    raise PermissionDenied(f"Se requiere uno de estos roles: {', '.join(roles)}")
                
                messages.error(request, 'No tienes el rol necesario para acceder a esta página.')
                return redirect('authentication:profile')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(raise_exception=False):
    """
    Decorador que requiere que el usuario sea administrador
    
    Usage:
        @admin_required()
        def admin_only_view(request):
            return render(request, 'admin_template.html')
    """
    return role_required('admin', raise_exception=raise_exception)

def vendedor_or_admin_required(raise_exception=False):
    """
    Decorador que requiere que el usuario sea vendedor o administrador
    
    Usage:
        @vendedor_or_admin_required()
        def seller_view(request):
            return render(request, 'seller_template.html')
    """
    return role_required('admin', 'vendedor', raise_exception=raise_exception)

def active_user_required(raise_exception=False):
    """
    Decorador que verifica que el usuario esté activo
    
    Usage:
        @active_user_required()
        def active_user_view(request):
            return render(request, 'template.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.esta_activo:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'error': 'Tu cuenta no está activa',
                        'user_status': request.user.status
                    }, status=403)
                
                if raise_exception:
                    raise PermissionDenied("Tu cuenta no está activa")
                
                messages.error(request, 'Tu cuenta no está activa. Contacta al administrador.')
                return redirect('authentication:login')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def multiple_permissions_required(*permissions, require_all=True, raise_exception=False):
    """
    Decorador que verifica múltiples permisos
    
    Args:
        *permissions: Lista de permisos a verificar
        require_all (bool): Si requiere TODOS los permisos o solo UNO
        raise_exception (bool): Si lanzar excepción o redirigir
    
    Usage:
        @multiple_permissions_required('view_users', 'edit_users', require_all=True)
        def view_requiring_multiple_perms(request):
            return render(request, 'template.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user_has_perms = [request.user.has_permission(perm) for perm in permissions]
            
            if require_all:
                has_required_perms = all(user_has_perms)
                error_msg = f"Se requieren todos estos permisos: {', '.join(permissions)}"
            else:
                has_required_perms = any(user_has_perms)
                error_msg = f"Se requiere al menos uno de estos permisos: {', '.join(permissions)}"
            
            if not has_required_perms:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'error': error_msg,
                        'permissions_required': list(permissions),
                        'require_all': require_all
                    }, status=403)
                
                if raise_exception:
                    raise PermissionDenied(error_msg)
                
                messages.error(request, 'No tienes los permisos necesarios para esta acción.')
                return redirect('authentication:profile')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def owner_or_admin_required(get_object_owner, raise_exception=False):
    """
    Decorador que verifica si el usuario es dueño del objeto o admin
    
    Args:
        get_object_owner (callable): Función que retorna el dueño del objeto
        raise_exception (bool): Si lanzar excepción o redirigir
    
    Usage:
        def get_client_owner(request, *args, **kwargs):
            client_id = kwargs.get('client_id')
            client = get_object_or_404(Client, id=client_id)
            return client.vendedor_asignado
        
        @owner_or_admin_required(get_client_owner)
        def edit_client(request, client_id):
            # Solo el vendedor asignado o admin puede editar
            return render(request, 'edit_client.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.es_admin:
                try:
                    owner = get_object_owner(request, *args, **kwargs)
                    if owner != request.user:
                        if request.headers.get('Content-Type') == 'application/json':
                            return JsonResponse({
                                'error': 'No eres el propietario de este recurso',
                            }, status=403)
                        
                        if raise_exception:
                            raise PermissionDenied("No eres el propietario de este recurso")
                        
                        messages.error(request, 'No tienes permisos para acceder a este recurso.')
                        return redirect('authentication:profile')
                except Exception as e:
                    if raise_exception:
                        raise PermissionDenied(f"Error verificando propiedad: {str(e)}")
                    
                    messages.error(request, 'Error verificando permisos.')
                    return redirect('authentication:profile')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def ajax_permission_required(permission_codename):
    """
    Decorador específico para vistas AJAX que requieren permisos
    
    Usage:
        @ajax_permission_required('delete_users')
        def delete_user_ajax(request):
            # Vista AJAX para eliminar usuario
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_permission(permission_codename):
                return JsonResponse({
                    'success': False,
                    'error': 'No tienes permisos para realizar esta acción',
                    'permission_required': permission_codename
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Decoradores de conveniencia para casos comunes
admin_only = admin_required()
seller_or_admin = vendedor_or_admin_required()
active_user_only = active_user_required()

# Ejemplos de uso en views.py:
"""
from .decorators import (
    permission_required, 
    admin_required, 
    module_access_required,
    multiple_permissions_required
)

@permission_required('view_users')
def user_list(request):
    # Solo usuarios con permiso 'view_users'
    pass

@admin_required()
def admin_panel(request):
    # Solo administradores
    pass

@module_access_required('financial_management')
def financial_dashboard(request):
    # Solo usuarios con acceso al módulo financiero
    pass

@multiple_permissions_required('view_reports', 'export_reports')
def export_report(request):
    # Requiere ambos permisos
    pass
"""