"""
Tests para el Sistema de Semáforos
Sistema PubliTrack - Pruebas unitarias e integración
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta, date
from unittest.mock import patch, MagicMock

from apps.content_management.models import CuñaPublicitaria, CategoriaPublicitaria, TipoContrato
from .models import (
    ConfiguracionSemaforo, EstadoSemaforo, HistorialEstadoSemaforo,
    AlertaSemaforo, ResumenEstadosSemaforo
)
from .utils.status_calculator import StatusCalculator, AlertasManager

User = get_user_model()


class ConfiguracionSemaforoTestCase(TestCase):
    """Tests para el modelo ConfiguracionSemaforo"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            rol='admin'
        )
    
    def test_crear_configuracion_basica(self):
        """Test crear configuración básica"""
        config = ConfiguracionSemaforo.objects.create(
            nombre="Test Config",
            descripcion="Configuración de prueba",
            tipo_calculo='combinado',
            created_by=self.admin_user
        )
        
        self.assertEqual(config.nombre, "Test Config")
        self.assertEqual(config.tipo_calculo, 'combinado')
        self.assertTrue(config.is_active)  # Primera configuración debe ser activa
        self.assertTrue(config.is_default)
    
    def test_solo_una_configuracion_activa(self):
        """Test que solo una configuración puede estar activa"""
        config1 = ConfiguracionSemaforo.objects.create(
            nombre="Config 1",
            is_active=True,
            created_by=self.admin_user
        )
        
        config2 = ConfiguracionSemaforo.objects.create(
            nombre="Config 2",
            is_active=True,  # Esto debe desactivar config1
            created_by=self.admin_user
        )
        
        config1.refresh_from_db()
        self.assertFalse(config1.is_active)
        self.assertTrue(config2.is_active)
    
    def test_validacion_umbrales(self):
        """Test validación de umbrales en ConfiguracionSemaforoForm"""
        from .forms import ConfiguracionSemaforoForm
        
        # Datos inválidos: días amarillo >= días verde
        form_data = {
            'nombre': 'Test Config',
            'tipo_calculo': 'combinado',
            'dias_verde_min': 10,
            'dias_amarillo_min': 15,  # Mayor que verde
            'porcentaje_verde_max': 50,
            'porcentaje_amarillo_max': 85,
        }
        
        form = ConfiguracionSemaforoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('días mínimos para amarillo deben ser menores', str(form.errors))
    
    def test_get_active_crea_default(self):
        """Test que get_active() crea configuración por defecto si no existe"""
        # Asegurar que no hay configuraciones
        ConfiguracionSemaforo.objects.all().delete()
        
        config = ConfiguracionSemaforo.get_active()
        
        self.assertIsNotNone(config)
        self.assertTrue(config.is_active)
        self.assertTrue(config.is_default)
        self.assertEqual(config.nombre, "Configuración por Defecto")


