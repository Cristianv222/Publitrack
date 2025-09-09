"""
Tests para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Pruebas unitarias y de integración
"""

import os
import tempfile
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, Mock

from .models import (
    CategoriaPublicitaria,
    TipoContrato,
    ArchivoAudio,
    CuñaPublicitaria,
    HistorialCuña
)
from .forms import (
    CategoriaPublicitariaForm,
    CuñaPublicitariaForm,
    ArchivoAudioForm
)

User = get_user_model()

# ==================== CONFIGURACIÓN BASE PARA TESTS ====================

class BaseTestCase(TestCase):
    """Clase base para tests con datos comunes"""
    
    @classmethod
    def setUpTestData(cls):
        """Configuración inicial de datos para todos los tests"""
        # Crear grupos de usuarios
        cls.grupo_admin = Group.objects.create(name='Administradores')
        cls.grupo_vendedores = Group.objects.create(name='Vendedores')
        cls.grupo_clientes = Group.objects.create(name='Clientes')
        cls.grupo_supervisores = Group.objects.create(name='Supervisores')
        
        # Crear usuarios de prueba
        cls.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            first_name='Admin',
            last_name='Test'
        )
        cls.admin_user.groups.add(cls.grupo_admin)
        
        cls.vendedor_user = User.objects.create_user(
            username='vendedor_test',
            email='vendedor@test.com',
            password='testpass123',
            first_name='Vendedor',
            last_name='Test'
        )
        cls.vendedor_user.groups.add(cls.grupo_vendedores)
        
        cls.cliente_user = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='testpass123',
            first_name='Cliente',
            last_name='Test'
        )
        cls.cliente_user.groups.add(cls.grupo_clientes)
        
        # Crear categoría de prueba
        cls.categoria = CategoriaPublicitaria.objects.create(
            nombre='Comercio Local Test',
            descripcion='Categoría de prueba',
            color_codigo='#FF0000',
            tarifa_base=Decimal('2.50')
        )
        
        # Crear tipo de contrato de prueba
        cls.tipo_contrato = TipoContrato.objects.create(
            nombre='Mensual Test',
            descripcion='Contrato de prueba',
            duracion_tipo='mensual',
            duracion_dias=30,
            repeticiones_minimas=2,
            descuento_porcentaje=Decimal('10.00')
        )

# ==================== TESTS DE MODELOS ====================

class CategoriaPublicitariaModelTest(BaseTestCase):
    """Tests para el modelo CategoriaPublicitaria"""
    
    def test_crear_categoria_valida(self):
        """Test crear categoría con datos válidos"""
        categoria = CategoriaPublicitaria.objects.create(
            nombre='Nueva Categoría',
            descripcion='Descripción de prueba',
            color_codigo='#00FF00',
            tarifa_base=Decimal('3.00')
        )
        
        self.assertEqual(categoria.nombre, 'Nueva Categoría')
        self.assertEqual(categoria.tarifa_base, Decimal('3.00'))
        self.assertTrue(categoria.is_active)
        self.assertIsNotNone(categoria.created_at)
    
    def test_str_representation(self):
        """Test representación string de categoría"""
        self.assertEqual(str(self.categoria), 'Comercio Local Test')
    
    def test_get_absolute_url(self):
        """Test URL absoluta de categoría"""
        url = self.categoria.get_absolute_url()
        expected_url = reverse('content:categoria_detail', kwargs={'pk': self.categoria.pk})
        self.assertEqual(url, expected_url)

