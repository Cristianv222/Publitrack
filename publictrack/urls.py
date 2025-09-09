"""
URLs principales del proyecto PubliTrack
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import HttpResponse

def home_redirect(request):
    """Redirige a la página apropiada según el estado del usuario"""
    if request.user.is_authenticated:
        # Si está logueado, redirigir según su rol
        if hasattr(request.user, 'es_admin') and request.user.es_admin:
            return redirect('admin:index')
        elif hasattr(request.user, 'es_vendedor') and request.user.es_vendedor:
            return redirect('authentication:vendedor_dashboard')
        elif hasattr(request.user, 'es_cliente') and request.user.es_cliente:
            return redirect('authentication:profile')
        else:
            return redirect('authentication:profile')
    else:
        # Si no está logueado, ir al login
        return redirect('authentication:login')

def health_check(request):
    """Endpoint simple para verificar que el sistema funciona"""
    return HttpResponse("OK - PubliTrack funcionando correctamente", content_type="text/plain")

urlpatterns = [
    # ============================================================================
    # URLS PRINCIPALES
    # ============================================================================
    path('', home_redirect, name='home'),
    path('health/', health_check, name='health'),
    
    # ============================================================================
    # ADMINISTRACIÓN DE DJANGO
    # ============================================================================
    path('admin/', admin.site.urls),
    
    # ============================================================================
    # APLICACIONES DEL PROYECTO
    # ============================================================================
    
    # Sistema de Autenticación y Usuarios
    path('auth/', include('apps.authentication.urls')),
    
    # TODO: Agregar URLs de otras apps cuando estén listas
    # path('financial/', include('apps.financial_management.urls')),
    # path('content/', include('apps.content_management.urls')),
    # path('traffic/', include('apps.traffic_light_system.urls')),
    # path('transmission/', include('apps.transmission_control.urls')),
    # path('notifications/', include('apps.notifications.urls')),
    # path('sales/', include('apps.sales_management.urls')),
    # path('reports/', include('apps.reports_analytics.urls')),
    # path('system/', include('apps.system_configuration.urls')),
    
    # ============================================================================
    # API ENDPOINTS (PARA FUTURO)
    # ============================================================================
    # path('api/v1/', include('apps.api.urls')),
]

# ============================================================================
# CONFIGURACIÓN PARA DESARROLLO
# ============================================================================

if settings.DEBUG:
    # Servir archivos de media en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar (si está instalado)
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

# ============================================================================
# CONFIGURACIÓN DEL ADMIN
# ============================================================================

# Personalizar títulos del admin
admin.site.site_header = "PubliTrack - Administración"
admin.site.site_title = "PubliTrack"
admin.site.index_title = "Panel de Control"

# ============================================================================
# HANDLER DE ERRORES PERSONALIZADOS (OPCIONAL)
# ============================================================================

# handler404 = 'apps.core.views.custom_404'
# handler500 = 'apps.core.views.custom_500'
# handler403 = 'apps.core.views.custom_403'