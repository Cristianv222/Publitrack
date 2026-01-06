
from django.core.management.base import BaseCommand
from apps.orders.models import OrdenToma, OrdenProduccion, OrdenAutorizacion, OrdenSuspension
from apps.authentication.models import CustomUser

class Command(BaseCommand):
    help = 'Corrige y asigna vendedores a las órdenes existentes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Iniciando corrección de vendedores asignados..."))
        
        # 1. Corregir Ordenes de Toma
        self.stdout.write("\n📦 Verificando Órdenes de Toma...")
        ordenes_toma = OrdenToma.objects.all()
        count_toma = 0
        for orden in ordenes_toma:
            if orden.cliente and orden.cliente.vendedor_asignado:
                # Si no tiene vendedor o es diferente al del cliente (prioridad al actual del cliente)
                # Nota: Podríamos solo actualizar si está VACÍO para no sobrescribir históricos,
                # pero el usuario pide que "jale bien la información", asumiendo corrección.
                # Vamos a actualizar si está vacío O si queremos forzar sincronización.
                # Por seguridad, solo si está vacío.
                if not orden.vendedor_asignado:
                    orden.vendedor_asignado = orden.cliente.vendedor_asignado
                    orden.save(update_fields=['vendedor_asignado'])
                    count_toma += 1
                    self.stdout.write(f"   - OT {orden.codigo} actualizada con {orden.cliente.vendedor_asignado}")
        self.stdout.write(self.style.SUCCESS(f"✅ {count_toma} Órdenes de Toma actualizadas."))

        # 2. Corregir Órdenes de Producción
        self.stdout.write("\n🏭 Verificando Órdenes de Producción...")
        ordenes_prod = OrdenProduccion.objects.all()
        count_prod = 0
        for orden in ordenes_prod:
            vendedor_correcto = None
            if orden.orden_toma and orden.orden_toma.vendedor_asignado:
                vendedor_correcto = orden.orden_toma.vendedor_asignado
            elif orden.orden_toma and orden.orden_toma.cliente and orden.orden_toma.cliente.vendedor_asignado:
                vendedor_correcto = orden.orden_toma.cliente.vendedor_asignado
                
            if vendedor_correcto and not orden.vendedor_asignado:
                orden.vendedor_asignado = vendedor_correcto
                orden.save(update_fields=['vendedor_asignado'])
                count_prod += 1
                self.stdout.write(f"   - OP {orden.codigo} actualizada con {vendedor_correcto}")
        self.stdout.write(self.style.SUCCESS(f"✅ {count_prod} Órdenes de Producción actualizadas."))
        
        # 3. Corregir Órdenes de Autorización
        self.stdout.write("\n📝 Verificando Órdenes de Autorización...")
        ordenes_auth = OrdenAutorizacion.objects.all()
        count_auth = 0
        for orden in ordenes_auth:
            vendedor_correcto = None
            if orden.orden_produccion and orden.orden_produccion.vendedor_asignado:
                 vendedor_correcto = orden.orden_produccion.vendedor_asignado
            elif orden.cliente and orden.cliente.vendedor_asignado:
                 vendedor_correcto = orden.cliente.vendedor_asignado
                 
            if vendedor_correcto and not orden.vendedor:
                 orden.vendedor = vendedor_correcto
                 orden.save(update_fields=['vendedor'])
                 count_auth += 1
                 self.stdout.write(f"   - AUT {orden.codigo} actualizada con {vendedor_correcto}")
        self.stdout.write(self.style.SUCCESS(f"✅ {count_auth} Órdenes de Autorización actualizadas."))
        
        # 4. Corregir Órdenes de Suspensión
        self.stdout.write("\n🛑 Verificando Órdenes de Suspensión...")
        ordenes_susp = OrdenSuspension.objects.all()
        count_susp = 0
        for orden in ordenes_susp:
            vendedor_correcto = None
            if orden.cliente and orden.cliente.vendedor_asignado:
                vendedor_correcto = orden.cliente.vendedor_asignado
                
            if vendedor_correcto and not orden.vendedor_asignado:
                orden.vendedor_asignado = vendedor_correcto
                orden.save(update_fields=['vendedor_asignado'])
                count_susp += 1
                self.stdout.write(f"   - SUSP {orden.codigo} actualizada con {vendedor_correcto}")
        self.stdout.write(self.style.SUCCESS(f"✅ {count_susp} Órdenes de Suspensión actualizadas."))