class TipoContratoModelTest(BaseTestCase):
    """Tests para el modelo TipoContrato"""
    
    def test_crear_tipo_contrato_valido(self):
        """Test crear tipo de contrato válido"""
        tipo = TipoContrato.objects.create(
            nombre='Anual Premium',
            descripcion='Contrato anual con descuento',
            duracion_tipo='anual',
            duracion_dias=365,
            descuento_porcentaje=Decimal('25.00')
        )
        
        self.assertEqual(tipo.nombre, 'Anual Premium')
        self.assertEqual(tipo.duracion_dias, 365)
        self.assertTrue(tipo.is_active)
    
    def test_str_representation(self):
        """Test representación string de tipo contrato"""
        expected = f"{self.tipo_contrato.nombre} ({self.tipo_contrato.get_duracion_tipo_display()})"
        self.assertEqual(str(self.tipo_contrato), expected)

class ArchivoAudioModelTest(BaseTestCase):
    """Tests para el modelo ArchivoAudio"""
    
    def setUp(self):
        """Configuración específica para tests de audio"""
        # Crear archivo de audio mock
        self.audio_content = b'fake_audio_content_for_testing'
        self.uploaded_file = SimpleUploadedFile(
            "test_audio.mp3",
            self.audio_content,
            content_type="audio/mpeg"
        )
    
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_crear_archivo_audio(self):
        """Test crear archivo de audio"""
        archivo = ArchivoAudio.objects.create(
            archivo=self.uploaded_file,
            nombre_original='test_audio.mp3',
            formato='mp3',
            duracion_segundos=30,
            subido_por=self.admin_user
        )
        
        self.assertEqual(archivo.nombre_original, 'test_audio.mp3')
        self.assertEqual(archivo.formato, 'mp3')
        self.assertEqual(archivo.duracion_segundos, 30)
        self.assertEqual(archivo.subido_por, self.admin_user)
    
    def test_duracion_formateada(self):
        """Test formato de duración"""
        archivo = ArchivoAudio(duracion_segundos=125)  # 2:05
        self.assertEqual(archivo.duracion_formateada, '02:05')
        
        archivo = ArchivoAudio(duracion_segundos=45)   # 0:45
        self.assertEqual(archivo.duracion_formateada, '00:45')
        
        archivo = ArchivoAudio(duracion_segundos=None)
        self.assertEqual(archivo.duracion_formateada, '00:00')
    
    def test_tamaño_formateado(self):
        """Test formato de tamaño de archivo"""
        archivo = ArchivoAudio(tamaño_bytes=1024)
        self.assertEqual(archivo.tamaño_formateado, '1.0 KB')
        
        archivo = ArchivoAudio(tamaño_bytes=1048576)  # 1 MB
        self.assertEqual(archivo.tamaño_formateado, '1.0 MB')
        
        archivo = ArchivoAudio(tamaño_bytes=None)
        self.assertEqual(archivo.tamaño_formateado, '0 B')

