"""
URLs principales del proyecto PubliTrack
Incluye soporte para Progressive Web App (PWA)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_control
from django.templatetags.static import static as static_url

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

def serve_manifest(request):
    """Sirve el manifest.json con las URLs absolutas correctas"""
    manifest = {
        "name": "PublicTrack - Sistema de Gestión Radial",
        "short_name": "PublicTrack",
        "description": "Sistema integral de gestión para emisoras de radio",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#1976d2",
        "orientation": "any",
        "scope": "/",
        "lang": "es",
        "dir": "ltr",
        "categories": ["business", "productivity", "utilities"],
        "prefer_related_applications": False,
        "icons": [
            {
                "src": static_url('icons/icon-72x72.png'),
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": static_url('icons/icon-96x96.png'),
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": static_url('icons/icon-128x128.png'),
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": static_url('icons/icon-144x144.png'),
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": static_url('icons/icon-152x152.png'),
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": static_url('icons/icon-192x192.png'),
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": static_url('icons/icon-384x384.png'),
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "maskable any"
            },
            {
                "src": static_url('icons/icon-512x512.png'),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable any"
            }
        ],
        "screenshots": [
            {
                "src": static_url('screenshots/desktop-home.png'),
                "sizes": "1920x1080",
                "type": "image/png",
                "platform": "wide",
                "label": "Dashboard Principal"
            },
            {
                "src": static_url('screenshots/mobile-home.png'),
                "sizes": "750x1334",
                "type": "image/png",
                "platform": "narrow",
                "label": "Vista Móvil"
            }
        ],
        "shortcuts": [
            {
                "name": "Nueva Cuña",
                "short_name": "Nueva Cuña",
                "description": "Registrar nueva cuña publicitaria",
                "url": "/content/nueva-cuna/",
                "icons": [
                    {
                        "src": static_url('icons/shortcut-new.png'),
                        "sizes": "96x96"
                    }
                ]
            },
            {
                "name": "Transmisiones",
                "short_name": "Transmisiones",
                "description": "Ver programación de transmisiones",
                "url": "/transmisiones/",
                "icons": [
                    {
                        "src": static_url('icons/shortcut-transmission.png'),
                        "sizes": "96x96"
                    }
                ]
            },
            {
                "name": "Reportes",
                "short_name": "Reportes",
                "description": "Ver reportes y análisis",
                "url": "/reports/",
                "icons": [
                    {
                        "src": static_url('icons/shortcut-reports.png'),
                        "sizes": "96x96"
                    }
                ]
            }
        ]
    }
    
    return JsonResponse(manifest)

def serve_service_worker(request):
    """Sirve el Service Worker (cuando lo implementes)"""
    sw_content = """
    // Service Worker básico para PublicTrack
    const CACHE_NAME = 'publictrack-v1';
    const urlsToCache = [
        '/',
        '/static/css/style.css',
        '/static/js/main.js',
    ];

    self.addEventListener('install', event => {
        event.waitUntil(
            caches.open(CACHE_NAME)
                .then(cache => cache.addAll(urlsToCache))
        );
    });

    self.addEventListener('fetch', event => {
        event.respondWith(
            caches.match(event.request)
                .then(response => response || fetch(event.request))
        );
    });
    """
    return HttpResponse(sw_content, content_type='application/javascript')

def offline_page(request):
    """Página que se muestra cuando no hay conexión"""
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sin Conexión - PublicTrack</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .offline-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 { color: #333; }
            p { color: #666; }
            button {
                background: #1976d2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="offline-container">
            <h1>📡 Sin Conexión</h1>
            <p>Estás trabajando en modo offline</p>
            <p>Los cambios se sincronizarán cuando vuelva la conexión</p>
            <button onclick="location.reload()">Reintentar</button>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

urlpatterns = [
    # ============================================================================
    # URLS PRINCIPALES
    # ============================================================================
    path('', home_redirect, name='home'),
    path('health/', health_check, name='health'),
    
    # ============================================================================
    # URLS PWA (Progressive Web App)
    # ============================================================================
    path('manifest.json', serve_manifest, name='manifest'),
    path('sw.js', serve_service_worker, name='service_worker'),
    path('offline/', offline_page, name='offline'),
    path('sw.js', TemplateView.as_view(template_name='../static/sw.js',content_type='application/javascript'), name='service_worker'),
    path('', include('pwa.urls')),
    
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
    path('content/', include('apps.content_management.urls')),
    path('traffic/', include('apps.traffic_light_system.urls')),
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