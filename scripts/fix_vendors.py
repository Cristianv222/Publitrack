
import os
import sys
import django

# Setup Django environment
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'publitrack.settings')
django.setup()

from apps.orders.models import OrdenToma, OrdenProduccion, OrdenAutorizacion, OrdenSuspension
from apps.authentication.models import CustomUser

def fix_vendors():
    print("🚀 Iniciando corrección de vendedores asignados...")
    
    # 1. Corregir Ordenes de Toma
    print("\n📦 Verificando Órdenes de Toma...")
    ordenes_toma = OrdenToma.objects.all()
    count_toma = 0
    for orden in ordenes_toma:
        if orden.cliente and orden.cliente.vendedor_asignado:
            if orden.vendedor_asignado != orden.cliente.vendedor_asignado:
                print(f"   - Actualizando OT {orden.codigo}: {orden.cliente.vendedor_asignado}")
                orden.vendedor_asignado = orden.cliente.vendedor_asignado
                orden.save(update_fields=['vendedor_asignado'])
                count_toma += 1
    print(f"✅ {count_toma} Órdenes de Toma actualizadas.")

    # 2. Corregir Órdenes de Producción
    print("\n🏭 Verificando Órdenes de Producción...")
    ordenes_prod = OrdenProduccion.objects.all()
    count_prod = 0
    for orden in ordenes_prod:
        # Intentar obtener vendedor de la OT o del Cliente (a través de OT)
        vendedor_correcto = None
        if orden.orden_toma and orden.orden_toma.vendedor_asignado:
            vendedor_correcto = orden.orden_toma.vendedor_asignado
        elif orden.orden_toma and orden.orden_toma.cliente and orden.orden_toma.cliente.vendedor_asignado:
            vendedor_correcto = orden.orden_toma.cliente.vendedor_asignado
            
        if vendedor_correcto and orden.vendedor_asignado != vendedor_correcto:
            print(f"   - Actualizando OP {orden.codigo}: {vendedor_correcto}")
            orden.vendedor_asignado = vendedor_correcto
            orden.save(update_fields=['vendedor_asignado'])
            count_prod += 1
    print(f"✅ {count_prod} Órdenes de Producción actualizadas.")
    
    # 3. Corregir Órdenes de Autorización
    print("\n📝 Verificando Órdenes de Autorización...")
    ordenes_auth = OrdenAutorizacion.objects.all()
    count_auth = 0
    for orden in ordenes_auth:
        vendedor_correcto = None
        # Prioridad: Orden Producción -> Cliente
        if orden.orden_produccion and orden.orden_produccion.vendedor_asignado:
             vendedor_correcto = orden.orden_produccion.vendedor_asignado
        elif orden.cliente and orden.cliente.vendedor_asignado:
             vendedor_correcto = orden.cliente.vendedor_asignado
             
        if vendedor_correcto and orden.vendedor != vendedor_correcto:
             print(f"   - Actualizando AUT {orden.codigo}: {vendedor_correcto}")
             orden.vendedor = vendedor_correcto
             orden.save(update_fields=['vendedor'])
             count_auth += 1
    print(f"✅ {count_auth} Órdenes de Autorización actualizadas.")
    
    # 4. Corregir Órdenes de Suspensión
    print("\n🛑 Verificando Órdenes de Suspensión...")
    ordenes_susp = OrdenSuspension.objects.all()
    count_susp = 0
    for orden in ordenes_susp:
        vendedor_correcto = None
        if orden.cliente and orden.cliente.vendedor_asignado:
            vendedor_correcto = orden.cliente.vendedor_asignado
            
        if vendedor_correcto and orden.vendedor_asignado != vendedor_correcto:
            print(f"   - Actualizando SUSP {orden.codigo}: {vendedor_correcto}")
            orden.vendedor_asignado = vendedor_correcto
            orden.save(update_fields=['vendedor_asignado'])
            count_susp += 1
    print(f"✅ {count_susp} Órdenes de Suspensión actualizadas.")
    
    print("\n✨ Proceso finalizado.")

if __name__ == '__main__':
    fix_vendors()