class CuñaPublicitariaModelTest(BaseTestCase):
    """Tests para el modelo CuñaPublicitaria"""
    
    def setUp(self):
        """Configuración específica para tests de cuñas"""
        self.cuña_data = {
            'titulo': 'Cuña de Prueba',
            'descripcion': 'Descripción de prueba',
            'cliente': self.cliente_user,
            'vendedor_asignado': self.vendedor_user,
            'categoria': self.categoria,
            'tipo_contrato': self.tipo_contrato,
            'duracion_planeada': 30,
            'precio_total': Decimal('150.00'),
            'repeticiones_dia': 3,
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() + timedelta(days=30),
            'created_by': self.admin_user
        }
    
    def test_crear_cuña_valida(self):
        """Test crear cuña con datos válidos"""
        cuña = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        self.assertEqual(cuña.titulo, 'Cuña de Prueba')
        self.assertEqual(cuña.cliente, self.cliente_user)
        self.assertEqual(cuña.estado, 'borrador')
        self.assertIsNotNone(cuña.codigo)
        self.assertTrue(cuña.codigo.startswith('CP'))
    
    def test_generar_codigo_automatico(self):
        """Test generación automática de código"""
        cuña = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        # El código debe seguir el formato CP{año}{mes}{contador}
        año_mes = timezone.now().strftime('%Y%m')
        self.assertTrue(cuña.codigo.startswith(f'CP{año_mes}'))
        self.assertEqual(len(cuña.codigo), 13)  # CP + 6 dígitos fecha + 4 dígitos contador
    
    def test_calcular_precio_por_segundo(self):
        """Test cálculo automático de precio por segundo"""
        cuña = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        precio_esperado = self.cuña_data['precio_total'] / self.cuña_data['duracion_planeada']
        self.assertEqual(cuña.precio_por_segundo, precio_esperado)
    
    def test_dias_restantes(self):
        """Test cálculo de días restantes"""
        # Cuña que vence en 5 días
        self.cuña_data['fecha_fin'] = date.today() + timedelta(days=5)
        cuña = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        self.assertEqual(cuña.dias_restantes, 5)
        
        # Cuña ya vencida
        self.cuña_data['fecha_fin'] = date.today() - timedelta(days=1)
        cuña_vencida = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        self.assertEqual(cuña_vencida.dias_restantes, 0)
    
    def test_esta_activa(self):
        """Test verificación de cuña activa"""
        # Cuña activa en período válido
        self.cuña_data['estado'] = 'activa'
        cuña = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        self.assertTrue(cuña.esta_activa)
        
        # Cuña pausada
        cuña.estado = 'pausada'
        cuña.save()
        
        self.assertFalse(cuña.esta_activa)
    
    def test_esta_vencida(self):
        """Test verificación de cuña vencida"""
        # Cuña vencida
        self.cuña_data['fecha_fin'] = date.today() - timedelta(days=1)
        cuña = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        self.assertTrue(cuña.esta_vencida)
        
        # Cuña vigente
        self.cuña_data['fecha_fin'] = date.today() + timedelta(days=5)
        cuña_vigente = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        self.assertFalse(cuña_vigente.esta_vencida)
    
    def test_clean_validation(self):
        """Test validaciones del método clean()"""
        # Fecha fin anterior a fecha inicio
        cuña = CuñaPublicitaria(**self.cuña_data)
        cuña.fecha_fin = cuña.fecha_inicio - timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            cuña.clean()
    
    def test_metodos_estado(self):
        """Test métodos para cambiar estado de cuña"""
        cuña = CuñaPublicitaria.objects.create(**self.cuña_data)
        
        # Aprobar cuña
        cuña.estado = 'pendiente_revision'
        cuña.save()
        cuña.aprobar(self.admin_user)
        
        self.assertEqual(cuña.estado, 'aprobada')
        self.assertEqual(cuña.aprobada_por, self.admin_user)
        self.assertIsNotNone(cuña.fecha_aprobacion)
        
        # Activar cuña
        cuña.activar()
        self.assertEqual(cuña.estado, 'activa')
        
        # Pausar cuña
        cuña.pausar()
        self.assertEqual(cuña.estado, 'pausada')
        
        # Finalizar cuña
        cuña.finalizar()
        self.assertEqual(cuña.estado, 'finalizada')
    
    def test_semaforo_estado(self):
        """Test cálculo de estado de semáforo"""
        # Cuña vencida debe ser roja
        self.cuña_data['fecha_fin'] = date.today() - timedelta(days=1)
        cuña_vencida = CuñaPublicitaria.objects.create(**self.cuña_data)
        self.assertEqual(cuña_vencida.semaforo_estado, 'rojo')
        
        # Cuña activa debe ser verde
        self.cuña_data['estado'] = 'activa'
        self.cuña_data['fecha_fin'] = date.today() + timedelta(days=30)
        cuña_activa = CuñaPublicitaria.objects.create(**self.cuña_data)
        self.assertEqual(cuña_activa.semaforo_estado, 'verde')

# ==================== TESTS DE FORMULARIOS ====================

