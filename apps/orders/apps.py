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
        # Importar señales para que se registren automáticamente
        import apps.orders.models  # Esto registra las señales definidas en models.py
        print("✓ Señales de Órdenes registradas correctamente")
