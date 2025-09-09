#!/bin/bash

echo "Esperando a que la base de datos esté disponible..."

# Función para verificar si PostgreSQL está listo
wait_for_db() {
    echo "Verificando conexión a la base de datos..."
    python << END
import sys
import psycopg2
import time
import os

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'db'),
            port=os.environ.get('DB_PORT', '5432'),
            user=os.environ.get('DB_USER', 'postgres'),           # ← Corregido
            password=os.environ.get('DB_PASSWORD', 'postgres'),   # ← Corregido
            database=os.environ.get('DB_NAME', 'publictrack')
        )
        conn.close()
        print("¡Base de datos disponible!")
        sys.exit(0)
    except psycopg2.OperationalError:
        attempt += 1
        print(f"Intento {attempt}/{max_attempts}. Esperando base de datos...")
        time.sleep(2)

print("No se pudo conectar a la base de datos después de varios intentos")
sys.exit(1)
END
}

# Esperar a que la base de datos esté disponible
wait_for_db

# Verificar si es la primera vez (no existen migraciones de authentication)
if [ ! -f "/app/apps/authentication/migrations/0001_initial.py" ]; then
    echo "Primera inicialización detectada..."
    
    # PASO 1: Crear migraciones para authentication primero
    echo "Creando migraciones para authentication..."
    python manage.py makemigrations authentication
    
    # PASO 2: Crear migraciones para otras apps
    echo "Creando migraciones para otras apps..."
    python manage.py makemigrations
    
    # PASO 3: Aplicar migraciones
    echo "Aplicando migraciones..."
    python manage.py migrate --noinput
    
    echo "Creando superusuario..."
    python manage.py shell << 'EOF'
from apps.authentication.models import CustomUser
if not CustomUser.objects.filter(username='admin').exists():
    CustomUser.objects.create_superuser(
        username='admin',
        email='admin@publictrack.com',
        password='admin123',
        first_name='Administrador',
        last_name='Sistema'
    )
    print("✅ Superusuario 'admin' creado")
    print("📧 Email: admin@publictrack.com") 
    print("🔑 Password: admin123")
EOF

else
    echo "Sistema ya inicializado, aplicando migraciones pendientes..."
    python manage.py makemigrations
    python manage.py migrate --noinput
fi

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Creando directorios necesarios..."
mkdir -p logs media/audio_spots media/documents media/uploads

echo "Configuración completada. Iniciando aplicación..."
exec "$@"