class CategoriaPublicitariaFormTest(BaseTestCase):
    """Tests para formulario de categorías"""
    
    def test_formulario_valido(self):
        """Test formulario con datos válidos"""
        form_data = {
            'nombre': 'Nueva Categoría',
            'descripcion': 'Descripción de prueba',
            'color_codigo': '#FF5733',
            'tarifa_base': '3.50',
            'is_active': True
        }
        
        form = CategoriaPublicitariaForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_formulario_color_invalido(self):
        """Test validación de color hexadecimal"""
        form_data = {
            'nombre': 'Categoría Test',
            'color_codigo': 'color_invalido',
            'tarifa_base': '2.00'
        }
        
        form = CategoriaPublicitariaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('color_codigo', form.errors)
    
    def test_formulario_tarifa_negativa(self):
        """Test validación de tarifa negativa"""
        form_data = {
            'nombre': 'Categoría Test',
            'tarifa_base': '-1.00'
        }
        
        form = CategoriaPublicitariaForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tarifa_base', form.errors)

class ArchivoAudioFormTest(BaseTestCase):
    """Tests para formulario de archivos de audio"""
    
    def test_formulario_archivo_valido(self):
        """Test formulario con archivo MP3 válido"""
        audio_file = SimpleUploadedFile(
            "test.mp3",
            b"fake_audio_content",
            content_type="audio/mpeg"
        )
        
        form = ArchivoAudioForm(files={'archivo': audio_file})
        self.assertTrue(form.is_valid())
    
    def test_formulario_extension_invalida(self):
        """Test validación de extensión de archivo"""
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"fake_content",
            content_type="text/plain"
        )
        
        form = ArchivoAudioForm(files={'archivo': invalid_file})
        self.assertFalse(form.is_valid())
        self.assertIn('archivo', form.errors)

