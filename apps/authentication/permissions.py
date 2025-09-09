"""
Funciones auxiliares para el sistema de permisos de PubliTrack
"""

from django.contrib.auth import get_user_model
from .models import Permission, Role, RolePermission

User = get_user_model()

class PermissionManager:
    """
    Clase utilitaria para gestionar permisos del sistema
    """
    
    # Definición de permisos por defecto del sistema
    DEFAULT_PERMISSIONS = {
        'authentication': [
            ('view_users', 'Ver usuarios', 'view'),
            ('add_users', 'Agregar usuarios', 'add'),
            ('change_users', 'Modificar usuarios', 'change'),
            ('delete_users', 'Eliminar usuarios', 'delete'),
            ('assign_roles', 'Asignar roles', 'assign'),
            ('view_user_reports', 'Ver reportes de usuarios', 'view'),
            ('export_user_data', 'Exportar datos de usuarios', 'export'),
        ],
        'content_management': [
            ('view_content', 'Ver contenido publicitario', 'view'),
            ('add_content', 'Agregar contenido publicitario', 'add'),
            ('change_content', 'Modificar contenido publicitario', 'change'),
            ('delete_content', 'Eliminar contenido publicitario', 'delete'),
            ('approve_content', 'Aprobar contenido publicitario', 'approve'),
            ('upload_audio', 'Subir archivos de audio', 'add'),
            ('view_content_reports', 'Ver reportes de contenido', 'view'),
        ],
        'financial_management': [
            ('view_finances', 'Ver información financiera', 'view'),
            ('add_transactions', 'Agregar transacciones', 'add'),
            ('change_transactions', 'Modificar transacciones', 'change'),
            ('delete_transactions', 'Eliminar transacciones', 'delete'),
            ('approve_payments', 'Aprobar pagos', 'approve'),
            ('view_financial_reports', 'Ver reportes financieros', 'view'),
            ('export_financial_data', 'Exportar datos financieros', 'export'),
            ('manage_invoicing', 'Gestionar facturación', 'configure'),
        ],
        'traffic_light_system': [
            ('view_status', 'Ver estados del semáforo', 'view'),
            ('change_status', 'Cambiar estados del semáforo', 'change'),
            ('configure_traffic_rules', 'Configurar reglas del semáforo', 'configure'),
            ('view_status_reports', 'Ver reportes de estados', 'view'),
        ],
        'transmission_control': [
            ('view_transmissions', 'Ver transmisiones', 'view'),
            ('add_transmissions', 'Programar transmisiones', 'add'),
            ('change_transmissions', 'Modificar transmisiones', 'change'),
            ('delete_transmissions', 'Eliminar transmisiones', 'delete'),
            ('control_broadcast', 'Controlar emisión', 'configure'),
            ('view_transmission_reports', 'Ver reportes de transmisión', 'view'),
        ],
        'notifications': [
            ('view_notifications', 'Ver notificaciones', 'view'),
            ('send_notifications', 'Enviar notificaciones', 'add'),
            ('configure_notifications', 'Configurar notificaciones', 'configure'),
            ('view_notification_reports', 'Ver reportes de notificaciones', 'view'),
        ],
        'sales_management': [
            ('view_sales', 'Ver ventas', 'view'),
            ('add_sales', 'Registrar ventas', 'add'),
            ('change_sales', 'Modificar ventas', 'change'),
            ('delete_sales', 'Eliminar ventas', 'delete'),
            ('manage_commissions', 'Gestionar comisiones', 'configure'),
            ('view_sales_reports', 'Ver reportes de ventas', 'view'),
            ('export_sales_data', 'Exportar datos de ventas', 'export'),
        ],
        'reports_analytics': [
            ('view_all_reports', 'Ver todos los reportes', 'view'),
            ('create_custom_reports', 'Crear reportes personalizados', 'add'),
            ('export_reports', 'Exportar reportes', 'export'),
            ('configure_analytics', 'Configurar analíticas', 'configure'),
        ],
        'system_configuration': [
            ('view_system_config', 'Ver configuración del sistema', 'view'),
            ('change_system_config', 'Modificar configuración del sistema', 'configure'),
            ('manage_company_settings', 'Gestionar configuraciones de empresa', 'configure'),
            ('backup_system', 'Realizar respaldos del sistema', 'configure'),
            ('view_system_logs', 'Ver logs del sistema', 'view'),
        ],
    }
    
    # Definición de roles por defecto
    DEFAULT_ROLES = {
        'admin': {
            'name': 'Administrador',
            'description': 'Acceso completo al sistema. Puede gestionar usuarios, configuraciones y todos los módulos.',
            'permissions': 'all'  # Todos los permisos
        },
        'vendedor': {
            'name': 'Vendedor',
            'description': 'Puede gestionar contenido publicitario, ventas, clientes asignados y ver reportes relacionados.',
            'permissions': [
                # Autenticación (limitado)
                'view_users',
                
                # Gestión de contenido
                'view_content', 'add_content', 'change_content', 'upload_audio', 'view_content_reports',
                
                # Gestión financiera (limitado)
                'view_finances', 'add_transactions', 'view_financial_reports',
                
                # Sistema de semáforos
                'view_status', 'change_status', 'view_status_reports',
                
                # Control de transmisiones
                'view_transmissions', 'add_transmissions', 'change_transmissions', 'view_transmission_reports',
                
                # Notificaciones
                'view_notifications', 'send_notifications',
                
                # Gestión de ventas
                'view_sales', 'add_sales', 'change_sales', 'manage_commissions', 'view_sales_reports', 'export_sales_data',
                
                # Reportes
                'view_all_reports', 'export_reports',
            ]
        },
        'cliente': {
            'name': 'Cliente',
            'description': 'Puede ver su contenido publicitario, estados de transmisión y reportes personales.',
            'permissions': [
                # Solo pueden ver su propio contenido y estados
                'view_content', 'view_status', 'view_transmissions', 'view_notifications', 'view_sales',
            ]
        }
    }
    
    @classmethod
    def create_default_permissions(cls):
        """
        Crea los permisos por defecto del sistema
        """
        created_count = 0
        
        for module, permissions in cls.DEFAULT_PERMISSIONS.items():
            for codename, name, action in permissions:
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    defaults={
                        'name': name,
                        'module': module,
                        'action': action,
                        'description': f'{name} en el módulo {module}'
                    }
                )
                if created:
                    created_count += 1
                    print(f"✅ Permiso creado: {permission}")
        
        print(f"📋 Total de permisos creados: {created_count}")
        return created_count
    
    @classmethod
    def create_default_roles(cls):
        """
        Crea los roles por defecto del sistema
        """
        created_count = 0
        
        for codename, role_data in cls.DEFAULT_ROLES.items():
            role, created = Role.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'is_system_role': True
                }
            )
            
            if created:
                created_count += 1
                print(f"✅ Rol creado: {role}")
                
                # Asignar permisos al rol
                cls.assign_permissions_to_role(role, role_data['permissions'])
        
        print(f"👥 Total de roles creados: {created_count}")
        return created_count
    
    @classmethod
    def assign_permissions_to_role(cls, role, permissions):
        """
        Asigna permisos a un rol
        """
        if permissions == 'all':
            # Asignar todos los permisos
            all_permissions = Permission.objects.filter(is_active=True)
            for permission in all_permissions:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission
                )
            print(f"  📋 Asignados TODOS los permisos a {role.name}")
        else:
            # Asignar permisos específicos
            assigned_count = 0
            for permission_codename in permissions:
                try:
                    permission = Permission.objects.get(codename=permission_codename, is_active=True)
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission
                    )
                    assigned_count += 1
                except Permission.DoesNotExist:
                    print(f"  ⚠️  Permiso no encontrado: {permission_codename}")
            
            print(f"  📋 Asignados {assigned_count} permisos a {role.name}")
    
    @classmethod
    def initialize_system(cls):
        """
        Inicializa todo el sistema de permisos
        """
        print("🚀 Inicializando sistema de permisos...")
        
        # Crear permisos
        permissions_created = cls.create_default_permissions()
        
        # Crear roles
        roles_created = cls.create_default_roles()
        
        print(f"✅ Sistema inicializado: {permissions_created} permisos, {roles_created} roles")
        return permissions_created, roles_created

