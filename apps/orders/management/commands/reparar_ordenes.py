from django.core.management.base import BaseCommand
from apps.orders.models import OrdenToma

class Command(BaseCommand):
    help = 'Repara los datos de clientes en órdenes existentes'

    def handle(self, *args, **options):
        ordenes = OrdenToma.objects.all()
        
        for orden in ordenes:
            if orden.cliente:
                self.stdout.write(f"Reparando orden {orden.codigo}...")
                orden.copiar_datos_cliente()
                orden.save()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Orden {orden.codigo} reparada: {orden.nombre_cliente} - {orden.empresa_cliente}")
                )