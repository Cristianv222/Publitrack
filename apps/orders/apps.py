"""
Configuración de la aplicación Orders
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuración de la app de Órdenes
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Gestión de Órdenes'
    
    def ready(self):
        """
        Método que se ejecuta cuando la aplicación está lista
        Aquí importamos las señales para que se registren
        """
        try:
            # Importar señales para que se registren automáticamente
            from . import signals
            print("✅ Señales de Órdenes registradas correctamente")
        except ImportError as e:
            print(f"⚠️ No se pudieron cargar las señales: {e}")
            # Intentar importar desde models como fallback
            try:
                # Las señales ahora están en signals.py, pero por compatibilidad
                from .models import OrdenToma, HistorialOrden
                print("✅ Modelos de órdenes cargados correctamente")
            except Exception as e2:
                print(f"❌ Error cargando modelos: {e2}")