def check_user_permission(user, permission_codename):
    """
    Función auxiliar para verificar permisos de usuario
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.has_permission(permission_codename)

def get_user_permissions_for_module(user, module_name):
    """
    Obtiene todos los permisos de un usuario para un módulo específico
    """
    if not user or not user.is_authenticated:
        return []
    
    permissions = user.get_user_permissions().filter(module=module_name)
    return [perm.codename for perm in permissions]

def get_available_modules_for_user(user):
    """
    Obtiene todos los módulos a los que tiene acceso el usuario
    """
    if not user or not user.is_authenticated:
        return []
    
    permissions = user.get_user_permissions()
    modules = set(perm.module for perm in permissions)
    return list(modules)

def user_can_access_object(user, obj, action='view'):
    """
    Verifica si un usuario puede acceder a un objeto específico
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superusuarios pueden todo
    if user.is_superuser:
        return True
    
    # Verificar si es el propietario del objeto
    if hasattr(obj, 'created_by') and obj.created_by == user:
        return True
    
    if hasattr(obj, 'vendedor_asignado') and obj.vendedor_asignado == user:
        return True
    
    # Verificar permisos por tipo de objeto
    app_label = obj._meta.app_label
    model_name = obj._meta.model_name
    permission_codename = f'{action}_{model_name}'
    
    return user.has_permission(permission_codename)

def get_filtered_queryset_for_user(user, queryset):
    """
    Filtra un queryset basado en los permisos del usuario
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    if user.is_superuser or user.es_admin:
        return queryset
    
    # Filtrar según el rol
    if user.es_vendedor:
        # Los vendedores solo ven sus propios objetos o los de sus clientes
        if hasattr(queryset.model, 'vendedor_asignado'):
            return queryset.filter(vendedor_asignado=user)
        elif hasattr(queryset.model, 'created_by'):
            return queryset.filter(created_by=user)
    
    elif user.es_cliente:
        # Los clientes solo ven sus propios objetos
        if hasattr(queryset.model, 'cliente'):
            return queryset.filter(cliente=user)
        elif hasattr(queryset.model, 'created_by'):
            return queryset.filter(created_by=user)
    
    return queryset.none()

# Context processor para templates
def permissions_context(request):
    """
    Context processor que agrega información de permisos a todos los templates
    """
    if not request.user.is_authenticated:
        return {}
    
    return {
        'user_permissions': request.user.get_user_permissions(),
        'user_modules': get_available_modules_for_user(request.user),
        'permissions_by_module': request.user.get_permissions_by_module(),
    }