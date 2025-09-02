# PowerShell script para crear estructura básica de PublicTrack

Write-Host "Creando estructura básica para PublicTrack..." -ForegroundColor Green

# Crear directorio principal apps
New-Item -ItemType Directory -Path "apps" -Force | Out-Null

# Lista de aplicaciones
$apps = @(
    "authentication",
    "financial_management",
    "content_management",
    "traffic_light_system",
    "transmission_control",
    "notifications",
    "sales_management",
    "reports_analytics",
    "system_configuration"
)

# Crear directorios para las apps primero
Write-Host "Creando directorios para las apps..." -ForegroundColor Yellow
foreach ($app in $apps) {
    New-Item -ItemType Directory -Path "apps/$app" -Force | Out-Null
}

# Crear aplicaciones Django
Write-Host "Creando apps Django..." -ForegroundColor Yellow
foreach ($app in $apps) {
    Write-Host "   Creando $app" -ForegroundColor White
    python manage.py startapp $app "apps/$app"
}

Write-Host "Creando estructura de directorios..." -ForegroundColor Yellow

# Directorios principales
$directories = @(
    "static/css",
    "static/js", 
    "static/images",
    "static/audio",
    "media/audio_spots",
    "media/documents",
    "media/uploads",
    "templates/dashboard",
    "templates/financial",
    "templates/content",
    "templates/transmissions",
    "templates/sales",
    "templates/reports",
    "utils",
    "tests/test_financial",
    "tests/test_content",
    "tests/test_transmissions",
    "tests/test_sales",
    "tests/fixtures",
    "logs"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Subdirectorios específicos por app
$appDirectories = @(
    "apps/financial_management/utils",
    "apps/content_management/storage",
    "apps/traffic_light_system/utils",
    "apps/transmission_control/scheduler",
    "apps/notifications/services",
    "apps/sales_management/commission",
    "apps/reports_analytics/generators",
    "apps/system_configuration/management/commands"
)

foreach ($dir in $appDirectories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

Write-Host "Creando archivos __init__.py..." -ForegroundColor Yellow

# __init__.py principales
$initFiles = @(
    "apps/__init__.py",
    "utils/__init__.py",
    "tests/__init__.py"
)

foreach ($file in $initFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

# __init__.py para subdirectorios de apps
$appInitFiles = @(
    "apps/financial_management/utils/__init__.py",
    "apps/content_management/storage/__init__.py",
    "apps/traffic_light_system/utils/__init__.py",
    "apps/transmission_control/scheduler/__init__.py",
    "apps/notifications/services/__init__.py",
    "apps/sales_management/commission/__init__.py",
    "apps/reports_analytics/generators/__init__.py",
    "apps/system_configuration/management/__init__.py",
    "apps/system_configuration/management/commands/__init__.py"
)

foreach ($file in $appInitFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

Write-Host "Creando archivos específicos vacíos..." -ForegroundColor Yellow

# Lista de archivos Python específicos
$pythonFiles = @(
    # Financial Management
    "apps/financial_management/utils/accounting.py",
    "apps/financial_management/utils/calculations.py",
    
    # Content Management
    "apps/content_management/storage/audio_handlers.py",
    
    # Traffic Light System
    "apps/traffic_light_system/utils/status_calculator.py",
    
    # Transmission Control
    "apps/transmission_control/scheduler/transmission_scheduler.py",
    "apps/transmission_control/scheduler/monitoring.py",
    
    # Notifications
    "apps/notifications/services/email_service.py",
    "apps/notifications/services/sms_service.py",
    "apps/notifications/services/push_notifications.py",
    
    # Sales Management
    "apps/sales_management/commission/calculator.py",
    
    # Reports Analytics
    "apps/reports_analytics/generators/financial_reports.py",
    "apps/reports_analytics/generators/operational_reports.py",
    "apps/reports_analytics/generators/dashboard_data.py",
    
    # System Configuration
    "apps/system_configuration/management/commands/setup_initial_data.py",
    "apps/system_configuration/management/commands/backup_system.py",
    
    # Utils generales
    "utils/permissions.py",
    "utils/mixins.py",
    "utils/validators.py",
    "utils/helpers.py"
)

foreach ($file in $pythonFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

# Templates
$templateFiles = @(
    "templates/base.html",
    "templates/dashboard/index.html",
    "templates/financial/dashboard.html",
    "templates/content/library.html",
    "templates/transmissions/schedule.html",
    "templates/sales/reports.html",
    "templates/reports/analytics.html"
)

foreach ($file in $templateFiles) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

Write-Host "Estructura básica creada exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "Estructura creada:" -ForegroundColor Cyan
Write-Host "   - apps/ (con 9 aplicaciones Django)" -ForegroundColor White
Write-Host "   - static/ (css, js, images, audio)" -ForegroundColor White
Write-Host "   - media/ (audio_spots, documents, uploads)" -ForegroundColor White
Write-Host "   - templates/ (con subdirectorios por módulo)" -ForegroundColor White
Write-Host "   - utils/ (archivos de utilidades)" -ForegroundColor White
Write-Host "   - tests/ (estructura de pruebas)" -ForegroundColor White
Write-Host "   - logs/ (para archivos de log)" -ForegroundColor White
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Magenta
Write-Host "   1. Configura settings.py para incluir las apps" -ForegroundColor Yellow
Write-Host "   2. python manage.py makemigrations" -ForegroundColor Yellow
Write-Host "   3. python manage.py migrate" -ForegroundColor Yellow