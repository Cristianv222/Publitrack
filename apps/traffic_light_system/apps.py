"""
Configuración de la aplicación Traffic Light System
Sistema PubliTrack - Sistema de semáforos para cuñas publicitarias
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class TrafficLightSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.traffic_light_system'
    verbose_name = 'Sistema de Semáforos'
    
    def ready(self):
        """
        Configuración que se ejecuta cuando la aplicación está lista
        """
        # Importar señales para registrarlas
        from . import signals
        
        # Conectar señales de post_migrate para configuración inicial
        post_migrate.connect(self.create_default_configuration, sender=self)
    
    def create_default_configuration(self, sender, **kwargs):
        """
        Crea configuración por defecto si no existe
        """
        from .models import ConfiguracionSemaforo
        
        # Solo crear si no hay configuraciones existentes
        if not ConfiguracionSemaforo.objects.exists():
            ConfiguracionSemaforo.objects.create(
                nombre="Configuración por Defecto",
                descripcion="Configuración inicial creada automáticamente por el sistema",
                tipo_calculo='combinado',
                dias_verde_min=15,
                dias_amarillo_min=7,
                porcentaje_verde_max=50.00,
                porcentaje_amarillo_max=85.00,
                estados_verde=['activa', 'aprobada'],
                estados_amarillo=['pendiente_revision', 'en_produccion', 'pausada'],
                estados_rojo=['borrador'],
                estados_gris=['finalizada', 'cancelada'],
                enviar_alertas=True,
                alertas_solo_empeoramiento=True,
                is_active=True,
                is_default=True
            )