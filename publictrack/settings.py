"""
Django settings for publictrack project.
Sistema de gestión de publicidad radial - PubliTrack
VERSIÓN PARA PRODUCCIÓN - CON WHITENOISE
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
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['*']

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
    'pwa',
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
    'apps.orders',
    'apps.parte_mortorios',
    'apps.programacion_canal',
    'apps.grilla_publicitaria',
    'apps.inventory',
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
        'NAME': config('DB_NAME', default='publictrack_prod'),
        'USER': config('DB_USER', default='publictrack_user'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
    }
}

# =============================================================================
# CONFIGURACIÓN DE CACHE - CORREGIDA
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/1'),
        'KEY_PREFIX': 'publictrack',
        'TIMEOUT': 300,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# =============================================================================
# CONFIGURACIÓN DE AUTENTICACIÓN - MEJORADA PARA PRODUCCIÓN
# =============================================================================

LOGIN_URL = 'authentication:login'
LOGIN_REDIRECT_URL = '/panel/'
LOGOUT_REDIRECT_URL = '/'

SESSION_COOKIE_AGE = 1209600  # 2 semanas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='https://publictrack.fronteratech.ec', cast=Csv())

# =============================================================================
# VALIDACIÓN DE CONTRASEÑAS - REFORZADA
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10},
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
TIME_ZONE = config('TIME_ZONE', default='America/Guayaquil')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# =============================================================================
# ARCHIVOS ESTÁTICOS Y MEDIA - CONFIGURACIÓN CORREGIDA PARA WHITENOISE
# =============================================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# CONFIGURACIÓN WHITENOISE MEJORADA
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# =============================================================================
# CONFIGURACIÓN DE ARCHIVOS MEDIA
# =============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644

# CONFIGURACIÓN ADICIONAL PARA SERVIR MEDIA EN PRODUCCIÓN
# Esta configuración permite que Django sirva archivos media de forma segura
# en producción sin necesidad de nginx adicional
WHITENOISE_AUTOREFRESH = DEBUG  # Solo auto-refresh en desarrollo
WHITENOISE_ADD_HEADERS_FUNCTION = None  # Puedes personalizar headers si lo necesitas

# =============================================================================
# CONFIGURACIÓN PWA - CORREGIDA
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
PWA_APP_ICONS = [
    {
        'src': '/static/icons/icon-192x192.png',
        'sizes': '192x192',
        'type': 'image/png'
    },
    {
        'src': '/static/icons/icon-512x512.png',
        'sizes': '512x512',
        'type': 'image/png'
    }
]
PWA_APP_ICONS_APPLE = [
    {
        'src': '/static/icons/icon-192x192.png',
        'sizes': '192x192',
    }
]
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static', 'serviceworker.js')

# =============================================================================
# CONFIGURACIÓN DE EMAIL - PARA PRODUCCIÓN
# =============================================================================

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@publictrack.fronteratech.ec')

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD - PARA PRODUCCIÓN
# =============================================================================

# Configuraciones de seguridad básicas
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'

# Configuraciones SSL (se activan solo en producción)
if not DEBUG:
    #     SECURE_SSL_REDIRECT = False
    #     SESSION_COOKIE_SECURE = False
    #     CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    #     SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =============================================================================
# LOGGING - CONFIGURADO PARA PRODUCCIÓN
# =============================================================================

# Crear directorio de logs si no existe
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

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
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ] if not DEBUG else [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# =============================================================================
# CONFIGURACIÓN DE CORS - RESTRINGIDA EN PRODUCCIÓN
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "https://publictrack.fronteratech.ec",
]

if DEBUG:
    CORS_ALLOWED_ORIGINS.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000", 
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ])

CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# CONFIGURACIONES ESPECÍFICAS DE PUBLICTRACK
# =============================================================================

# Configuración de archivos de audio
AUDIO_UPLOAD_PATH = 'audio_spots/'
MAX_AUDIO_UPLOAD_SIZE = config('MAX_AUDIO_UPLOAD_SIZE', default=50 * 1024 * 1024, cast=int)
AUDIO_FORMATS_ALLOWED = ['mp3', 'wav', 'aac', 'm4a', 'ogg']

# Configuración financiera
DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='USD')
TAX_RATE = config('TAX_RATE', default=12.0, cast=float)

# =============================================================================
# CONFIGURACIÓN FINAL
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Mensaje de confirmación
if DEBUG:
    print("=" * 80)
    print(" Settings de PubliTrack - MODO DESARROLLO")
    print(" PWA configurada")
    print(" Whitenoise activado para archivos estáticos")
    print(" Media files servidos por Django")
    print("=" * 80)
else:
    print("=" * 80)
    print(" Settings de PubliTrack - MODO PRODUCCIÓN")
    print(" Configuraciones de seguridad activadas")
    print(" Email configurado para SMTP")
    print(" Dominio: publictrack.fronteratech.ec")
    print(" Media files servidos mediante Django (no se requiere nginx)")
    print("=" * 80)