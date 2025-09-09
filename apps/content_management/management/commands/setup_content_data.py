"""
Comando para configurar datos iniciales del módulo de contenido publicitario
Sistema PubliTrack - Setup de categorías, tipos de contrato y datos base
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

from apps.content_management.models import CategoriaPublicitaria, TipoContrato

User = get_user_model()

class Command(BaseCommand):
    help = 'Configura datos iniciales para el módulo de gestión de contenido publicitario'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de datos existentes',
        )
        parser.add_argument(
            '--skip-groups',
            action='store_true',
            help='Omite la creación de grupos de usuarios',
        )
        parser.add_argument(
            '--skip-categories',
            action='store_true',
            help='Omite la creación de categorías',
        )
        parser.add_argument(
            '--skip-contracts',
            action='store_true',
            help='Omite la creación de tipos de contrato',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando configuración de datos del módulo de contenido...')
        )
        
        # Configurar grupos de usuarios
        if not options['skip_groups']:
            self.setup_user_groups(options['force'])
        
        # Configurar categorías publicitarias
        if not options['skip_categories']:
            self.setup_categories(options['force'])
        
        # Configurar tipos de contrato
        if not options['skip_contracts']:
            self.setup_contract_types(options['force'])
        
        self.stdout.write(
            self.style.SUCCESS('✅ Configuración completada exitosamente!')
        )
    
    def setup_user_groups(self, force=False):
        """Configura grupos de usuarios y permisos"""
        self.stdout.write('Configurando grupos de usuarios...')
        
        # Definir grupos y sus permisos
        groups_config = {
            'Administradores': {
                'description': 'Acceso completo al sistema',
                'permissions': ['add', 'change', 'delete', 'view']
            },
            'Supervisores': {
                'description': 'Supervisión y aprobación de contenido',
                'permissions': ['add', 'change', 'view']
            },
            'Vendedores': {
                'description': 'Gestión de ventas y cuñas asignadas',
                'permissions': ['add', 'change', 'view']
            },
            'Clientes': {
                'description': 'Acceso limitado a contenido propio',
                'permissions': ['view']
            },
            'Operadores': {
                'description': 'Operación técnica del sistema',
                'permissions': ['view']
            }
        }
        
        content_types = [
            ContentType.objects.get_for_model(CategoriaPublicitaria),
            ContentType.objects.get_for_model(TipoContrato),
            ContentType.objects.get_for_model('content_management', 'archivoaudio'),
            ContentType.objects.get_for_model('content_management', 'cuñapublicitaria'),
            ContentType.objects.get_for_model('content_management', 'historialcuña'),
        ]
        
        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created or force:
                # Limpiar permisos existentes si force=True
                if force:
                    group.permissions.clear()
                
                # Asignar permisos
                for content_type in content_types:
                    for permission_type in config['permissions']:
                        try:
                            permission = Permission.objects.get(
                                content_type=content_type,
                                codename=f'{permission_type}_{content_type.model}'
                            )
                            group.permissions.add(permission)
                        except Permission.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Permiso {permission_type}_{content_type.model} no encontrado'
                                )
                            )
                
                status = 'creado' if created else 'actualizado'
                self.stdout.write(f'  ✓ Grupo "{group_name}" {status}')
            else:
                self.stdout.write(f'  - Grupo "{group_name}" ya existe (usar --force para actualizar)')
    
    def setup_categories(self, force=False):
        """Configura categorías publicitarias base"""
        self.stdout.write('Configurando categorías publicitarias...')
        
        categories = [
            {
                'nombre': 'Comercio Local',
                'descripcion': 'Negocios y comercios locales',
                'color_codigo': '#28a745',
                'tarifa_base': Decimal('2.50')
            },
            {
                'nombre': 'Servicios Profesionales',
                'descripcion': 'Médicos, abogados, consultores',
                'color_codigo': '#007bff',
                'tarifa_base': Decimal('3.00')
            },
            {
                'nombre': 'Automotriz',
                'descripcion': 'Concesionarios y servicios automotrices',
                'color_codigo': '#fd7e14',
                'tarifa_base': Decimal('4.00')
            },
            {
                'nombre': 'Inmobiliaria',
                'descripcion': 'Venta y renta de propiedades',
                'color_codigo': '#6f42c1',
                'tarifa_base': Decimal('3.50')
            },
            {
                'nombre': 'Restaurantes',
                'descripcion': 'Restaurantes y servicios de comida',
                'color_codigo': '#dc3545',
                'tarifa_base': Decimal('2.00')
            },
            {
                'nombre': 'Educación',
                'descripcion': 'Instituciones educativas y cursos',
                'color_codigo': '#20c997',
                'tarifa_base': Decimal('2.25')
            },
            {
                'nombre': 'Salud y Bienestar',
                'descripcion': 'Clínicas, gimnasios, spas',
                'color_codigo': '#17a2b8',
                'tarifa_base': Decimal('2.75')
            },
            {
                'nombre': 'Tecnología',
                'descripcion': 'Empresas de tecnología y servicios IT',
                'color_codigo': '#6610f2',
                'tarifa_base': Decimal('4.50')
            },
            {
                'nombre': 'Entretenimiento',
                'descripcion': 'Eventos, espectáculos y entretenimiento',
                'color_codigo': '#e83e8c',
                'tarifa_base': Decimal('3.25')
            },
            {
                'nombre': 'Servicios Financieros',
                'descripcion': 'Bancos, seguros, inversiones',
                'color_codigo': '#6c757d',
                'tarifa_base': Decimal('5.00')
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for cat_data in categories:
            categoria, created = CategoriaPublicitaria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults=cat_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Categoría "{cat_data["nombre"]}" creada')
            elif force:
                # Actualizar datos existentes
                for key, value in cat_data.items():
                    setattr(categoria, key, value)
                categoria.save()
                updated_count += 1
                self.stdout.write(f'  ✓ Categoría "{cat_data["nombre"]}" actualizada')
            else:
                self.stdout.write(f'  - Categoría "{cat_data["nombre"]}" ya existe')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Categorías: {created_count} creadas, {updated_count} actualizadas'
            )
        )
    
    def setup_contract_types(self, force=False):
        """Configura tipos de contrato base"""
        self.stdout.write('Configurando tipos de contrato...')
        
        contract_types = [
            {
                'nombre': 'Paquete Básico Semanal',
                'descripcion': 'Paquete básico de 1 semana',
                'duracion_tipo': 'semanal',
                'duracion_dias': 7,
                'repeticiones_minimas': 3,
                'descuento_porcentaje': Decimal('0.00')
            },
            {
                'nombre': 'Paquete Estándar Mensual',
                'descripcion': 'Paquete estándar de 1 mes',
                'duracion_tipo': 'mensual',
                'duracion_dias': 30,
                'repeticiones_minimas': 2,
                'descuento_porcentaje': Decimal('10.00')
            },
            {
                'nombre': 'Paquete Premium Trimestral',
                'descripcion': 'Paquete premium de 3 meses',
                'duracion_tipo': 'trimestral',
                'duracion_dias': 90,
                'repeticiones_minimas': 4,
                'descuento_porcentaje': Decimal('20.00')
            },
            {
                'nombre': 'Paquete Corporativo Semestral',
                'descripcion': 'Paquete corporativo de 6 meses',
                'duracion_tipo': 'semestral',
                'duracion_dias': 180,
                'repeticiones_minimas': 5,
                'descuento_porcentaje': Decimal('25.00')
            },
            {
                'nombre': 'Paquete Empresarial Anual',
                'descripcion': 'Paquete empresarial de 1 año',
                'duracion_tipo': 'anual',
                'duracion_dias': 365,
                'repeticiones_minimas': 6,
                'descuento_porcentaje': Decimal('30.00')
            },
            {
                'nombre': 'Campaña Express',
                'descripcion': 'Campaña corta de alto impacto',
                'duracion_tipo': 'semanal',
                'duracion_dias': 3,
                'repeticiones_minimas': 8,
                'descuento_porcentaje': Decimal('0.00')
            },
            {
                'nombre': 'Paquete Fin de Semana',
                'descripcion': 'Especial para fines de semana',
                'duracion_tipo': 'semanal',
                'duracion_dias': 7,
                'repeticiones_minimas': 6,
                'descuento_porcentaje': Decimal('5.00')
            },
            {
                'nombre': 'Campaña Personalizada',
                'descripcion': 'Campaña con duración personalizada',
                'duracion_tipo': 'personalizado',
                'duracion_dias': 30,
                'repeticiones_minimas': 1,
                'descuento_porcentaje': Decimal('0.00')
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for contract_data in contract_types:
            contrato, created = TipoContrato.objects.get_or_create(
                nombre=contract_data['nombre'],
                defaults=contract_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Tipo de contrato "{contract_data["nombre"]}" creado')
            elif force:
                # Actualizar datos existentes
                for key, value in contract_data.items():
                    setattr(contrato, key, value)
                contrato.save()
                updated_count += 1
                self.stdout.write(f'  ✓ Tipo de contrato "{contract_data["nombre"]}" actualizado')
            else:
                self.stdout.write(f'  - Tipo de contrato "{contract_data["nombre"]}" ya existe')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Tipos de contrato: {created_count} creados, {updated_count} actualizados'
            )
        )
    
    def create_demo_user(self):
        """Crea usuario de demostración (solo para desarrollo)"""
        self.stdout.write('Creando usuario de demostración...')
        
        if not User.objects.filter(username='demo_admin').exists():
            admin_user = User.objects.create_user(
                username='demo_admin',
                email='admin@publitrack.demo',
                password='demo123',
                first_name='Admin',
                last_name='Demo',
                is_staff=True,
                is_superuser=True
            )
            
            # Agregar a grupo administradores
            admin_group = Group.objects.get(name='Administradores')
            admin_user.groups.add(admin_group)
            
            self.stdout.write('  ✓ Usuario demo_admin creado (password: demo123)')
        else:
            self.stdout.write('  - Usuario demo_admin ya existe')
        
        # Crear otros usuarios de demo
        demo_users = [
            {
                'username': 'demo_vendedor',
                'email': 'vendedor@publitrack.demo',
                'first_name': 'Vendedor',
                'last_name': 'Demo',
                'group': 'Vendedores'
            },
            {
                'username': 'demo_cliente',
                'email': 'cliente@publitrack.demo',
                'first_name': 'Cliente',
                'last_name': 'Demo',
                'group': 'Clientes'
            }
        ]
        
        for user_data in demo_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password='demo123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                group = Group.objects.get(name=user_data['group'])
                user.groups.add(group)
                
                self.stdout.write(f'  ✓ Usuario {user_data["username"]} creado')
            else:
                self.stdout.write(f'  - Usuario {user_data["username"]} ya existe')