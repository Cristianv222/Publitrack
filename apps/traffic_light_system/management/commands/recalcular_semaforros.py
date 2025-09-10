"""
Management command para recalcular estados de semáforo masivamente
Sistema PubliTrack - Recálculo automatizado de estados
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.traffic_light_system.utils.status_calculator import StatusCalculator
from apps.traffic_light_system.models import ConfiguracionSemaforo
from apps.content_management.models import CuñaPublicitaria
import time


class Command(BaseCommand):
    help = 'Recalcula todos los estados del sistema de semáforos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--configuracion',
            type=int,
            help='ID de configuración específica a usar (por defecto usa la activa)'
        )
        
        parser.add_argument(
            '--solo-activas',
            action='store_true',
            help='Solo recalcular cuñas activas y aprobadas'
        )
        
        parser.add_argument(
            '--cliente',
            type=int,
            help='Solo recalcular cuñas de un cliente específico'
        )
        
        parser.add_argument(
            '--vendedor',
            type=int,
            help='Solo recalcular cuñas de un vendedor específico'
        )
        
        parser.add_argument(
            '--desde-fecha',
            type=str,
            help='Solo cuñas creadas desde esta fecha (YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular ejecución sin hacer cambios reales'
        )
        
        parser.add_argument(
            '--verbosity',
            type=int,
            choices=[0, 1, 2],
            default=1,
            help='Nivel de detalle en la salida'
        )
    
    def handle(self, *args, **options):
        start_time = time.time()
        verbosity = options['verbosity']
        
        if verbosity >= 1:
            self.stdout.write("Iniciando recálculo de estados de semáforo...")
        
        try:
            # Obtener configuración
            if options['configuracion']:
                try:
                    configuracion = ConfiguracionSemaforo.objects.get(
                        id=options['configuracion']
                    )
                    if verbosity >= 1:
                        self.stdout.write(f"Usando configuración: {configuracion.nombre}")
                except ConfiguracionSemaforo.DoesNotExist:
                    raise CommandError(f"Configuración con ID {options['configuracion']} no existe")
            else:
                configuracion = ConfiguracionSemaforo.get_active()
                if verbosity >= 1:
                    self.stdout.write(f"Usando configuración activa: {configuracion.nombre}")
            
            # Crear calculadora
            calculator = StatusCalculator(configuracion)
            
            # Construir filtros
            filtros = None
            filtros_texto = []
            
            if options['solo_activas']:
                from django.db.models import Q
                filtros = Q(estado__in=['activa', 'aprobada'])
                filtros_texto.append("solo cuñas activas/aprobadas")
            
            if options['cliente']:
                from django.db.models import Q
                filtro_cliente = Q(cliente_id=options['cliente'])
                filtros = filtro_cliente if filtros is None else filtros & filtro_cliente
                filtros_texto.append(f"cliente ID {options['cliente']}")
            
            if options['vendedor']:
                from django.db.models import Q
                filtro_vendedor = Q(vendedor_asignado_id=options['vendedor'])
                filtros = filtro_vendedor if filtros is None else filtros & filtro_vendedor
                filtros_texto.append(f"vendedor ID {options['vendedor']}")
            
            if options['desde_fecha']:
                try:
                    from datetime import datetime
                    from django.db.models import Q
                    fecha = datetime.strptime(options['desde_fecha'], '%Y-%m-%d').date()
                    filtro_fecha = Q(created_at__date__gte=fecha)
                    filtros = filtro_fecha if filtros is None else filtros & filtro_fecha
                    filtros_texto.append(f"desde {fecha}")
                except ValueError:
                    raise CommandError("Formato de fecha inválido. Use YYYY-MM-DD")
            
            if filtros_texto and verbosity >= 1:
                self.stdout.write(f"Aplicando filtros: {', '.join(filtros_texto)}")
            
            # Contar cuñas a procesar
            if filtros:
                total_cuñas = CuñaPublicitaria.objects.filter(filtros).count()
            else:
                total_cuñas = CuñaPublicitaria.objects.count()
            
            if total_cuñas == 0:
                self.stdout.write(
                    self.style.WARNING("No se encontraron cuñas para procesar")
                )
                return
            
            if verbosity >= 1:
                self.stdout.write(f"Total de cuñas a procesar: {total_cuñas}")
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING(
                        f"SIMULACIÓN: Se procesarían {total_cuñas} cuñas "
                        f"con configuración '{configuracion.nombre}'"
                    )
                )
                return
            
            # Confirmar si hay muchas cuñas
            if total_cuñas > 1000 and not options.get('force'):
                confirm = input(
                    f"¿Confirma procesar {total_cuñas} cuñas? "
                    f"Esto puede tomar varios minutos. (y/N): "
                )
                if confirm.lower() not in ['y', 'yes', 'sí', 's']:
                    self.stdout.write("Operación cancelada")
                    return
            
            # Ejecutar recálculo
            stats = calculator.actualizar_todas_las_cuñas(filtros)
            
            # Mostrar resultados
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nRecálculo completado exitosamente en {execution_time:.2f} segundos"
                )
            )
            
            if verbosity >= 1:
                self.stdout.write("\nEstadísticas:")
                self.stdout.write(f"  - Total procesadas: {stats['total_procesadas']}")
                self.stdout.write(f"  - Actualizadas: {stats['actualizadas']}")
                self.stdout.write(f"  - Creadas: {stats['creadas']}")
                self.stdout.write(f"  - Cambios de color: {stats['cambios_color']}")
                self.stdout.write(f"  - Alertas generadas: {stats['alertas_generadas']}")
                self.stdout.write(f"  - Errores: {stats['errores']}")
            
            if stats['errores'] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Se encontraron {stats['errores']} errores")
                )
            
            # Mostrar resumen de estados resultantes
            if verbosity >= 2:
                resumen = calculator.obtener_estadisticas_resumen()
                self.stdout.write("\nResumen de estados resultantes:")
                self.stdout.write(f"  - Verde: {resumen['contadores']['verde']}")
                self.stdout.write(f"  - Amarillo: {resumen['contadores']['amarillo']}")
                self.stdout.write(f"  - Rojo: {resumen['contadores']['rojo']}")
                self.stdout.write(f"  - Gris: {resumen['contadores']['gris']}")
                self.stdout.write(f"  - Porcentaje con problemas: {resumen['porcentajes']['problemas']}%")
            
        except Exception as e:
            raise CommandError(f"Error durante el recálculo: {str(e)}")