class StatusCalculatorTestCase(TestCase):
    """Tests para StatusCalculator"""
    
    def setUp(self):
        # Crear usuarios de prueba
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            rol='admin'
        )
        
        self.cliente_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='testpass123',
            rol='cliente',
            empresa='Empresa Test'
        )
        
        self.vendedor_user = User.objects.create_user(
            username='vendedor_test',
            email='vendedor@test.com',
            password='testpass123',
            rol='vendedor'
        )
        
        # Crear categoría y tipo de contrato
        self.categoria = CategoriaPublicitaria.objects.create(
            nombre='Categoría Test',
            tarifa_base=Decimal('10.00')
        )
        
        self.tipo_contrato = TipoContrato.objects.create(
            nombre='Mensual Test',
            duracion_dias=30
        )
        
        # Crear configuración de semáforo
        self.configuracion = ConfiguracionSemaforo.objects.create(
            nombre="Config Test",
            tipo_calculo='combinado',
            dias_verde_min=15,
            dias_amarillo_min=7,
            porcentaje_verde_max=Decimal('50.00'),
            porcentaje_amarillo_max=Decimal('85.00'),
            created_by=self.admin_user
        )
        
        # Crear calculator
        self.calculator = StatusCalculator(self.configuracion)
        
        # Fechas de prueba
        self.hoy = timezone.now().date()
        self.fecha_inicio = self.hoy - timedelta(days=10)
        self.fecha_fin = self.hoy + timedelta(days=20)
    
    def crear_cuña_test(self, **kwargs):
        """Helper para crear cuñas de prueba"""
        defaults = {
            'codigo': 'TEST001',
            'titulo': 'Cuña de Prueba',
            'cliente': self.cliente_user,
            'vendedor_asignado': self.vendedor_user,
            'categoria': self.categoria,
            'tipo_contrato': self.tipo_contrato,
            'estado': 'activa',
            'duracion_planeada': 30,
            'precio_total': Decimal('300.00'),
            'repeticiones_dia': 3,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'created_by': self.admin_user
        }
        defaults.update(kwargs)
        return CuñaPublicitaria.objects.create(**defaults)
    
    def test_calculo_dias_restantes(self):
        """Test cálculo de días restantes"""
        cuña = self.crear_cuña_test()
        
        dias = self.calculator._calcular_dias_restantes(cuña)
        esperado = (self.fecha_fin - self.hoy).days
        
        self.assertEqual(dias, esperado)
    
    def test_calculo_porcentaje_tiempo(self):
        """Test cálculo de porcentaje de tiempo transcurrido"""
        cuña = self.crear_cuña_test()
        
        porcentaje = self.calculator._calcular_porcentaje_tiempo_transcurrido(cuña)
        
        # Calcular porcentaje esperado
        duracion_total = (self.fecha_fin - self.fecha_inicio).days
        dias_transcurridos = (self.hoy - self.fecha_inicio).days
        esperado = Decimal(str(round((dias_transcurridos / duracion_total) * 100, 2)))
        
        self.assertEqual(porcentaje, esperado)
    
    def test_calculo_por_estado_verde(self):
        """Test cálculo por estado - caso verde"""
        cuña = self.crear_cuña_test(estado='activa')
        
        color, razon = self.calculator._calcular_por_estado(cuña)
        
        self.assertEqual(color, 'verde')
        self.assertIn('activa', razon)
    
    def test_calculo_por_estado_rojo(self):
        """Test cálculo por estado - caso rojo"""
        cuña = self.crear_cuña_test(estado='borrador')
        
        color, razon = self.calculator._calcular_por_estado(cuña)
        
        self.assertEqual(color, 'rojo')
        self.assertIn('borrador', razon)
    
    def test_calculo_por_dias_vencida(self):
        """Test cálculo por días - cuña vencida"""
        fecha_fin_vencida = self.hoy - timedelta(days=5)
        cuña = self.crear_cuña_test(fecha_fin=fecha_fin_vencida)
        
        dias_restantes = (fecha_fin_vencida - self.hoy).days  # Negativo
        color, razon = self.calculator._calcular_por_dias_restantes(cuña, dias_restantes)
        
        self.assertEqual(color, 'rojo')
        self.assertIn('vencida', razon.lower())
    
    def test_calculo_por_dias_verde(self):
        """Test cálculo por días - caso verde"""
        fecha_fin_lejana = self.hoy + timedelta(days=30)
        cuña = self.crear_cuña_test(fecha_fin=fecha_fin_lejana)
        
        dias_restantes = (fecha_fin_lejana - self.hoy).days
        color, razon = self.calculator._calcular_por_dias_restantes(cuña, dias_restantes)
        
        self.assertEqual(color, 'verde')
    
    def test_calculo_por_porcentaje_rojo(self):
        """Test cálculo por porcentaje - caso rojo (>85%)"""
        porcentaje = Decimal('95.00')
        cuña = self.crear_cuña_test()
        
        color, razon = self.calculator._calcular_por_porcentaje_tiempo(cuña, porcentaje)
        
        self.assertEqual(color, 'rojo')
        self.assertIn('95', razon)
    
    def test_calculo_combinado_toma_peor_estado(self):
        """Test que el cálculo combinado toma el peor estado"""
        # Cuña que por estado sería verde, pero por tiempo rojo
        fecha_inicio_temprana = self.hoy - timedelta(days=25)
        fecha_fin_proxima = self.hoy + timedelta(days=5)
        
        cuña = self.crear_cuña_test(
            estado='activa',  # Verde por estado
            fecha_inicio=fecha_inicio_temprana,
            fecha_fin=fecha_fin_proxima  # Rojo por días restantes
        )
        
        resultado = self.calculator.calcular_estado_cuña(cuña)
        
        # Debe ser rojo porque es el peor estado
        self.assertEqual(resultado['color'], 'rojo')
    
    def test_actualizar_estado_cuña_nueva(self):
        """Test actualizar estado para cuña nueva"""
        cuña = self.crear_cuña_test()
        
        estado = self.calculator.actualizar_estado_cuña(cuña)
        
        self.assertIsNotNone(estado)
        self.assertEqual(estado.cuña, cuña)
        self.assertIsNotNone(estado.color_actual)
        self.assertIsNotNone(estado.prioridad)
    
    def test_actualizar_estado_crea_historial(self):
        """Test que actualizar estado crea entrada en historial"""
        cuña = self.crear_cuña_test()
        
        self.calculator.actualizar_estado_cuña(cuña, crear_historial=True)
        
        historial = HistorialEstadoSemaforo.objects.filter(cuña=cuña)
        self.assertTrue(historial.exists())
    
    def test_determinar_prioridad_critica(self):
        """Test determinación de prioridad crítica"""
        cuña = self.crear_cuña_test()
        
        # Caso: rojo con días negativos (vencida)
        prioridad = self.calculator._determinar_prioridad(
            color='rojo', 
            cuña=cuña, 
            dias_restantes=-2, 
            porcentaje_tiempo=Decimal('105.00')
        )
        
        self.assertEqual(prioridad, 'critica')
    
    def test_requiere_alerta_rojo(self):
        """Test que estado rojo requiere alerta"""
        cuña = self.crear_cuña_test()
        
        requiere = self.calculator._requiere_alerta(
            color='rojo',
            cuña=cuña,
            dias_restantes=5
        )
        
        self.assertTrue(requiere)
    
    def test_estadisticas_resumen(self):
        """Test obtención de estadísticas resumen"""
        # Crear algunas cuñas con diferentes estados
        cuña1 = self.crear_cuña_test(codigo='TEST001')
        cuña2 = self.crear_cuña_test(codigo='TEST002', estado='borrador')
        
        # Actualizar sus estados
        self.calculator.actualizar_estado_cuña(cuña1)
        self.calculator.actualizar_estado_cuña(cuña2)
        
        stats = self.calculator.obtener_estadisticas_resumen()
        
        self.assertIn('total_cuñas', stats)
        self.assertIn('contadores', stats)
        self.assertIn('porcentajes', stats)
        self.assertEqual(stats['total_cuñas'], 2)


