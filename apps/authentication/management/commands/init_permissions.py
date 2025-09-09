"""
Comando de gestión para inicializar el sistema de permisos
Ubicación: apps/authentication/management/commands/init_permissions.py
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.authentication.permissions import PermissionManager
from apps.authentication.models import Permission, Role, CustomUser

class Command(BaseCommand):
    help = 'Inicializa el sistema de permisos y roles de PubliTrack'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar recreación de permisos y roles existentes',
        )
        
        parser.add_argument(
            '--only-permissions',
            action='store_true',
            help='Solo crear permisos, no roles',
        )
        
        parser.add_argument(
            '--only-roles',
            action='store_true',
            help='Solo crear roles, no permisos',
        )
        
        parser.add_argument(
            '--update-users',
            action='store_true',
            help='Actualizar roles de usuarios existentes',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Inicializando sistema de permisos de PubliTrack...')
        )
        
        force = options['force']
        only_permissions = options['only_permissions']
        only_roles = options['only_roles']
        update_users = options['update_users']
        
        try:
            with transaction.atomic():
                # Limpiar datos existentes si se fuerza
                if force:
                    self.stdout.write('⚠️  Modo FORCE activado - Limpiando datos existentes...')
                    self._clear_existing_data()
                
                # Crear permisos
                if not only_roles:
                    permissions_created = self._create_permissions()
                    
                # Crear roles
                if not only_permissions:
                    roles_created = self._create_roles()
                
                # Actualizar usuarios existentes
                if update_users:
                    self._update_existing_users()
                
                # Verificar integridad
                self._verify_system_integrity()
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Sistema de permisos inicializado correctamente!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la inicialización: {str(e)}')
            )
            raise
    
    def _clear_existing_data(self):
        """Limpia datos existentes del sistema de permisos"""
        self.stdout.write('  📋 Eliminando permisos existentes...')
        Permission.objects.all().delete()
        
        self.stdout.write('  👥 Eliminando roles existentes...')
        Role.objects.all().delete()
        
        self.stdout.write('  ✅ Datos anteriores eliminados')
    
    def _create_permissions(self):
        """Crea los permisos del sistema"""
        self.stdout.write('📋 Creando permisos del sistema...')
        
        permissions_created = PermissionManager.create_default_permissions()
        
        self.stdout.write(
            self.style.SUCCESS(f'  ✅ {permissions_created} permisos creados')
        )
        
        return permissions_created
    
    def _create_roles(self):
        """Crea los roles del sistema"""
        self.stdout.write('👥 Creando roles del sistema...')
        
        roles_created = PermissionManager.create_default_roles()
        
        self.stdout.write(
            self.style.SUCCESS(f'  ✅ {roles_created} roles creados')
        )
        
        return roles_created
    
    def _update_existing_users(self):
        """Actualiza los roles de usuarios existentes"""
        self.stdout.write('👤 Actualizando usuarios existentes...')
        
        updated_count = 0
        
        # Verificar que existan los roles
        admin_role = Role.objects.filter(codename='admin').first()
        vendedor_role = Role.objects.filter(codename='vendedor').first()
        cliente_role = Role.objects.filter(codename='cliente').first()
        
        if not all([admin_role, vendedor_role, cliente_role]):
            self.stdout.write(
                self.style.ERROR('  ❌ No se encontraron todos los roles necesarios')
            )
            return
        
        for user in CustomUser.objects.all():
            old_rol = user.rol
            # Los roles ya están correctos en el modelo CustomUser
            # Aquí podrías agregar lógica adicional si necesitas sincronizar algo
            
            self.stdout.write(f'  📝 Usuario {user.username}: {old_rol}')
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'  ✅ {updated_count} usuarios verificados')
        )
    
    def _verify_system_integrity(self):
        """Verifica la integridad del sistema de permisos"""
        self.stdout.write('🔍 Verificando integridad del sistema...')
        
        # Verificar permisos
        total_permissions = Permission.objects.count()
        active_permissions = Permission.objects.filter(is_active=True).count()
        
        self.stdout.write(f'  📋 Permisos: {active_permissions}/{total_permissions} activos')
        
        # Verificar roles
        total_roles = Role.objects.count()
        active_roles = Role.objects.filter(is_active=True).count()
        
        self.stdout.write(f'  👥 Roles: {active_roles}/{total_roles} activos')
        
        # Verificar asignaciones
        for role in Role.objects.filter(is_active=True):
            perm_count = role.permissions.filter(is_active=True).count()
            self.stdout.write(f'    🔹 {role.name}: {perm_count} permisos')
        
        # Verificar usuarios por rol
        for rol_code, rol_name in CustomUser.ROLE_CHOICES:
            user_count = CustomUser.objects.filter(rol=rol_code, status='activo').count()
            self.stdout.write(f'  👤 {rol_name}: {user_count} usuarios activos')
        
        self.stdout.write('  ✅ Verificación completada')
    
    def _display_summary(self):
        """Muestra un resumen del sistema"""
        self.stdout.write('\n📊 RESUMEN DEL SISTEMA DE PERMISOS')
        self.stdout.write('=' * 50)
        
        # Módulos y permisos
        modules = Permission.objects.values_list('module', flat=True).distinct()
        for module in modules:
            perm_count = Permission.objects.filter(module=module, is_active=True).count()
            self.stdout.write(f'📁 {module}: {perm_count} permisos')
        
        # Roles y usuarios
        self.stdout.write('\n👥 ROLES Y USUARIOS:')
        for role in Role.objects.filter(is_active=True):
            user_count = CustomUser.objects.filter(rol=role.codename, status='activo').count()
            perm_count = role.permissions.filter(is_active=True).count()
            self.stdout.write(f'  🔹 {role.name}: {user_count} usuarios, {perm_count} permisos')
        
        self.stdout.write('\n✅ Sistema listo para usar!')
        self.stdout.write('\n💡 Comandos útiles:')
        self.stdout.write('  • python manage.py shell')
        self.stdout.write('  • from apps.authentication.models import CustomUser')
        self.stdout.write('  • user = CustomUser.objects.get(username="admin")')
        self.stdout.write('  • user.has_permission("view_users")')
        self.stdout.write('')