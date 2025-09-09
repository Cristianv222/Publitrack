"""
Comando para validar la integridad del sistema de gestión de contenido
Sistema PubliTrack - Validación de datos, archivos y consistencia
"""

import os
import hashlib
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
import json

from apps.content_management.models import (
    CategoriaPublicitaria,
    TipoContrato,
    ArchivoAudio,
    CuñaPublicitaria,
    HistorialCuña
)

class Command(BaseCommand):
    help = 'Valida la integridad de datos y archivos del módulo de contenido publicitario'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Intenta corregir automáticamente los problemas encontrados',
        )
        parser.add_argument(
            '--report',
            type=str,
            help='Genera reporte en archivo JSON',
        )
        parser.add_argument(
            '--check-files',
            action='store_true',
            help='Verifica integridad de archivos físicos',
        )
        parser.add_argument(
            '--check-data',
            action='store_true',
            help='Verifica consistencia de datos',
        )
        parser.add_argument(
            '--check-orphans',
            action='store_true',
            help='Busca registros huérfanos',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Muestra información detallada',
        )
    
    def handle(self, *args, **options):
        self.verbosity = options.get('verbosity', 1)
        self.verbose = options.get('verbose', False)
        
        # Resultados de validación
        self.validation_results = {
            'timestamp': timezone.now().isoformat(),
            'checks_performed': [],
            'errors': [],
            'warnings': [],
            'info': [],
            'fixes_applied': [],
            'summary': {}
        }
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando validación de integridad del sistema...')
        )
        
        # Ejecutar validaciones según argumentos
        if options['check_files'] or not any([options['check_files'], options['check_data'], options['check_orphans']]):
            self.validate_file_integrity(options['fix'])
        
        if options['check_data'] or not any([options['check_files'], options['check_data'], options['check_orphans']]):
            self.validate_data_consistency(options['fix'])
        
        if options['check_orphans'] or not any([options['check_files'], options['check_data'], options['check_orphans']]):
            self.validate_orphaned_records(options['fix'])
        
        # Validaciones adicionales
        self.validate_business_rules()
        self.validate_system_health()
        
        # Mostrar resumen
        self.show_summary()
        
        # Generar reporte si se solicita
        if options['report']:
            self.generate_report(options['report'])
        
        # Determinar código de salida
        if self.validation_results['errors']:
            self.stdout.write(
                self.style.ERROR('❌ Validación completada con errores')
            )
            exit(1)
        elif self.validation_results['warnings']:
            self.stdout.write(
                self.style.WARNING('⚠️ Validación completada con advertencias')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Validación completada exitosamente')
            )
    
    def validate_file_integrity(self, fix=False):
        """Valida integridad de archivos de audio"""
        self.stdout.write('📁 Validando integridad de archivos...')
        self.validation_results['checks_performed'].append('file_integrity')
        
        archivos_problema = []
        archivos_sin_hash = []
        archivos_hash_incorrecto = []
        archivos_inexistentes = []
        
        for archivo in ArchivoAudio.objects.all():
            try:
                # Verificar que el archivo físico existe
                if not archivo.archivo or not os.path.isfile(archivo.archivo.path):
                    archivos_inexistentes.append({
                        'id': archivo.id,
                        'nombre': archivo.nombre_original,
                        'path': archivo.archivo.path if archivo.archivo else 'N/A'
                    })
                    continue
                
                # Verificar hash
                if not archivo.hash_archivo:
                    archivos_sin_hash.append(archivo)
                else:
                    # Calcular hash actual
                    with archivo.archivo.open('rb') as f:
                        file_hash = hashlib.sha256()
                        for chunk in iter(lambda: f.read(4096), b""):
                            file_hash.update(chunk)
                        
                        if file_hash.hexdigest() != archivo.hash_archivo:
                            archivos_hash_incorrecto.append({
                                'id': archivo.id,
                                'nombre': archivo.nombre_original,
                                'hash_db': archivo.hash_archivo,
                                'hash_actual': file_hash.hexdigest()
                            })
                
            except Exception as e:
                archivos_problema.append({
                    'id': archivo.id,
                    'nombre': archivo.nombre_original,
                    'error': str(e)
                })
        
        # Reportar problemas
        if archivos_inexistentes:
            self.add_error(f"Archivos físicos inexistentes: {len(archivos_inexistentes)}")
            if self.verbose:
                for archivo in archivos_inexistentes:
                    self.stdout.write(f"  - {archivo['nombre']} (ID: {archivo['id']})")
        
        if archivos_sin_hash:
            self.add_warning(f"Archivos sin hash: {len(archivos_sin_hash)}")
            if fix:
                self.fix_missing_hashes(archivos_sin_hash)
        
        if archivos_hash_incorrecto:
            self.add_error(f"Archivos con hash incorrecto: {len(archivos_hash_incorrecto)}")
            if self.verbose:
                for archivo in archivos_hash_incorrecto:
                    self.stdout.write(f"  - {archivo['nombre']} (Hash modificado)")
        
        if archivos_problema:
            self.add_error(f"Archivos con errores: {len(archivos_problema)}")
        
        if not any([archivos_inexistentes, archivos_sin_hash, archivos_hash_incorrecto, archivos_problema]):
            self.add_info("Todos los archivos están íntegros")
    
    def validate_data_consistency(self, fix=False):
        """Valida consistencia de datos"""
        self.stdout.write('📊 Validando consistencia de datos...')
        self.validation_results['checks_performed'].append('data_consistency')
        
        # Cuñas con fechas inconsistentes
        cuñas_fechas_malas = CuñaPublicitaria.objects.filter(
            fecha_fin__lte=F('fecha_inicio')
        )
        if cuñas_fechas_malas.exists():
            self.add_error(f"Cuñas con fechas inconsistentes: {cuñas_fechas_malas.count()}")
            if fix:
                self.fix_inconsistent_dates(cuñas_fechas_malas)
        
        # Cuñas sin categoría
        cuñas_sin_categoria = CuñaPublicitaria.objects.filter(categoria__isnull=True)
        if cuñas_sin_categoria.exists():
            self.add_warning(f"Cuñas sin categoría: {cuñas_sin_categoria.count()}")
        
        # Cuñas sin vendedor
        cuñas_sin_vendedor = CuñaPublicitaria.objects.filter(vendedor_asignado__isnull=True)
        if cuñas_sin_vendedor.exists():
            self.add_warning(f"Cuñas sin vendedor asignado: {cuñas_sin_vendedor.count()}")
        
        # Cuñas con precio cero
        cuñas_precio_cero = CuñaPublicitaria.objects.filter(precio_total__lte=0)
        if cuñas_precio_cero.exists():
            self.add_warning(f"Cuñas con precio cero o negativo: {cuñas_precio_cero.count()}")
        
        # Cuñas con duración inconsistente vs archivo de audio
        cuñas_duracion_inconsistente = []
        for cuña in CuñaPublicitaria.objects.filter(archivo_audio__isnull=False):
            if cuña.archivo_audio.duracion_segundos:
                diferencia = abs(cuña.duracion_planeada - cuña.archivo_audio.duracion_segundos)
                if diferencia > 5:  # Tolerancia de 5 segundos
                    cuñas_duracion_inconsistente.append(cuña)
        
        if cuñas_duracion_inconsistente:
            self.add_warning(f"Cuñas con duración inconsistente vs archivo: {len(cuñas_duracion_inconsistente)}")
        
        # Categorías sin cuñas
        categorias_sin_uso = CategoriaPublicitaria.objects.annotate(
            num_cuñas=Count('cuñas')
        ).filter(num_cuñas=0, is_active=True)
        
        if categorias_sin_uso.exists():
            self.add_info(f"Categorías activas sin uso: {categorias_sin_uso.count()}")
    
    def validate_orphaned_records(self, fix=False):
        """Busca registros huérfanos"""
        self.stdout.write('🔗 Validando registros huérfanos...')
        self.validation_results['checks_performed'].append('orphaned_records')
        
        # Archivos de audio sin usar
        audios_sin_uso = ArchivoAudio.objects.annotate(
            num_cuñas=Count('cuñas')
        ).filter(num_cuñas=0)
        
        if audios_sin_uso.exists():
            self.add_info(f"Archivos de audio sin usar: {audios_sin_uso.count()}")
            if fix and self.verbosity >= 2:
                self.stdout.write("  Estos archivos podrían eliminarse para liberar espacio")
        
        # Historial huérfano (cuñas eliminadas)
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM content_management_historialcuña h
                LEFT JOIN content_management_cuñapublicitaria c ON h.cuña_id = c.id
                WHERE c.id IS NULL
            """)
            historial_huerfano = cursor.fetchone()[0]
            
            if historial_huerfano > 0:
                self.add_warning(f"Registros de historial huérfanos: {historial_huerfano}")
                if fix:
                    cursor.execute("""
                        DELETE FROM content_management_historialcuña
                        WHERE cuña_id NOT IN (
                            SELECT id FROM content_management_cuñapublicitaria
                        )
                    """)
                    self.add_fix(f"Eliminados {historial_huerfano} registros de historial huérfanos")
    
    def validate_business_rules(self):
        """Valida reglas de negocio"""
        self.stdout.write('📋 Validando reglas de negocio...')
        self.validation_results['checks_performed'].append('business_rules')
        
        # Cuñas activas vencidas
        cuñas_activas_vencidas = CuñaPublicitaria.objects.filter(
            estado='activa',
            fecha_fin__lt=timezone.now().date()
        )
        
        if cuñas_activas_vencidas.exists():
            self.add_warning(f"Cuñas activas pero vencidas: {cuñas_activas_vencidas.count()}")
        
        # Cuñas con fecha de inicio futura pero estado activa
        cuñas_futuras_activas = CuñaPublicitaria.objects.filter(
            estado='activa',
            fecha_inicio__gt=timezone.now().date()
        )
        
        if cuñas_futuras_activas.exists():
            self.add_warning(f"Cuñas activas con fecha de inicio futura: {cuñas_futuras_activas.count()}")
        
        # Cuñas aprobadas hace más de 30 días sin activar
        hace_30_dias = timezone.now() - timedelta(days=30)
        cuñas_aprobadas_viejas = CuñaPublicitaria.objects.filter(
            estado='aprobada',
            fecha_aprobacion__lt=hace_30_dias
        )
        
        if cuñas_aprobadas_viejas.exists():
            self.add_info(f"Cuñas aprobadas hace más de 30 días sin activar: {cuñas_aprobadas_viejas.count()}")
    
    def validate_system_health(self):
        """Valida salud general del sistema"""
        self.stdout.write('🏥 Validando salud del sistema...')
        self.validation_results['checks_performed'].append('system_health')
        
        # Estadísticas generales
        total_cuñas = CuñaPublicitaria.objects.count()
        total_archivos = ArchivoAudio.objects.count()
        total_categorias = CategoriaPublicitaria.objects.count()
        
        self.validation_results['summary'].update({
            'total_cuñas': total_cuñas,
            'total_archivos': total_archivos,
            'total_categorias': total_categorias,
        })
        
        # Verificar directorios de media
        if hasattr(settings, 'MEDIA_ROOT'):
            audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio_spots')
            if not os.path.exists(audio_dir):
                self.add_warning(f"Directorio de audio no existe: {audio_dir}")
            elif not os.access(audio_dir, os.W_OK):
                self.add_error(f"Sin permisos de escritura en directorio de audio: {audio_dir}")
        
        # Verificar espacio en disco (si es posible)
        try:
            import shutil
            if hasattr(settings, 'MEDIA_ROOT'):
                total, used, free = shutil.disk_usage(settings.MEDIA_ROOT)
                free_gb = free // (1024**3)
                
                if free_gb < 1:  # Menos de 1GB libre
                    self.add_warning(f"Poco espacio libre en disco: {free_gb}GB")
                elif free_gb < 0.1:  # Menos de 100MB libre
                    self.add_error(f"Espacio crítico en disco: {free_gb}GB")
                else:
                    self.add_info(f"Espacio libre en disco: {free_gb}GB")
        except Exception:
            pass
    
    def fix_missing_hashes(self, archivos):
        """Corrige archivos sin hash"""
        fixed_count = 0
        for archivo in archivos:
            try:
                if archivo.archivo and os.path.isfile(archivo.archivo.path):
                    with archivo.archivo.open('rb') as f:
                        file_hash = hashlib.sha256()
                        for chunk in iter(lambda: f.read(4096), b""):
                            file_hash.update(chunk)
                        
                        archivo.hash_archivo = file_hash.hexdigest()
                        archivo.save(update_fields=['hash_archivo'])
                        fixed_count += 1
            except Exception as e:
                self.stdout.write(f"Error generando hash para {archivo.nombre_original}: {e}")
        
        if fixed_count > 0:
            self.add_fix(f"Generados {fixed_count} hashes faltantes")
    
    def fix_inconsistent_dates(self, cuñas):
        """Corrige fechas inconsistentes"""
        # Esta función requiere lógica específica del negocio
        # Por ahora solo reportamos
        self.add_info("Fechas inconsistentes requieren revisión manual")
    
    def add_error(self, message):
        """Agrega un error a los resultados"""
        self.validation_results['errors'].append(message)
        if self.verbosity >= 1:
            self.stdout.write(self.style.ERROR(f"❌ {message}"))
    
    def add_warning(self, message):
        """Agrega una advertencia a los resultados"""
        self.validation_results['warnings'].append(message)
        if self.verbosity >= 1:
            self.stdout.write(self.style.WARNING(f"⚠️ {message}"))
    
    def add_info(self, message):
        """Agrega información a los resultados"""
        self.validation_results['info'].append(message)
        if self.verbosity >= 2 or self.verbose:
            self.stdout.write(self.style.SUCCESS(f"ℹ️ {message}"))
    
    def add_fix(self, message):
        """Agrega una corrección aplicada"""
        self.validation_results['fixes_applied'].append(message)
        if self.verbosity >= 1:
            self.stdout.write(self.style.SUCCESS(f"🔧 {message}"))
    
    def show_summary(self):
        """Muestra resumen de la validación"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE VALIDACIÓN'))
        self.stdout.write('='*50)
        
        results = self.validation_results
        
        self.stdout.write(f"Verificaciones realizadas: {len(results['checks_performed'])}")
        self.stdout.write(f"Errores encontrados: {len(results['errors'])}")
        self.stdout.write(f"Advertencias: {len(results['warnings'])}")
        self.stdout.write(f"Información: {len(results['info'])}")
        self.stdout.write(f"Correcciones aplicadas: {len(results['fixes_applied'])}")
        
        if 'total_cuñas' in results['summary']:
            self.stdout.write(f"\nEstadísticas del sistema:")
            self.stdout.write(f"  Total de cuñas: {results['summary']['total_cuñas']}")
            self.stdout.write(f"  Total de archivos: {results['summary']['total_archivos']}")
            self.stdout.write(f"  Total de categorías: {results['summary']['total_categorias']}")
    
    def generate_report(self, filename):
        """Genera reporte en archivo JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(
                self.style.SUCCESS(f"📄 Reporte generado: {filename}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error generando reporte: {e}")
            )