class AlertasManagerTestCase(TestCase):
    """Tests para AlertasManager"""
    
    def setUp(self):
        # Crear datos de prueba similares a StatusCalculatorTestCase
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            rol='admin'
        )
        
        self.cliente_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='testpass123',
            rol='cliente'
        )
        
        self.categoria = CategoriaPublicitaria.objects.create(
            nombre='Categoría Test'
        )
        
        self.configuracion = ConfiguracionSemaforo.objects.create(
            nombre="Config Test",
            enviar_alertas=True,
            created_by=self.admin_user
        )
        
        self.manager = AlertasManager()
        
        # Crear cuña y estado que requiere alerta
        self.cuña = CuñaPublicitaria.objects.create(
            codigo='TEST001',
            titulo='Cuña Test',
            cliente=self.cliente_user,
            categoria=self.categoria,
            estado='activa',
            duracion_planeada=30,
            precio_total=Decimal('300.00'),
            repeticiones_dia=3,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=5),
            created_by=self.admin_user
        )
        
        self.estado = EstadoSemaforo.objects.create(
            cuña=self.cuña,
            color_actual='rojo',
            prioridad='alta',
            requiere_alerta=True,
            alerta_enviada=False,
            configuracion_utilizada=self.configuracion
        )
    
    def test_crear_alerta_para_estado(self):
        """Test crear alerta para estado específico"""
        alerta = self.manager._crear_alerta_para_estado(self.estado)
        
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta.cuña, self.cuña)
        self.assertEqual(alerta.estado_semaforo, self.estado)
        self.assertTrue(alerta.enviar_email)
    
    def test_generar_alertas_pendientes(self):
        """Test generar alertas pendientes"""
        stats = self.manager.generar_alertas_pendientes()
        
        self.assertIn('alertas_creadas', stats)
        self.assertIn('errores', stats)
        self.assertEqual(stats['alertas_creadas'], 1)
    
    def test_no_duplicar_alertas_recientes(self):
        """Test que no se duplican alertas recientes"""
        # Crear primera alerta
        self.manager._crear_alerta_para_estado(self.estado)
        
        # Intentar crear segunda alerta
        stats = self.manager.generar_alertas_pendientes()
        
        # No debe crear nueva alerta porque ya existe una reciente
        self.assertEqual(stats['alertas_creadas'], 0)
    
    def test_obtener_usuarios_destino(self):
        """Test obtención de usuarios destino"""
        usuarios = self.manager._obtener_usuarios_destino(self.cuña)
        
        # Debe incluir al admin
        self.assertIn(self.admin_user, usuarios)
    
    def test_construir_mensaje_alerta(self):
        """Test construcción de mensaje de alerta"""
        mensaje = self.manager._construir_mensaje_alerta(self.estado)
        
        self.assertIn(self.cuña.titulo, mensaje)
        self.assertIn(self.cliente_user.get_full_name(), mensaje)
        self.assertIn('Estado: Rojo', mensaje)


