"""
Django settings for publictrack project.
Sistema de gestión de publicidad radial - PubliTrack
VERSIÓN CORREGIDA - CON SOPORTE PWA
"""

from pathlib import Path
import os
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# CONFIGURACIÓN DE USUARIO PERSONALIZADO - DEBE IR AL INICIO
# =============================================================================
AUTH_USER_MODEL = 'authentication.CustomUser'

# =============================================================================
# CONFIGURACIÓN BÁSICA DE DJANGO
# =============================================================================

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0', cast=Csv())

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'pwa',  # django-pwa agregado aquí
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.financial_management',
    'apps.content_management',
    'apps.traffic_light_system',
    'apps.transmission_control',
    'apps.notifications',
    'apps.sales_management',
    'apps.reports_analytics',
    'apps.system_configuration',
    'apps.custom_admin',
    # ✨ NUEVAS APPS AGREGADAS
    'apps.orders',
    'apps.parte_mortorios',
    'apps.programacion_canal',
    'apps.grilla_publicitaria',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'publictrack.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.i18n',
                'django.template.context_processors.tz',
            ],
        },
    },
]

WSGI_APPLICATION = 'publictrack.wsgi.application'

# =============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='publictrack'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='db'),  # Corregido para docker-compose
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 60,
        },
    }
}

# =============================================================================
# CONFIGURACIÓN DE CACHE - OPCIONAL
# =============================================================================

# Simplificado - solo si tienes Redis funcionando
try:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL', default='redis://redis:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'publictrack',
            'TIMEOUT': 300,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
except:
    # Fallback a sesiones en DB si Redis falla
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# =============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN
# =============================================================================

LOGIN_URL = 'authentication:login'
LOGIN_REDIRECT_URL = '/panel/'  
LOGOUT_REDIRECT_URL = '/panel/'

SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=1209600, cast=int)  # 2 semanas
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=False, cast=bool)
SESSION_SAVE_EVERY_REQUEST = config('SESSION_SAVE_EVERY_REQUEST', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# =============================================================================
# VALIDACIÓN DE CONTRASEÑAS
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'first_name', 'last_name', 'email'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =============================================================================
# INTERNACIONALIZACIÓN
# =============================================================================

LANGUAGE_CODE = config('LANGUAGE_CODE', default='es-es')
TIME_ZONE = config('TIME_ZONE', default='America/Lima')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# =============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA
# =============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=5242880, cast=int)  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# =============================================================================
# CONFIGURACIÓN PWA (Progressive Web App) - django-pwa
# =============================================================================

PWA_APP_NAME = 'PublicTrack'
PWA_APP_DESCRIPTION = 'Sistema integral de gestión para emisoras de radio'
PWA_APP_THEME_COLOR = '#1976d2'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_LANG = 'es-ES'
PWA_APP_DIR = 'ltr'
PWA_APP_ICONS = [
    {
        'src': '/static/icons/icon-72x72.png',
        'sizes': '72x72',
        'type': 'image/png'
    },
    {
        'src': '/static/icons/icon-96x96.png',
        'sizes': '96x96',
        'type': 'image/png'
    },
    {
        'src': '/static/icons/icon-128x128.png',
        'sizes': '128x128',
        'type': 'image/png'
    },
    {
        'src': '/static/icons/icon-144x144.png',
        'sizes': '144x144',
        'type': 'image/png'
    },
    {
        'src': '/static/icons/icon-152x152.png',
        'sizes': '152x152',
        'type': 'image/png'
    },
    {
        'src': '/static/icons/icon-192x192.png',
        'sizes': '192x192',
        'type': 'image/png',
        'purpose': 'any maskable'
    },
    {
        'src': '/static/icons/icon-384x384.png',
        'sizes': '384x384',
        'type': 'image/png'
    },
    {
        'src': '/static/icons/icon-512x512.png',
        'sizes': '512x512',
        'type': 'image/png',
        'purpose': 'any maskable'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/icons/icon-192x192.png',
        'sizes': '192x192',
        'type': 'image/png'
    }
]
PWA_APP_SPLASH_SCREEN = [
    {
        'src': '/static/images/splash-640x1136.png',
        'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/images/splash-750x1334.png',
        'media': '(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/images/splash-1242x2208.png',
        'media': '(device-width: 414px) and (device-height: 736px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/images/splash-1125x2436.png',
        'media': '(device-width: 375px) and (device-height: 812px) and (-webkit-device-pixel-ratio: 3)'
    },
    {
        'src': '/static/images/splash-1536x2048.png',
        'media': '(device-width: 768px) and (device-height: 1024px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/images/splash-1668x2224.png',
        'media': '(device-width: 834px) and (device-height: 1112px) and (-webkit-device-pixel-ratio: 2)'
    },
    {
        'src': '/static/images/splash-2048x2732.png',
        'media': '(device-width: 1024px) and (device-height: 1366px) and (-webkit-device-pixel-ratio: 2)'
    }
]
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static', 'serviceworker.js')
PWA_APP_DEBUG_MODE = DEBUG  # Muestra errores en desarrollo

# Shortcuts para la PWA
PWA_APP_SHORTCUTS = [
    {
        'name': 'Nueva Cuña',
        'short_name': 'Nueva Cuña',
        'description': 'Registrar nueva cuña publicitaria',
        'url': '/content/nueva-cuna/',
        'icons': [{'src': '/static/icons/icon-96x96.png', 'sizes': '96x96'}]
    },
    {
        'name': 'Transmisiones',
        'short_name': 'Transmisiones',
        'description': 'Ver programación de transmisiones',
        'url': '/transmisiones/',
        'icons': [{'src': '/static/icons/icon-96x96.png', 'sizes': '96x96'}]
    }
]

# =============================================================================
# CONFIGURACIÓN DE EMAIL
# =============================================================================

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@publictrack.com')

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD
# =============================================================================

SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# LOGGING - SIMPLIFICADO SIN ERRORES
# =============================================================================

# Desactivar logging personalizado problemático
LOGGING_CONFIG = None

# Logging básico solo para desarrollo
import logging
if DEBUG:
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s %(asctime)s %(message)s',
        handlers=[logging.StreamHandler()]
    )

