from django.core.management.base import BaseCommand
from apps.orders.models import OrdenToma
from apps.authentication.models import CustomUser
from decimal import Decimal

class Command(BaseCommand):
    help = 'Diagnostica y repara problemas con órdenes automáticas'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Diagnóstico del sistema de órdenes...")
        
        # Contar clientes sin órdenes
        clientes_sin_orden = CustomUser.objects.filter(
            rol='cliente', 
            is_active=True
        ).exclude(
            ordenes_toma__isnull=False
        )
        
        count_sin_orden = clientes_sin_orden.count()
        self.stdout.write(f"📊 Clientes sin órdenes: {count_sin_orden}")
        
        if count_sin_orden > 0:
            self.stdout.write("🔄 Creando órdenes faltantes...")
            for cliente in clientes_sin_orden:
                try:
                    # Verificar nuevamente para evitar condiciones de carrera
                    if not OrdenToma.objects.filter(cliente=cliente).exists():
                        orden = OrdenToma.objects.create(
                            cliente=cliente,
                            detalle_productos=f'Orden de toma automática para {cliente.get_full_name() or cliente.username}',
                            cantidad=1,
                            total=Decimal('0.00'),
                            created_by=cliente,
                            estado='pendiente'
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Orden creada: {orden.codigo} para {cliente.username}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ El cliente {cliente.username} ya tiene una orden')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error creando orden para {cliente.username}: {e}')
                    )
        
        # Estadísticas finales
        total_ordenes = OrdenToma.objects.count()
        total_clientes = CustomUser.objects.filter(rol='cliente', is_active=True).count()
        
        self.stdout.write(f"\n📈 Resumen final:")
        self.stdout.write(f"   Total de clientes: {total_clientes}")
        self.stdout.write(f"   Total de órdenes: {total_ordenes}")
        
        if total_clientes > 0:
            cobertura = (total_ordenes / total_clientes) * 100
            self.stdout.write(f"   Cobertura: {cobertura:.1f}%")
        
        # Mostrar algunas órdenes de ejemplo
        self.stdout.write(f"\n📋 Últimas 5 órdenes creadas:")
        ultimas_ordenes = OrdenToma.objects.select_related('cliente').order_by('-created_at')[:5]
        for orden in ultimas_ordenes:
            self.stdout.write(f"   - {orden.codigo} | {orden.cliente.username} | {orden.estado}")