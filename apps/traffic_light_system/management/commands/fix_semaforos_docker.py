from django.core.management.base import BaseCommand
from django.utils import timezone
import os

class Command(BaseCommand):
    help = 'Reparar semáforos - Versión Docker'

    def handle(self, *args, **options):
        self.stdout.write("🐳 INICIANDO REPARACIÓN EN DOCKER...")
        self.stdout.write(f"📁 Entorno: {os.environ.get('DJANGO_SETTINGS_MODULE', 'No configurado')}")
        
        try:
            from apps.content_management.models import CuñaPublicitaria
            from apps.traffic_light_system.utils.status_calculator import StatusCalculator
            
            calculator = StatusCalculator()
            cuñas = CuñaPublicitaria.objects.all()
            
            self.stdout.write(f"📊 Encontradas {cuñas.count()} cuñas")
            
            success_count = 0
            error_count = 0
            
            for i, cuña in enumerate(cuñas, 1):
                try:
                    estado_anterior = getattr(cuña.estado_semaforo, 'color_actual', 'N/A') if hasattr(cuña, 'estado_semaforo') and cuña.estado_semaforo else 'N/A'
                    
                    estado_semaforo = calculator.actualizar_estado_cuña(cuña, crear_historial=True)
                    
                    if estado_anterior != estado_semaforo.color_actual:
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ [{i}/{len(cuñas)}] {cuña.codigo}: {estado_anterior} → {estado_semaforo.color_actual}")
                        )
                    else:
                        self.stdout.write(f"🔵 [{i}/{len(cuñas)}] {cuña.codigo}: Sin cambios ({estado_semaforo.color_actual})")
                    
                    success_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"❌ [{i}/{len(cuñas)}] {cuña.codigo}: {str(e)}")
                    )
                    error_count += 1
            
            # Resumen
            self.stdout.write("\n" + "="*60)
            self.stdout.write(
                self.style.SUCCESS(
                    f"🎯 RESULTADO FINAL:\n"
                    f"   • Éxitos: {success_count}\n"
                    f"   • Errores: {error_count}\n"
                    f"   • Total: {len(cuñas)}"
                )
            )
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"📦 Error de importación: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"💥 Error general: {e}"))