# =============================================================================
# CONFIGURACIÓN DE DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': config('API_PAGE_SIZE', default=20, cast=int),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DATETIME_FORMAT': '%d/%m/%Y %H:%M:%S',
    'DATE_FORMAT': '%d/%m/%Y',
    'TIME_FORMAT': '%H:%M:%S',
    'USE_TZ': True,
}

# =============================================================================
# CONFIGURACIÓN DE CORS
# =============================================================================

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000',
    cast=Csv()
)

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

# =============================================================================
# CONFIGURACIONES ESPECÍFICAS DE PUBLICTRACK
# =============================================================================

# Configuración de archivos de audio
AUDIO_UPLOAD_PATH = 'audio_spots/'
MAX_AUDIO_UPLOAD_SIZE = config('MAX_AUDIO_UPLOAD_SIZE', default=50 * 1024 * 1024, cast=int)  # 50MB
AUDIO_FORMATS_ALLOWED = config('AUDIO_FORMATS_ALLOWED', default='.mp3,.wav,.aac,.m4a,.ogg', cast=Csv())

# Formatos de fecha y hora personalizados
DATETIME_FORMAT = 'd/m/Y H:i:s'
DATE_FORMAT = 'd/m/Y'
TIME_FORMAT = 'H:i:s'
USE_L10N = False

# Configuración para el sistema de transmisiones
TRANSMISSION_SCHEDULE_INTERVAL = config('TRANSMISSION_SCHEDULE_INTERVAL', default=15, cast=int)
TRANSMISSION_OVERLAP_TOLERANCE = config('TRANSMISSION_OVERLAP_TOLERANCE', default=5, cast=int)

# Configuración para reportes
REPORTS_CACHE_TIMEOUT = config('REPORTS_CACHE_TIMEOUT', default=3600, cast=int)
REPORTS_EXPORT_FORMATS = ['pdf', 'xlsx', 'csv']

# Configuración del sistema de semáforos
TRAFFIC_LIGHT_COLORS = {
    'verde': '#28a745',    # Pagado/Transmitido
    'amarillo': '#ffc107', # Pendiente/Por vencer
    'rojo': '#dc3545',     # Vencido/Error
}

# Configuración financiera
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='PEN')
TAX_RATE = config('TAX_RATE', default=18.0, cast=float)
INVOICE_NUMBER_PREFIX = config('INVOICE_NUMBER_PREFIX', default='FT-')
RECEIPT_NUMBER_PREFIX = config('RECEIPT_NUMBER_PREFIX', default='RC-')

# Configuración de comisiones
DEFAULT_COMMISSION_RATE = config('DEFAULT_COMMISSION_RATE', default=10.0, cast=float)
MIN_COMMISSION_RATE = config('MIN_COMMISSION_RATE', default=0.0, cast=float)
MAX_COMMISSION_RATE = config('MAX_COMMISSION_RATE', default=50.0, cast=float)

# Configuración de créditos
DEFAULT_CREDIT_DAYS = config('DEFAULT_CREDIT_DAYS', default=30, cast=int)
MAX_CREDIT_LIMIT = config('MAX_CREDIT_LIMIT', default=50000.0, cast=float)

# =============================================================================
# CONFIGURACIÓN DE DESARROLLO
# =============================================================================

if DEBUG:
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
        '0.0.0.0',
    ]
    
    # Email en consola para desarrollo - FORZADO
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    # Configuraciones adicionales de desarrollo
    CORS_ALLOW_ALL_ORIGINS = True  # Solo para desarrollo
    
else:
    # Configuraciones para producción
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# =============================================================================
# CONFIGURACIÓN ADICIONAL PERSONALIZADA
# =============================================================================

APP_VERSION = config('APP_VERSION', default='1.0.0')
COMPANY_NAME = config('COMPANY_NAME', default='PubliTrack')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# MENSAJE DE CONFIRMACIÓN
# =============================================================================

print("✅ Settings de PubliTrack cargados correctamente")
print("📱 PWA con django-pwa configurada")
print("🆕 Nuevas apps integradas: orders, parte_mortorios")
if DEBUG:
    print(f"🔧 Modo: DESARROLLO")
    print(f"🗄️  Base de datos: {DATABASES['default']['NAME']} en {DATABASES['default']['HOST']}")
    print(f"📧 Email backend: {EMAIL_BACKEND}")
else:
    print(f"🚀 Modo: PRODUCCIÓN")
    print(f"🔒 Configuraciones de seguridad activadas")