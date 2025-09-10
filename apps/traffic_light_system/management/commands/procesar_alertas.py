"""
Management command para generar y procesar alertas automáticas
Sistema PubliTrack - Gestión automatizada de alertas
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.traffic_light_system.utils.status_calculator import AlertasManager
from apps.traffic_light_system.models import AlertaSemaforo, EstadoSemaforo
from datetime import timedelta


class Command(BaseCommand):
    help = 'Genera y procesa alertas automáticas del sistema de semáforos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--generar',
            action='store_true',
            help='Generar nuevas alertas para estados que las requieren'
        )
        
        parser.add_argument(
            '--procesar-pendientes',
            action='store_true',
            help='Procesar alertas pendientes de envío'
        )
        
        parser.add_argument(
            '--reintentar-errores',
            action='store_true',
            help='Reintentar alertas que fallaron en el envío'
        )
        
        parser.add_argument(
            '--limpiar-antiguas',
            action='store_true',
            help='Limpiar alertas antiguas procesadas'
        )
        
        parser.add_argument(
            '--solo-criticas',
            action='store_true',
            help='Solo procesar alertas críticas y de error'
        )
        
        parser.add_argument(
            '--dias-antiguedad',
            type=int,
            default=30,
            help='Días de antigüedad para considerar alertas como "antiguas" (default: 30)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular ejecución sin hacer cambios reales'
        )
    
    def handle(self, *args, **options):
        if not any([
            options['generar'],
            options['procesar_pendientes'], 
            options['reintentar_errores'],
            options['limpiar_antiguas']
        ]):
            # Si no se especifica acción, hacer todo por defecto
            options['generar'] = True
            options['procesar_pendientes'] = True
            options['reintentar_errores'] = True
        
        manager = AlertasManager()
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO SIMULACIÓN - No se harán cambios reales"))
        
        # Generar nuevas alertas
        if options['generar']:
            self.stdout.write("Generando nuevas alertas...")
            
            if dry_run:
                # Contar estados que requieren alerta
                estados_pendientes = EstadoSemaforo.objects.filter(
                    requiere_alerta=True,
                    alerta_enviada=False
                ).count()
                self.stdout.write(f"Se generarían alertas para {estados_pendientes} estados")
            else:
                try:
                    stats = manager.generar_alertas_pendientes()
                    self.stdout.write(
                        f"Alertas generadas: {stats['alertas_creadas']}, "
                        f"Errores: {stats['errores']}"
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error generando alertas: {str(e)}")
                    )
        
        # Procesar alertas pendientes
        if options['procesar_pendientes']:
            self.stdout.write("Procesando alertas pendientes...")
            
            filtros = {'estado': 'pendiente'}
            
            if options['solo_criticas']:
                filtros['severidad__in'] = ['critical', 'error']
            
            # Filtrar por fecha programada (solo las que ya deberían enviarse)
            alertas_query = AlertaSemaforo.objects.filter(
                **filtros,
                fecha_programada__lte=timezone.now()
            ) if 'fecha_programada' in AlertaSemaforo._meta.get_fields() else AlertaSemaforo.objects.filter(**filtros)
            
            alertas_pendientes = alertas_query[:100]  # Procesar máximo 100 por vez
            
            if dry_run:
                self.stdout.write(f"Se procesarían {len(alertas_pendientes)} alertas pendientes")
            else:
                procesadas = 0
                errores = 0
                
                for alerta in alertas_pendientes:
                    try:
                        # Aquí iría la lógica de envío real (email, SMS, etc.)
                        # Por ahora solo marcamos como enviada
                        alerta.marcar_como_enviada()
                        procesadas += 1
                        
                        if procesadas % 10 == 0:
                            self.stdout.write(f"Procesadas: {procesadas}")
                            
                    except Exception as e:
                        alerta.marcar_error(str(e))
                        errores += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Error procesando alerta {alerta.id}: {str(e)}"
                            )
                        )
                
                self.stdout.write(
                    f"Alertas procesadas: {procesadas}, Errores: {errores}"
                )
        
        # Reintentar alertas con error
        if options['reintentar_errores']:
            self.stdout.write("Reintentando alertas con error...")
            
            alertas_error = AlertaSemaforo.objects.filter(
                estado='error',
                reintentos__lt=3,  # Solo las que no han alcanzado el máximo de reintentos
                created_at__gte=timezone.now() - timedelta(days=7)  # Solo las de la última semana
            )
            
            if options['solo_criticas']:
                alertas_error = alertas_error.filter(severidad__in=['critical', 'error'])
            
            if dry_run:
                self.stdout.write(f"Se reintentarían {alertas_error.count()} alertas")
            else:
                reintentadas = 0
                
                for alerta in alertas_error:
                    try:
                        alerta.programar_reintento(minutos_delay=5)
                        reintentadas += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Error programando reintento para alerta {alerta.id}: {str(e)}"
                            )
                        )
                
                self.stdout.write(f"Alertas programadas para reintento: {reintentadas}")
        
        # Limpiar alertas antiguas
        if options['limpiar_antiguas']:
            self.stdout.write("Limpiando alertas antiguas...")
            
            fecha_limite = timezone.now() - timedelta(days=options['dias_antiguedad'])
            
            alertas_antiguas = AlertaSemaforo.objects.filter(
                estado__in=['enviada', 'ignorada'],
                created_at__lt=fecha_limite
            )
            
            count_antiguas = alertas_antiguas.count()
            
            if dry_run:
                self.stdout.write(f"Se eliminarían {count_antiguas} alertas antiguas")
            else:
                if count_antiguas > 0:
                    # Solo eliminar si hay más de 100 para evitar eliminar pocas alertas
                    if count_antiguas > 100:
                        deleted_count = alertas_antiguas.delete()[0]
                        self.stdout.write(f"Alertas antiguas eliminadas: {deleted_count}")
                    else:
                        self.stdout.write(
                            f"Solo {count_antiguas} alertas antiguas encontradas, "
                            "no se eliminan (mínimo 100)"
                        )
                else:
                    self.stdout.write("No se encontraron alertas antiguas para eliminar")
        
        # Mostrar estadísticas finales
        if not dry_run:
            self.stdout.write("\nEstadísticas actuales del sistema:")
            
            stats_alertas = {
                'pendientes': AlertaSemaforo.objects.filter(estado='pendiente').count(),
                'enviadas_hoy': AlertaSemaforo.objects.filter(
                    estado='enviada',
                    fecha_enviada__date=timezone.now().date()
                ).count(),
                'errores': AlertaSemaforo.objects.filter(estado='error').count(),
                'total_activas': AlertaSemaforo.objects.exclude(
                    estado__in=['enviada', 'ignorada']
                ).count()
            }
            
            self.stdout.write(f"- Alertas pendientes: {stats_alertas['pendientes']}")
            self.stdout.write(f"- Enviadas hoy: {stats_alertas['enviadas_hoy']}")
            self.stdout.write(f"- Con errores: {stats_alertas['errores']}")
            self.stdout.write(f"- Total activas: {stats_alertas['total_activas']}")
            
            # Verificar estados que requieren alerta pero no la tienen
            estados_sin_alerta = EstadoSemaforo.objects.filter(
                requiere_alerta=True,
                alerta_enviada=False
            ).count()
            
            if estados_sin_alerta > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"ATENCIÓN: {estados_sin_alerta} estados requieren alerta "
                        "pero no tienen alerta generada"
                    )
                )
        
        self.stdout.write(self.style.SUCCESS("Procesamiento de alertas completado"))