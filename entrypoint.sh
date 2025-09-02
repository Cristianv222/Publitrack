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
            user=os.environ.get('DB_USER', 'publictrack_user'),
            password=os.environ.get('DB_PASSWORD', 'publictrack_password'),
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

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Creando directorios necesarios..."
mkdir -p logs media/audio_spots media/documents media/uploads

echo "Configuración completada. Iniciando aplicación..."
exec "$@"