class ViewsTestCase(TestCase):
    """Tests para las vistas del sistema"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            rol='admin'
        )
        
        self.vendedor_user = User.objects.create_user(
            username='vendedor_test',
            email='vendedor@test.com',
            password='testpass123',
            rol='vendedor'
        )
        
        self.cliente_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='testpass123',
            rol='cliente'
        )
    
    def test_dashboard_acceso_admin(self):
        """Test que admin puede acceder al dashboard"""
        self.client.login(username='admin_test', password='testpass123')
        
        with patch.object(User, 'can_view_traffic_light_system', return_value=True):
            response = self.client.get(reverse('traffic_light:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_acceso_denegado_cliente(self):
        """Test que cliente no puede acceder al dashboard"""
        self.client.login(username='cliente_test', password='testpass123')
        
        with patch.object(User, 'can_view_traffic_light_system', return_value=False):
            response = self.client.get(reverse('traffic_light:dashboard'))
        
        # Debe denegar acceso o redirigir
        self.assertIn(response.status_code, [302, 403])
    
    def test_api_recalcular_cuña_permiso_admin(self):
        """Test API de recálculo con permisos de admin"""
        self.client.login(username='admin_test', password='testpass123')
        
        # Crear cuña de prueba
        categoria = CategoriaPublicitaria.objects.create(nombre='Test')
        cuña = CuñaPublicitaria.objects.create(
            codigo='TEST001',
            titulo='Test',
            cliente=self.cliente_user,
            categoria=categoria,
            estado='activa',
            duracion_planeada=30,
            precio_total=Decimal('300.00'),
            repeticiones_dia=3,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=30),
            created_by=self.admin_user
        )
        
        with patch.object(User, 'can_manage_content', return_value=True):
            response = self.client.post(
                reverse('traffic_light:api_recalcular_cuña', args=[cuña.id])
            )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_api_estadisticas_dashboard(self):
        """Test API de estadísticas del dashboard"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(reverse('traffic_light:api_estadisticas'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('estadisticas', data)


class ModelsIntegrationTestCase(TransactionTestCase):
    """Tests de integración entre modelos"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            rol='admin'
        )
        
        self.cliente_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='testpass123',
            rol='cliente'
        )
        
        self.categoria = CategoriaPublicitaria.objects.create(
            nombre='Categoría Test'
        )
    
    def test_señal_actualiza_estado_al_crear_cuña(self):
        """Test que las señales actualizan estado al crear cuña"""
        cuña = CuñaPublicitaria.objects.create(
            codigo='TEST001',
            titulo='Test',
            cliente=self.cliente_user,
            categoria=self.categoria,
            estado='activa',
            duracion_planeada=30,
            precio_total=Decimal('300.00'),
            repeticiones_dia=3,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=30),
            created_by=self.admin_user
        )
        
        # Verificar que se creó estado de semáforo
        self.assertTrue(
            EstadoSemaforo.objects.filter(cuña=cuña).exists()
        )
    
    def test_señal_crea_historial_al_cambiar_estado(self):
        """Test que se crea historial al cambiar estado de cuña"""
        cuña = CuñaPublicitaria.objects.create(
            codigo='TEST001',
            titulo='Test',
            cliente=self.cliente_user,
            categoria=self.categoria,
            estado='borrador',
            duracion_planeada=30,
            precio_total=Decimal('300.00'),
            repeticiones_dia=3,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=30),
            created_by=self.admin_user
        )
        
        # Cambiar estado
        cuña.estado = 'activa'
        cuña.save()
        
        # Verificar que se creó historial
        historial = HistorialEstadoSemaforo.objects.filter(cuña=cuña)
        self.assertTrue(historial.exists())


class PerformanceTestCase(TestCase):
    """Tests de rendimiento para operaciones críticas"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            rol='admin'
        )
        
        self.categoria = CategoriaPublicitaria.objects.create(
            nombre='Categoría Test'
        )
        
        # Crear múltiples usuarios cliente
        self.clientes = []
        for i in range(10):
            cliente = User.objects.create_user(
                username=f'cliente_{i}',
                email=f'cliente{i}@test.com',
                password='testpass123',
                rol='cliente'
            )
            self.clientes.append(cliente)
    
    def test_recalculo_masivo_performance(self):
        """Test rendimiento del recálculo masivo"""
        import time
        
        # Crear múltiples cuñas
        cuñas = []
        for i, cliente in enumerate(self.clientes):
            cuña = CuñaPublicitaria.objects.create(
                codigo=f'TEST{i:03d}',
                titulo=f'Test {i}',
                cliente=cliente,
                categoria=self.categoria,
                estado='activa',
                duracion_planeada=30,
                precio_total=Decimal('300.00'),
                repeticiones_dia=3,
                fecha_inicio=timezone.now().date(),
                fecha_fin=timezone.now().date() + timedelta(days=30),
                created_by=self.admin_user
            )
            cuñas.append(cuña)
        
        # Medir tiempo de recálculo masivo
        calculator = StatusCalculator()
        
        start_time = time.time()
        stats = calculator.actualizar_todas_las_cuñas()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Verificar que se procesaron todas las cuñas
        self.assertEqual(stats['total_procesadas'], len(cuñas))
        
        # Verificar que el tiempo de ejecución es razonable (menos de 5 segundos para 10 cuñas)
        self.assertLess(execution_time, 5.0)
        
        print(f"Recálculo masivo de {len(cuñas)} cuñas: {execution_time:.2f} segundos")


