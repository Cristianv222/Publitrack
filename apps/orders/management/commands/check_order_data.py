from django.core.management.base import BaseCommand
from apps.orders.models import OrdenToma

class Command(BaseCommand):
    help = 'Verifica los datos de producción en las órdenes'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando datos de producción en órdenes...")
        
        ordenes_completadas = OrdenToma.objects.filter(estado='completado')
        
        self.stdout.write(f"📊 Órdenes completadas: {ordenes_completadas.count()}")
        
        for orden in ordenes_completadas:
            self.stdout.write(f"\n📋 Orden: {orden.codigo}")
            self.stdout.write(f"   Proyecto/Campaña: {orden.proyecto_campania or 'No definido'}")
            self.stdout.write(f"   Título Material: {orden.titulo_material or 'No definido'}")
            self.stdout.write(f"   Descripción Breve: {orden.descripcion_breve or 'No definido'}")
            self.stdout.write(f"   Locaciones: {orden.locaciones or 'No definido'}")
            self.stdout.write(f"   Equipo: {orden.equipo_asignado or 'No definido'}")
            self.stdout.write(f"   Fecha Inicio: {orden.fecha_produccion_inicio or 'No definido'}")
            self.stdout.write(f"   Fecha Fin: {orden.fecha_produccion_fin or 'No definido'}")
            
            if orden.proyecto_campania:
                self.stdout.write(self.style.SUCCESS("   ✅ Tiene datos de producción completos"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️ Sin datos de producción completos"))