class CuñaPublicitariaFormTest(BaseTestCase):
    """Tests para formulario de cuñas publicitarias"""
    
    def test_formulario_cuña_valido(self):
        """Test formulario con datos válidos"""
        form_data = {
            'titulo': 'Cuña de Prueba',
            'descripcion': 'Descripción',
            'cliente': self.cliente_user.id,
            'vendedor_asignado': self.vendedor_user.id,
            'categoria': self.categoria.id,
            'tipo_contrato': self.tipo_contrato.id,
            'duracion_planeada': 30,
            'precio_total': '150.00',
            'repeticiones_dia': 3,
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() + timedelta(days=30),
            'prioridad': 'normal',
            'requiere_aprobacion': True,
            'notificar_vencimiento': True,
            'dias_aviso_vencimiento': 7
        }
        
        form = CuñaPublicitariaForm(data=form_data, user=self.admin_user)
        if not form.is_valid():
            print("Errores del formulario:", form.errors)
        self.assertTrue(form.is_valid())
    
    def test_formulario_fechas_invalidas(self):
        """Test validación de fechas"""
        form_data = {
            'titulo': 'Cuña Test',
            'cliente': self.cliente_user.id,
            'duracion_planeada': 30,
            'precio_total': '100.00',
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() - timedelta(days=1),  # Fecha fin anterior
            'repeticiones_dia': 1
        }
        
        form = CuñaPublicitariaForm(data=form_data, user=self.admin_user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

# ==================== TESTS DE VISTAS ====================

class DashboardViewTest(BaseTestCase):
    """Tests para la vista del dashboard"""
    
    def test_dashboard_acceso_autenticado(self):
        """Test acceso al dashboard con usuario autenticado"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(reverse('content_management:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'total_cuñas')
    
    def test_dashboard_acceso_no_autenticado(self):
        """Test redirección para usuario no autenticado"""
        response = self.client.get(reverse('content_management:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirección a login

class CategoriaViewsTest(BaseTestCase):
    """Tests para vistas de categorías"""
    
    def setUp(self):
        """Configuración para tests de vistas"""
        self.client.login(username='admin_test', password='testpass123')
    
    def test_lista_categorias(self):
        """Test vista de lista de categorías"""
        response = self.client.get(reverse('content_management:categoria_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.categoria.nombre)
    
    def test_detalle_categoria(self):
        """Test vista de detalle de categoría"""
        response = self.client.get(
            reverse('content_management:categoria_detail', kwargs={'pk': self.categoria.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.categoria.nombre)
    
    def test_crear_categoria(self):
        """Test creación de categoría vía POST"""
        data = {
            'nombre': 'Nueva Categoría POST',
            'descripcion': 'Creada vía POST',
            'color_codigo': '#00FF00',
            'tarifa_base': '3.00',
            'is_active': True
        }
        
        response = self.client.post(
            reverse('content_management:categoria_create'),
            data=data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirección después de crear
        self.assertTrue(
            CategoriaPublicitaria.objects.filter(nombre='Nueva Categoría POST').exists()
        )

class CuñaViewsTest(BaseTestCase):
    """Tests para vistas de cuñas"""
    
    def setUp(self):
        """Configuración para tests de cuñas"""
        self.client.login(username='vendedor_test', password='testpass123')
        
        # Crear cuña de prueba
        self.cuña = CuñaPublicitaria.objects.create(
            titulo='Cuña Test Vista',
            cliente=self.cliente_user,
            vendedor_asignado=self.vendedor_user,
            categoria=self.categoria,
            duracion_planeada=30,
            precio_total=Decimal('100.00'),
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            created_by=self.vendedor_user
        )
    
    def test_lista_cuñas_vendedor(self):
        """Test que vendedor solo ve sus cuñas"""
        response = self.client.get(reverse('content_management:cuña_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cuña.titulo)
    
    def test_detalle_cuña_propia(self):
        """Test acceso a detalle de cuña propia"""
        response = self.client.get(
            reverse('content_management:cuña_detail', kwargs={'pk': self.cuña.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cuña.titulo)
    
    def test_acceso_cuña_ajena_prohibido(self):
        """Test que vendedor no puede ver cuñas de otros"""
        # Crear cuña de otro vendedor
        otro_vendedor = User.objects.create_user(
            username='otro_vendedor',
            password='test123'
        )
        otro_vendedor.groups.add(self.grupo_vendedores)
        
        cuña_ajena = CuñaPublicitaria.objects.create(
            titulo='Cuña Ajena',
            cliente=self.cliente_user,
            vendedor_asignado=otro_vendedor,
            categoria=self.categoria,
            duracion_planeada=30,
            precio_total=Decimal('100.00'),
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            created_by=otro_vendedor
        )
        
        response = self.client.get(
            reverse('content_management:cuña_detail', kwargs={'pk': cuña_ajena.pk})
        )
        self.assertEqual(response.status_code, 404)

# ==================== TESTS DE SEÑALES ====================

class SignalsTest(TransactionTestCase):
    """Tests para señales del módulo"""
    
    def setUp(self):
        """Configuración para tests de señales"""
        self.grupo_admin = Group.objects.create(name='Administradores')
        self.admin_user = User.objects.create_user(
            username='admin_signal',
            password='test123'
        )
        self.admin_user.groups.add(self.grupo_admin)
        
        self.categoria = CategoriaPublicitaria.objects.create(
            nombre='Categoría Signal',
            tarifa_base=Decimal('2.00')
        )
    
    def test_historial_creacion_automatica(self):
        """Test que se crea historial automáticamente"""
        cuña = CuñaPublicitaria.objects.create(
            titulo='Cuña Test Signal',
            cliente=self.admin_user,
            categoria=self.categoria,
            duracion_planeada=30,
            precio_total=Decimal('100.00'),
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            created_by=self.admin_user
        )
        
        # Verificar que se creó entrada en historial
        self.assertTrue(
            HistorialCuña.objects.filter(
                cuña=cuña,
                accion='creada'
            ).exists()
        )
    
    def test_historial_edicion_automatica(self):
        """Test historial automático en edición"""
        cuña = CuñaPublicitaria.objects.create(
            titulo='Cuña Original',
            cliente=self.admin_user,
            categoria=self.categoria,
            duracion_planeada=30,
            precio_total=Decimal('100.00'),
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=30),
            created_by=self.admin_user
        )
        
        # Editar cuña
        cuña.titulo = 'Cuña Editada'
        cuña.save()
        
        # Verificar historial de edición
        self.assertTrue(
            HistorialCuña.objects.filter(
                cuña=cuña,
                accion='editada'
            ).exists()
        )

# ==================== TESTS DE INTEGRACION ====================

class IntegrationTest(TransactionTestCase):
    """Tests de integración del módulo completo"""
    
    def setUp(self):
        """Configuración para tests de integración"""
        # Crear grupos
        Group.objects.create(name='Administradores')
        Group.objects.create(name='Vendedores')
        Group.objects.create(name='Clientes')
        
        # Crear usuarios con permisos
        self.admin = User.objects.create_user(
            username='admin_integration',
            password='test123',
            email='admin@test.com'
        )
        self.admin.groups.add(Group.objects.get(name='Administradores'))
        self.admin.is_staff = True
        self.admin.save()
    
    def test_flujo_completo_cuña(self):
        """Test flujo completo: crear categoría, tipo contrato y cuña"""
        self.client.login(username='admin_integration', password='test123')
        
        # 1. Crear categoría
        categoria_data = {
            'nombre': 'Categoría Integración',
            'tarifa_base': '3.00',
            'color_codigo': '#FF0000',
            'is_active': True
        }
        
        response = self.client.post(
            reverse('content_management:categoria_create'),
            data=categoria_data
        )
        self.assertEqual(response.status_code, 302)
        
        categoria = CategoriaPublicitaria.objects.get(nombre='Categoría Integración')
        
        # 2. Crear tipo de contrato
        contrato_data = {
            'nombre': 'Contrato Integración',
            'duracion_tipo': 'mensual',
            'duracion_dias': 30,
            'repeticiones_minimas': 2,
            'descuento_porcentaje': '10.00',
            'is_active': True
        }
        
        response = self.client.post(
            reverse('content_management:tipo_contrato_create'),
            data=contrato_data
        )
        self.assertEqual(response.status_code, 302)
        
        tipo_contrato = TipoContrato.objects.get(nombre='Contrato Integración')
        
        # 3. Crear cliente
        cliente = User.objects.create_user(
            username='cliente_integration',
            password='test123'
        )
        cliente.groups.add(Group.objects.get(name='Clientes'))
        
        # 4. Crear cuña
        cuña_data = {
            'titulo': 'Cuña Integración',
            'descripcion': 'Cuña de prueba integración',
            'cliente': cliente.id,
            'vendedor_asignado': self.admin.id,
            'categoria': categoria.id,
            'tipo_contrato': tipo_contrato.id,
            'duracion_planeada': 30,
            'precio_total': '150.00',
            'repeticiones_dia': 3,
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() + timedelta(days=30),
            'prioridad': 'normal',
            'requiere_aprobacion': True,
            'notificar_vencimiento': True,
            'dias_aviso_vencimiento': 7
        }
        
        response = self.client.post(
            reverse('content_management:cuña_create'),
            data=cuña_data
        )
        
        if response.status_code != 302:
            print("Errores en creación de cuña:", response.context['form'].errors if 'form' in response.context else 'Sin contexto')
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la cuña se creó correctamente
        cuña = CuñaPublicitaria.objects.get(titulo='Cuña Integración')
        self.assertEqual(cuña.cliente, cliente)
        self.assertEqual(cuña.categoria, categoria)
        self.assertEqual(cuña.tipo_contrato, tipo_contrato)
        
        # Verificar que se creó historial
        self.assertTrue(
            HistorialCuña.objects.filter(
                cuña=cuña,
                accion='creada'
            ).exists()
        )

# ==================== COMANDO PARA EJECUTAR TESTS ====================

if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['apps.content_management.tests'])