class EdgeCasesTestCase(TestCase):
    """Tests para casos extremos y situaciones inusuales"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            rol='admin'
        )
        
        self.cliente_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='testpass123',
            rol='cliente'
        )
        
        self.categoria = CategoriaPublicitaria.objects.create(
            nombre='Categoría Test'
        )
        
        self.calculator = StatusCalculator()
    
    def test_cuña_sin_fechas(self):
        """Test manejo de cuña sin fechas definidas"""
        cuña = CuñaPublicitaria.objects.create(
            codigo='TEST001',
            titulo='Test sin fechas',
            cliente=self.cliente_user,
            categoria=self.categoria,
            estado='activa',
            duracion_planeada=30,
            precio_total=Decimal('300.00'),
            repeticiones_dia=3,
            # fecha_inicio=None,  # Sin fechas
            # fecha_fin=None,
            created_by=self.admin_user
        )
        
        resultado = self.calculator.calcular_estado_cuña(cuña)
        
        self.assertEqual(resultado['color'], 'gris')
        self.assertIn('sin fechas', resultado['razon'].lower())
    
    def test_cuña_fecha_fin_anterior_inicio(self):
        """Test validación de fechas inválidas en cuña"""
        with self.assertRaises(ValidationError):
            cuña = CuñaPublicitaria(
                codigo='TEST001',
                titulo='Test fechas inválidas',
                cliente=self.cliente_user,
                categoria=self.categoria,
                estado='activa',
                duracion_planeada=30,
                precio_total=Decimal('300.00'),
                repeticiones_dia=3,
                fecha_inicio=timezone.now().date(),
                fecha_fin=timezone.now().date() - timedelta(days=1),  # Anterior al inicio
                created_by=self.admin_user
            )
            cuña.full_clean()  # Esto debe lanzar ValidationError
    
    def test_configuracion_umbrales_extremos(self):
        """Test configuración con umbrales extremos"""
        config = ConfiguracionSemaforo.objects.create(
            nombre="Extremos",
            dias_verde_min=365,  # Un año
            dias_amarillo_min=180,  # 6 meses
            porcentaje_verde_max=Decimal('10.00'),  # Muy restrictivo
            porcentaje_amarillo_max=Decimal('50.00'),
            created_by=self.admin_user
        )
        
        calculator = StatusCalculator(config)
        
        # Cuña con 200 días restantes debería ser verde con esta configuración
        cuña = CuñaPublicitaria.objects.create(
            codigo='TEST001',
            titulo='Test extremos',
            cliente=self.cliente_user,
            categoria=self.categoria,
            estado='activa',
            duracion_planeada=30,
            precio_total=Decimal('300.00'),
            repeticiones_dia=3,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=200),
            created_by=self.admin_user
        )
        
        resultado = calculator.calcular_estado_cuña(cuña)
        self.assertEqual(resultado['color'], 'amarillo')  # Por tiempo transcurrido
    
    def test_alerta_sin_configuracion_activa(self):
        """Test manejo cuando no hay configuración activa"""
        # Eliminar todas las configuraciones
        ConfiguracionSemaforo.objects.all().delete()
        
        # Crear nueva calculadora (debe crear configuración por defecto)
        calculator = StatusCalculator()
        
        self.assertIsNotNone(calculator.configuracion)
        self.assertTrue(calculator.configuracion.is_active)