from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import JsonResponse, FileResponse
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.auth.models import Group, Permission
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from apps.authentication.models import CustomUser
from apps.content_management.models import PlantillaContrato
from apps.orders.models import PlantillaOrden, OrdenGenerada
from apps.orders.models import OrdenToma 
from apps.parte_mortorios.models import ParteMortorio
import csv
import xlwt
from django.http import HttpResponse
from datetime import datetime
from apps.reports_analytics.models import DashboardContratos
from apps.content_management.models import ContratoGenerado
import plotly.express as px
import plotly.offline as pyo
import plotly.io as pio
# Obtener el modelo de usuario correcto
User = get_user_model()

# IMPORTS CONDICIONALES PARA MODELOS
try:
    from apps.content_management.models import (
        CuñaPublicitaria, 
        CategoriaPublicitaria, 
        TipoContrato, 
        ArchivoAudio,
        ContratoGenerado,
    )
    CONTENT_MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando modelos de content_management: {e}")
    CONTENT_MODELS_AVAILABLE = False
    CuñaPublicitaria = None
    CategoriaPublicitaria = None
    TipoContrato = None
    ArchivoAudio = None
    ContratoGenerado = None
try:
    import plotly.express as px
    import plotly.offline as pyo
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️ Plotly no está disponible. Las gráficas no se mostrarán.")
try:
    from apps.reports_analytics.models import DashboardContratos, ReporteContratos
    REPORTS_MODELS_AVAILABLE = True
except ImportError as e:
    print("Error importando modelos de reports_analytics:", e)
    REPORTS_MODELS_AVAILABLE = False
    DashboardContratos = None
    ReporteContratos = None

try:
    from apps.transmission_control.models import ProgramacionTransmision
    TRANSMISSION_MODELS_AVAILABLE = True
except ImportError:
    ProgramacionTransmision = None
    TRANSMISSION_MODELS_AVAILABLE = False

try:
    from apps.traffic_light_system.models import (
        EstadoSemaforo, 
        ConfiguracionSemaforo,
        HistorialEstadoSemaforo,
        AlertaSemaforo,
        ResumenEstadosSemaforo
    )
    TRAFFIC_MODELS_AVAILABLE = True
except ImportError:
    TRAFFIC_MODELS_AVAILABLE = False
    EstadoSemaforo = None
    ConfiguracionSemaforo = None
    HistorialEstadoSemaforo = None
    AlertaSemaforo = None
    ResumenEstadosSemaforo = None
try:
    from apps.orders.models import PlantillaOrden, OrdenGenerada, OrdenToma
    ORDERS_MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando modelos de orders: {e}")
    ORDERS_MODELS_AVAILABLE = False
    PlantillaOrden = None
    OrdenGenerada = None
    OrdenToma = None
# IMPORTS CONDICIONALES PARA PARTE MORTORIOS
try:
    from apps.parte_mortorios.models import (
        ParteMortorio, 
        HistorialParteMortorio,
        PlantillaParteMortorio,
        ParteMortorioGenerado
    )
    PARTE_MORTORIO_MODELS_AVAILABLE = True

except ImportError as e:
    print(f"⚠️ Error importando modelos de parte_mortorios: {e}")
    PARTE_MORTORIO_MODELS_AVAILABLE = False
    ParteMortorio = None
    HistorialParteMortorio = None
    PlantillaParteMortorio = None
    ParteMortorioGenerado = None
# ==================== IMPORTS PARA REPORTES ====================
try:
    from apps.content_management.models import ContratoGenerado, CuñaPublicitaria
    CONTENT_MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando modelos de content_management: {e}")
    CONTENT_MODELS_AVAILABLE = False
    ContratoGenerado = None
    CuñaPublicitaria = None

try:
    from apps.reports_analytics.models import ReporteContratos, DashboardContratos
    REPORTS_MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Error importando modelos de reports_analytics: {e}")
    REPORTS_MODELS_AVAILABLE = False
    ReporteContratos = None
    DashboardContratos = None
def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_superuser or user.is_staff or getattr(user, 'rol', None) == 'admin'

# ==================== APIs PARA PANTEONES ====================

@login_required
@user_passes_test(is_admin)
def api_panteones(request):
    """API para obtener panteones"""
    try:
        # Datos de ejemplo - reemplazar con tu modelo real
        panteones = [
            {
                'id': 1,
                'codigo': 'PAN-001',
                'nombre': 'Panteón Familiar Ejemplo',
                'ubicacion': 'Sector A - Nivel 1',
                'capacidad': 4,
                'ocupados': 2,
                'estado': 'disponible',
                'responsable': 'Admin Cementerio'
            },
            {
                'id': 2,
                'codigo': 'PAN-002',
                'nombre': 'Panteón Comunitario',
                'ubicacion': 'Sector B - Nivel 2',
                'capacidad': 6,
                'ocupados': 6,
                'estado': 'completo',
                'responsable': 'Admin Cementerio'
            }
        ]
        
        return JsonResponse({'success': True, 'panteones': panteones})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==================== APIs PARA CONTRATOS ====================

@login_required
@user_passes_test(is_admin)
def api_plantillas_contrato(request):
    """API para obtener todas las plantillas de contrato activas"""
    try:
        plantillas = PlantillaContrato.objects.filter(is_active=True).order_by('-is_default', 'nombre')
        
        data = []
        for plantilla in plantillas:
            data.append({
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'tipo_contrato': plantilla.tipo_contrato,
                'tipo_contrato_display': plantilla.get_tipo_contrato_display(),
                'version': plantilla.version,
                'incluye_iva': plantilla.incluye_iva,
                'porcentaje_iva': str(plantilla.porcentaje_iva),
                'is_default': plantilla.is_default,
                'descripcion': plantilla.descripcion or '',
                'archivo_url': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None
            })
        
        return JsonResponse({'success': True, 'plantillas': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def api_clientes_activos(request):
    """API para obtener todos los clientes activos"""
    try:
        clientes = CustomUser.objects.filter(
            rol='cliente',
            is_active=True
        ).order_by('empresa', 'first_name', 'last_name')
        
        data = []
        for cliente in clientes:
            data.append({
                'id': cliente.id,
                'nombre_completo': cliente.get_full_name(),
                'empresa': cliente.empresa or '',
                'ruc_dni': cliente.ruc_dni or '',
                'email': cliente.email,
                'telefono': cliente.telefono or '',
                'ciudad': cliente.ciudad or '',
                'direccion': cliente.direccion_exacta or '',
                'vendedor_asignado': cliente.vendedor_asignado.get_full_name() if cliente.vendedor_asignado else ''
            })
        
        return JsonResponse({'success': True, 'clientes': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def api_plantilla_detalle(request, id):
    """API para obtener detalles de una plantilla específica"""
    try:
        plantilla = PlantillaContrato.objects.get(id=id)
        
        data = {
            'id': plantilla.id,
            'nombre': plantilla.nombre,
            'tipo_contrato': plantilla.tipo_contrato,
            'tipo_contrato_display': plantilla.get_tipo_contrato_display(),
            'version': plantilla.version,
            'descripcion': plantilla.descripcion or '',
            'incluye_iva': plantilla.incluye_iva,
            'porcentaje_iva': str(plantilla.porcentaje_iva),
            'is_default': plantilla.is_default,
            'instrucciones': plantilla.instrucciones or '',
            'variables_disponibles': plantilla.variables_disponibles,
            'archivo_url': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None
        }
        
        return JsonResponse({'success': True, 'plantilla': data})
    
    except PlantillaContrato.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def api_cliente_detalle(request, id):
    """API para obtener detalles de un cliente específico"""
    try:
        cliente = CustomUser.objects.get(id=id, rol='cliente')
        
        data = {
            'id': cliente.id,
            'username': cliente.username,
            'nombre_completo': cliente.get_full_name(),
            'empresa': cliente.empresa or '',
            'ruc_dni': cliente.ruc_dni or '',
            'email': cliente.email,
            'telefono': cliente.telefono or '',
            'ciudad': cliente.ciudad or '',
            'provincia': cliente.provincia or '',
            'direccion_exacta': cliente.direccion_exacta or '',
            'razon_social': cliente.razon_social or '',
            'giro_comercial': cliente.giro_comercial or '',
            'vendedor_asignado': cliente.vendedor_asignado.get_full_name() if cliente.vendedor_asignado else '',
            'vendedor_asignado_id': cliente.vendedor_asignado.id if cliente.vendedor_asignado else None
        }
        
        return JsonResponse({'success': True, 'cliente': data})
    
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==================== CONTRATOS GENERADOS ====================
@login_required
@user_passes_test(is_admin)
def contratos_generados_list(request):
    """Vista principal para gestión de contratos generados"""
    
    print("\n" + "="*80)
    print("🔍 INICIANDO contratos_generados_list")
    print("="*80)
    
    # Obtener plantillas activas
    plantillas = PlantillaContrato.objects.filter(is_active=True).order_by('-is_default', 'nombre')
    print(f"📄 Plantillas encontradas: {plantillas.count()}")
    
    # Obtener clientes activos
    clientes = CustomUser.objects.filter(
        rol='cliente',
        is_active=True
    ).order_by('empresa', 'username')
    print(f"👥 Clientes encontrados: {clientes.count()}")
    
    # Inicializar variables
    contratos_recientes = []
    total_contratos = 0
    contratos_hoy = 0
    contratos_mes = 0
    contratos_activos = 0  # ✅ NUEVA VARIABLE
    contratos_pendientes = 0  # ✅ NUEVA VARIABLE
    
    # Verificar disponibilidad del modelo
    print(f"\n📊 CONTENT_MODELS_AVAILABLE: {CONTENT_MODELS_AVAILABLE}")
    
    if CONTENT_MODELS_AVAILABLE:
        print(f"📊 ContratoGenerado is None: {ContratoGenerado is None}")
        
        if ContratoGenerado is not None:
            try:
                from datetime import timedelta
                
                # ✅ Obtener TODOS los contratos sin filtros
                all_contratos = ContratoGenerado.objects.all()
                print(f"\n✅ Total contratos en BD (sin filtros): {all_contratos.count()}")
                
                # Listar los primeros 3 contratos para debug
                if all_contratos.exists():
                    print("\n📋 Primeros 3 contratos (RAW):")
                    for idx, c in enumerate(all_contratos[:3], 1):
                        print(f"   {idx}. ID:{c.id} | Num:{c.numero_contrato} | Cliente:{c.nombre_cliente} | Estado:{c.estado}")
                
                # Obtener contratos recientes con select_related
                contratos_recientes = list(
                    ContratoGenerado.objects
                    .select_related('cliente', 'plantilla_usada', 'generado_por')
                    .order_by('-fecha_generacion')[:10]
                )
                
                print(f"✅ Contratos recientes (después de select_related): {len(contratos_recientes)}")
                
                # Calcular estadísticas
                total_contratos = ContratoGenerado.objects.count()
                contratos_hoy = ContratoGenerado.objects.filter(
                    fecha_generacion__date=timezone.now().date()
                ).count()
                contratos_mes = ContratoGenerado.objects.filter(
                    fecha_generacion__gte=timezone.now() - timedelta(days=30)
                ).count()
                
                # ✅ NUEVAS ESTADÍSTICAS: Contratos activos y pendientes
                contratos_activos = ContratoGenerado.objects.filter(
                    estado='validado'
                ).count()
                
                contratos_pendientes = ContratoGenerado.objects.filter(
                    estado='generado'
                ).count()
                
                print(f"✅ Contratos hoy: {contratos_hoy}")
                print(f"✅ Contratos último mes: {contratos_mes}")
                print(f"✅ Contratos activos (validados): {contratos_activos}")  # ✅ NUEVO
                print(f"✅ Contratos pendientes (generados): {contratos_pendientes}")  # ✅ NUEVO
                
                # Detalles de cada contrato reciente
                if contratos_recientes:
                    print("\n📋 Detalles de contratos recientes:")
                    for idx, c in enumerate(contratos_recientes, 1):
                        print(f"   {idx}. {c.numero_contrato} | {c.nombre_cliente} | {c.estado} | {c.fecha_generacion}")
                        print(f"      - Cliente ID: {c.cliente_id if hasattr(c, 'cliente_id') else 'N/A'}")
                        print(f"      - Plantilla: {c.plantilla_usada.nombre if c.plantilla_usada else 'N/A'}")
                        if idx >= 3:  # Solo mostrar 3 para no llenar los logs
                            break
                
            except Exception as e:
                import traceback
                print(f"\n❌ ERROR al cargar contratos:")
                print(f"   Tipo de error: {type(e).__name__}")
                print(f"   Mensaje: {str(e)}")
                print(f"\n📋 Traceback completo:")
                print(traceback.format_exc())
        else:
            print("❌ ContratoGenerado es None")
    else:
        print("❌ CONTENT_MODELS_AVAILABLE es False")
    
    plantillas_activas = plantillas.count()
    
    context = {
        'plantillas': plantillas,
        'clientes': clientes,
        'contratos_recientes': contratos_recientes,
        'total_contratos': total_contratos,
        'contratos_hoy': contratos_hoy,
        'contratos_mes': contratos_mes,
        'contratos_activos': contratos_activos,  # ✅ NUEVA VARIABLE
        'contratos_pendientes': contratos_pendientes,  # ✅ NUEVA VARIABLE
        'plantillas_activas': plantillas_activas,
    }
    
    print(f"\n📦 CONTEXT FINAL:")
    print(f"   - plantillas: {type(context['plantillas'])} | Count: {context['plantillas'].count()}")
    print(f"   - clientes: {type(context['clientes'])} | Count: {context['clientes'].count()}")
    print(f"   - contratos_recientes: {type(context['contratos_recientes'])} | Len: {len(context['contratos_recientes'])}")
    print(f"   - total_contratos: {context['total_contratos']}")
    print(f"   - contratos_hoy: {context['contratos_hoy']}")
    print(f"   - contratos_mes: {context['contratos_mes']}")
    print(f"   - contratos_activos: {context['contratos_activos']}")  # ✅ NUEVO
    print(f"   - contratos_pendientes: {context['contratos_pendientes']}")  # ✅ NUEVO
    print(f"   - plantillas_activas: {context['plantillas_activas']}")
    print("="*80 + "\n")
    
    return render(request, 'custom_admin/contratos/list.html', context)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def contrato_generar_api(request):
    """API para generar un contrato desde una plantilla"""
    try:
        from apps.content_management.models import ContratoGenerado
        from datetime import datetime
        
        data = json.loads(request.body)
        
        # Obtener plantilla y cliente
        plantilla = PlantillaContrato.objects.get(id=data['plantilla_id'])
        cliente = CustomUser.objects.get(id=data['cliente_id'], rol='cliente')
        
        # Validar que la plantilla tenga archivo
        if not plantilla.archivo_plantilla:
            return JsonResponse({
                'success': False,
                'error': 'La plantilla no tiene un archivo asociado'
            }, status=400)
        
        # ✅ CREAR CONTRATO CON EL NUEVO CÁLCULO
        contrato = ContratoGenerado.objects.create(
            plantilla_usada=plantilla,
            cliente=cliente,
            nombre_cliente=cliente.empresa or cliente.get_full_name(),
            ruc_dni_cliente=cliente.ruc_dni or '',
            valor_sin_iva=Decimal(str(data['valor_total'])),  # Usamos el valor total calculado
            generado_por=request.user,
            estado='borrador'
        )
        
        # ✅ GUARDAR DATOS PARA USAR DESPUÉS AL CREAR LA CUÑA
        contrato.datos_generacion = {
            'FECHA_INICIO_RAW': data['fecha_inicio'],
            'FECHA_FIN_RAW': data['fecha_fin'],
            'SPOTS_DIA': data.get('spots_dia', 1),
            'DURACION_SPOT': data.get('duracion_spot', 30),
            'VALOR_POR_SEGUNDO': data.get('valor_por_segundo', 0),  # Nuevo campo
            'OBSERVACIONES': data.get('observaciones', '')
        }
        contrato.save()
        
        # Generar el archivo del contrato
        if contrato.generar_contrato():
            return JsonResponse({
                'success': True,
                'message': 'Contrato generado exitosamente',
                'contrato_id': contrato.id,
                'numero_contrato': contrato.numero_contrato,
                'archivo_url': contrato.archivo_contrato_pdf.url if contrato.archivo_contrato_pdf else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error al generar el archivo del contrato'
            }, status=500)
        
    except PlantillaContrato.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except CustomUser.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        import traceback
        print("="*50)
        print("ERROR AL GENERAR CONTRATO:")
        print(traceback.format_exc())
        print("="*50)
        return JsonResponse({
            'success': False,
            'error': f'Error al generar el contrato: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
def contrato_detalle(request, contrato_id):
    """Vista para ver el detalle completo de un contrato"""
    try:
        from apps.content_management.models import ContratoGenerado
        
        contrato = get_object_or_404(ContratoGenerado.objects.select_related(
            'cliente', 'plantilla_usada', 'generado_por', 'cuña'
        ), pk=contrato_id)
        
        # Obtener información adicional del cliente
        cliente_info = {
            'telefono': contrato.cliente.telefono if contrato.cliente else '',
            'email': contrato.cliente.email if contrato.cliente else '',
            'direccion': contrato.cliente.direccion_exacta if contrato.cliente else '',
            'ciudad': contrato.cliente.ciudad if contrato.cliente else '',
            'cargo_empresa': contrato.cliente.cargo_empresa if contrato.cliente else '',
            'profesion': contrato.cliente.profesion if contrato.cliente else '',
        }
        
        # Obtener información de la cuña si existe
        cuña_info = {}
        if contrato.cuña:
            cuña_info = {
                'codigo': contrato.cuña.codigo,
                'titulo': contrato.cuña.titulo,
                'estado': contrato.cuña.estado,
                'fecha_inicio': contrato.cuña.fecha_inicio,
                'fecha_fin': contrato.cuña.fecha_fin,
                'duracion_planeada': contrato.cuña.duracion_planeada,
                'repeticiones_dia': contrato.cuña.repeticiones_dia,
            }
        
        context = {
            'contrato': contrato,
            'cliente_info': cliente_info,
            'cuña_info': cuña_info,
            'datos_generacion': contrato.datos_generacion or {},
        }
        
        return render(request, 'custom_admin/contratos/detalle.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en contrato_detalle: {str(e)}")
        messages.error(request, f'Error al cargar el detalle del contrato: {str(e)}')
        return redirect('custom_admin:contratos_generados_list')
# ✅ NUEVA API: Subir contrato validado
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def contrato_subir_validado_api(request, id):
    """API para subir un contrato validado y crear automáticamente la cuña"""
    try:
        from apps.content_management.models import ContratoGenerado
        
        contrato = ContratoGenerado.objects.get(pk=id)
        
        # Validar que se haya enviado un archivo
        if 'archivo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar un archivo PDF'
            }, status=400)
        
        archivo = request.FILES['archivo']
        
        if not archivo.name.endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'El archivo debe ser un PDF'
            }, status=400)
        
        # Guardar el archivo validado
        contrato.archivo_contrato_validado = archivo
        contrato.save()
        
        # ✅ USAR EL MÉTODO ACTUALIZADO que crea la cuña en estado pendiente
        resultado = contrato.validar_y_crear_cuna(user=request.user)
        
        if resultado['success']:
            # Registrar en historial
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(contrato).pk,
                object_id=contrato.pk,
                object_repr=contrato.numero_contrato,
                action_flag=CHANGE,
                change_message=f'Contrato validado y cuña creada automáticamente en estado pendiente (ID: {resultado["cuna_id"]})'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Contrato validado y cuña creada exitosamente en estado pendiente',
                'cuna_id': resultado['cuna_id'],
                'estado_cuna': 'pendiente_revision'  # Informar el estado
            })
        else:
            return JsonResponse({
                'success': False,
                'error': resultado.get('error', 'Error al crear la cuña')
            }, status=500)
        
    except ContratoGenerado.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Contrato no encontrado'}, status=404)
    except Exception as e:
        import traceback
        print("="*50)
        print("ERROR AL SUBIR CONTRATO VALIDADO:")
        print(traceback.format_exc())
        print("="*50)
        return JsonResponse({
            'success': False,
            'error': f'Error al subir el contrato: {str(e)}'
        }, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def contrato_eliminar_api(request, id):
    """API para eliminar un contrato generado"""
    try:
        from apps.content_management.models import ContratoGenerado
        
        contrato = ContratoGenerado.objects.get(pk=id)
        numero = contrato.numero_contrato
        
        # Registrar eliminación
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(contrato).pk,
            object_id=id,
            object_repr=numero,
            action_flag=DELETION,
            change_message=f'Contrato eliminado: {numero}'
        )
        
        contrato.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Contrato eliminado exitosamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==================== PLANTILLAS DE CONTRATO ====================

@login_required
@user_passes_test(is_admin)
def plantillas_contrato_list(request):
    """Vista para listar plantillas de contrato"""
    try:
        plantillas = PlantillaContrato.objects.all().order_by('-created_at')
    except:
        plantillas = []
    
    context = {
        'title': 'Plantillas de Contrato',
        'plantillas': plantillas,
    }
    return render(request, 'custom_admin/plantillas_contrato/list.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def plantilla_contrato_crear_api(request):
    """API para crear una plantilla de contrato"""
    try:
        # Obtener datos del POST (FormData)
        nombre = request.POST.get('nombre')
        tipo_contrato = request.POST.get('tipo_contrato')
        version = request.POST.get('version', '1.0')
        descripcion = request.POST.get('descripcion', '')
        incluye_iva = request.POST.get('incluye_iva') == 'true'
        porcentaje_iva = request.POST.get('porcentaje_iva', '15.00')
        is_active = request.POST.get('is_active') == 'true'
        is_default = request.POST.get('is_default') == 'true'
        instrucciones = request.POST.get('instrucciones', '')
        archivo_plantilla = request.FILES.get('archivo_plantilla')
        
        # Validar campos requeridos
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        if not tipo_contrato:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de contrato es obligatorio'
            }, status=400)
        
        # Si se marca como default, desmarcar las demás
        if is_default:
            PlantillaContrato.objects.all().update(is_default=False)
        
        # Crear la plantilla
        plantilla = PlantillaContrato.objects.create(
            nombre=nombre,
            tipo_contrato=tipo_contrato,
            version=version,
            descripcion=descripcion,
            incluye_iva=incluye_iva,
            porcentaje_iva=porcentaje_iva,
            is_active=is_active,
            is_default=is_default,
            instrucciones=instrucciones,
            created_by=request.user
        )
        
        # Asignar archivo si existe
        if archivo_plantilla:
            plantilla.archivo_plantilla = archivo_plantilla
            plantilla.save()
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(plantilla).pk,
            object_id=plantilla.pk,
            object_repr=str(plantilla.nombre),
            action_flag=ADDITION,
            change_message=f'Plantilla creada: {plantilla.nombre} - Tipo: {plantilla.get_tipo_contrato_display()}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla creada exitosamente',
            'id': plantilla.id
        })
        
    except Exception as e:
        import traceback
        print("="*50)
        print("ERROR AL CREAR PLANTILLA:")
        print(traceback.format_exc())
        print("="*50)
        return JsonResponse({
            'success': False,
            'error': f'Error al crear la plantilla: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
def plantilla_contrato_detalle_api(request, id):
    """API para obtener detalles de una plantilla de contrato"""
    try:
        plantilla = PlantillaContrato.objects.get(pk=id)
        
        data = {
            'id': plantilla.id,
            'nombre': plantilla.nombre,
            'tipo_contrato': plantilla.tipo_contrato,
            'tipo_contrato_display': plantilla.get_tipo_contrato_display() if hasattr(plantilla, 'get_tipo_contrato_display') else plantilla.tipo_contrato,
            'version': plantilla.version,
            'descripcion': plantilla.descripcion or '',
            'incluye_iva': plantilla.incluye_iva,
            'porcentaje_iva': str(plantilla.porcentaje_iva),
            'is_active': plantilla.is_active,
            'is_default': plantilla.is_default,
            'instrucciones': plantilla.instrucciones or '',
            'archivo_plantilla': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None,
            'created_by': plantilla.created_by.username if plantilla.created_by else None,
            'created_at': plantilla.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(plantilla, 'created_at') else None,
            'updated_at': plantilla.updated_at.strftime('%d/%m/%Y %H:%M') if hasattr(plantilla, 'updated_at') else None,
            'contratos_count': plantilla.contratos_generados.count() if hasattr(plantilla, 'contratos_generados') else 0,
            'variables_disponibles': plantilla.variables_disponibles if hasattr(plantilla, 'variables_disponibles') else {}
        }
        
        return JsonResponse(data)
    except PlantillaContrato.DoesNotExist:
        return JsonResponse({'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        import traceback
        print("="*50)
        print("ERROR AL OBTENER DETALLE:")
        print(traceback.format_exc())
        print("="*50)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "POST"])
def plantilla_contrato_actualizar_api(request, id):
    """API para actualizar una plantilla de contrato"""
    try:
        plantilla = PlantillaContrato.objects.get(pk=id)
        
        # Si viene como PUT con JSON
        if request.method == 'PUT':
            data = json.loads(request.body)
            nombre = data.get('nombre', plantilla.nombre)
            tipo_contrato = data.get('tipo_contrato', plantilla.tipo_contrato)
            version = data.get('version', plantilla.version)
            descripcion = data.get('descripcion', plantilla.descripcion)
            incluye_iva = data.get('incluye_iva', plantilla.incluye_iva)
            porcentaje_iva = data.get('porcentaje_iva', plantilla.porcentaje_iva)
            is_active = data.get('is_active', plantilla.is_active)
            is_default = data.get('is_default', plantilla.is_default)
            instrucciones = data.get('instrucciones', plantilla.instrucciones)
            archivo_plantilla = None
        # Si viene como POST con FormData
        else:
            nombre = request.POST.get('nombre', plantilla.nombre)
            tipo_contrato = request.POST.get('tipo_contrato', plantilla.tipo_contrato)
            version = request.POST.get('version', plantilla.version)
            descripcion = request.POST.get('descripcion', plantilla.descripcion)
            incluye_iva = request.POST.get('incluye_iva') == 'true'
            porcentaje_iva = request.POST.get('porcentaje_iva', plantilla.porcentaje_iva)
            is_active = request.POST.get('is_active') == 'true'
            is_default = request.POST.get('is_default') == 'true'
            instrucciones = request.POST.get('instrucciones', plantilla.instrucciones)
            archivo_plantilla = request.FILES.get('archivo_plantilla')
        
        nombre_anterior = plantilla.nombre
        
        # Si se marca como default, desmarcar las demás
        if is_default and not plantilla.is_default:
            PlantillaContrato.objects.exclude(pk=id).update(is_default=False)
        
        # Actualizar campos
        plantilla.nombre = nombre
        plantilla.tipo_contrato = tipo_contrato
        plantilla.version = version
        plantilla.descripcion = descripcion
        plantilla.incluye_iva = incluye_iva
        plantilla.porcentaje_iva = porcentaje_iva
        plantilla.is_active = is_active
        plantilla.is_default = is_default
        plantilla.instrucciones = instrucciones
        
        # Actualizar archivo si viene uno nuevo
        if archivo_plantilla:
            plantilla.archivo_plantilla = archivo_plantilla
        
        plantilla.save()
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(plantilla).pk,
            object_id=plantilla.pk,
            object_repr=str(plantilla.nombre),
            action_flag=CHANGE,
            change_message=f'Plantilla modificada: {nombre_anterior} → {plantilla.nombre}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla actualizada exitosamente'
        })
        
    except PlantillaContrato.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        import traceback
        print("="*50)
        print("ERROR AL ACTUALIZAR PLANTILLA:")
        print(traceback.format_exc())
        print("="*50)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def plantilla_contrato_eliminar_api(request, id):
    """API para eliminar una plantilla de contrato"""
    try:
        plantilla = PlantillaContrato.objects.get(pk=id)
        nombre = plantilla.nombre
        
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(plantilla).pk,
            object_id=id,
            object_repr=nombre,
            action_flag=DELETION,
            change_message=f'Plantilla eliminada: {nombre}'
        )
        
        plantilla.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla eliminada exitosamente'
        })
    except PlantillaContrato.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@login_required
def plantilla_contrato_marcar_default_api(request, id):
    """
    Marca una plantilla de contrato como predeterminada
    y desmarca todas las demás
    """
    try:
        # Obtener la plantilla
        plantilla = PlantillaContrato.objects.get(id=id)
        
        # Verificar permisos
        if not request.user.has_perm('content_management.change_plantillacontrato'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para modificar plantillas'
            }, status=403)
        
        # Desmarcar todas las demás plantillas como default
        PlantillaContrato.objects.exclude(id=id).update(is_default=False)
        
        # Marcar esta plantilla como default
        plantilla.is_default = True
        plantilla.save()
        
        return JsonResponse({
            'success': True,
            'message': f'La plantilla "{plantilla.nombre}" ha sido marcada como predeterminada',
            'plantilla_id': plantilla.id,
            'plantilla_nombre': plantilla.nombre
        })
        
    except PlantillaContrato.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'La plantilla no existe'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al marcar plantilla como predeterminada: {str(e)}'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def plantilla_contrato_descargar_api(request, id):
    """
    Descarga el archivo de una plantilla de contrato
    """
    try:
        from django.http import FileResponse
        import os
        
        # Obtener la plantilla
        plantilla = PlantillaContrato.objects.get(id=id)
        
        # Verificar permisos
        if not request.user.has_perm('content_management.view_plantillacontrato'):
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para descargar plantillas'
            }, status=403)
        
        # Verificar que tenga archivo
        if not plantilla.archivo_plantilla:
            return JsonResponse({
                'success': False,
                'error': 'Esta plantilla no tiene un archivo adjunto'
            }, status=404)
        
        # Obtener la extensión del archivo
        file_name = os.path.basename(plantilla.archivo_plantilla.name)
        file_extension = os.path.splitext(file_name)[1]
        
        # Definir el nombre de descarga
        download_name = f"{plantilla.nombre}{file_extension}"
        
        # Determinar el content_type según la extensión
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
        }
        content_type = content_types.get(file_extension.lower(), 'application/octet-stream')
        
        # Crear la respuesta de descarga
        response = FileResponse(
            plantilla.archivo_plantilla.open('rb'),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{download_name}"'
        
        return response
        
    except PlantillaContrato.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'La plantilla no existe'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al descargar la plantilla: {str(e)}'
        }, status=500)

# ============= DASHBOARD =============
@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Dashboard principal"""
    context = {
        'total_usuarios': User.objects.count(),
        'usuarios_activos': User.objects.filter(is_active=True).count(),
        'total_cunas': 0,
        'cunas_activas': 0,
        'alertas_pendientes': 0,
    }
    
    if CONTENT_MODELS_AVAILABLE and CuñaPublicitaria:
        try:
            context['total_cunas'] = CuñaPublicitaria.objects.count()
            context['cunas_activas'] = CuñaPublicitaria.objects.filter(estado='activa').count()
        except:
            pass
    
    return render(request, 'custom_admin/dashboard.html', context)

# ============= VISTAS DE USUARIOS =============
@login_required
@user_passes_test(is_admin)
def usuarios_list(request):
    """Lista de usuarios del sistema"""
    query = request.GET.get('q')
    usuarios = User.objects.all().prefetch_related('groups')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    # Procesar usuarios para agregar tipo de rol y clase CSS
    usuarios_procesados = []
    for usuario in usuarios:
        # Obtener nombres de grupos del usuario (en minúsculas para comparación)
        grupos_usuario = [g.name.lower() for g in usuario.groups.all()]
        
        # Determinar el tipo de usuario y clase CSS
        if usuario.is_superuser:
            usuario.tipo_usuario = 'superadmin'
            usuario.color_clase = 'admin'
        elif 'administrador' in grupos_usuario or 'administradores' in grupos_usuario:
            usuario.tipo_usuario = 'admin'
            usuario.color_clase = 'admin'
        elif 'vendedor' in grupos_usuario or 'vendedores' in grupos_usuario:
            usuario.tipo_usuario = 'vendedor'
            usuario.color_clase = 'vendedor'
        elif 'cliente' in grupos_usuario or 'clientes' in grupos_usuario:
            usuario.tipo_usuario = 'cliente'
            usuario.color_clase = 'cliente'
        else:
            usuario.tipo_usuario = 'usuario'
            usuario.color_clase = 'usuario'
        
        usuarios_procesados.append(usuario)
    
    paginator = Paginator(usuarios_procesados, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_usuarios = User.objects.count()
    usuarios_activos = User.objects.filter(is_active=True).count()
    administradores = User.objects.filter(
        Q(is_superuser=True) | 
        Q(groups__name__iexact='administrador') | 
        Q(groups__name__iexact='administradores')
    ).distinct().count()
    vendedores = User.objects.filter(
        Q(groups__name__iexact='vendedor') | 
        Q(groups__name__iexact='vendedores')
    ).count()
    
    # Obtener grupos disponibles
    grupos = Group.objects.all()
    
    context = {
        'usuarios': page_obj,
        'query': query,
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'administradores': administradores,
        'vendedores': vendedores,
        'grupos': grupos,
    }
    return render(request, 'custom_admin/usuarios/list.html', context)

# ============= APIs DE USUARIOS =============
@login_required
@user_passes_test(is_admin)
def usuario_detail_api(request, pk):
    """API para obtener detalle de usuario"""
    try:
        usuario = User.objects.get(pk=pk)
        data = {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'is_active': usuario.is_active,
            'is_staff': usuario.is_staff,
            'is_superuser': usuario.is_superuser,
            'date_joined': usuario.date_joined.strftime('%d/%m/%Y'),
            'last_login': usuario.last_login.strftime('%d/%m/%Y %H:%M') if usuario.last_login else None,
            'groups': list(usuario.groups.values_list('id', flat=True)),
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)

@login_required
@user_passes_test(is_admin)
@require_POST
def usuario_create_api(request):
    """API para crear usuario"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not username or not email:
            return JsonResponse({
                'success': False,
                'error': 'Usuario y email son obligatorios'
            })
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'error': 'El nombre de usuario ya existe'
            })
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'El email ya está registrado'
            })
        
        # Crear usuario
        usuario = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
        )
        
        usuario.is_active = data.get('is_active', True)
        usuario.is_staff = data.get('is_staff', False)
        usuario.is_superuser = data.get('is_superuser', False)
        
        # ✅ DETERMINAR Y ESTABLECER EL ROL
        group_id = data.get('group_id')
        grupo = None
        
        # Si es superusuario, es admin
        if usuario.is_superuser:
            usuario.rol = 'admin'
        # Si tiene grupo asignado
        elif group_id:
            try:
                grupo = Group.objects.get(pk=group_id)
                usuario.groups.add(grupo)
                
                # Mapear grupo a rol
                grupo_nombre = grupo.name.lower()
                if 'vendedor' in grupo_nombre:
                    usuario.rol = 'vendedor'
                elif 'admin' in grupo_nombre or 'administrador' in grupo_nombre:
                    usuario.rol = 'admin'
                else:
                    usuario.rol = 'cliente'
            except Group.DoesNotExist:
                usuario.rol = 'cliente'
        # Si no tiene grupo ni es superuser
        else:
            usuario.rol = 'cliente'
        
        usuario.save()
        
        # REGISTRAR EN LOGENTRY
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(usuario).pk,
            object_id=usuario.pk,
            object_repr=str(usuario),
            action_flag=ADDITION,
            change_message=f'Creado con rol: {usuario.get_rol_display()} ({grupo.name if grupo else "Sin grupo"})'
        )
        
        messages.success(request, f'Usuario {usuario.username} creado exitosamente con rol {usuario.get_rol_display()}')
        
        return JsonResponse({
            'success': True,
            'id': usuario.id,
            'message': 'Usuario creado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT"])
def usuario_update_api(request, pk):
    """API para actualizar usuario"""
    try:
        usuario = get_object_or_404(User, pk=pk)
        data = json.loads(request.body)
        
        # Guardar cambios para el log
        cambios = []
        if data['username'] != usuario.username:
            cambios.append(f"Username: {usuario.username} → {data['username']}")
        if data.get('email') != usuario.email:
            cambios.append(f"Email: {usuario.email} → {data.get('email')}")
        if data.get('is_active') != usuario.is_active:
            cambios.append(f"Activo: {usuario.is_active} → {data.get('is_active')}")
        
        # Validar username único si cambió
        if data['username'] != usuario.username:
            if User.objects.filter(username=data['username']).exists():
                return JsonResponse({'success': False, 'error': 'El nombre de usuario ya existe'})
        
        # Validar email único si cambió
        if data.get('email') and data['email'] != usuario.email:
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({'success': False, 'error': 'El email ya está registrado'})
        
        # Actualizar campos básicos
        usuario.username = data['username']
        usuario.email = data.get('email', '')
        usuario.first_name = data.get('first_name', '')
        usuario.last_name = data.get('last_name', '')
        usuario.is_active = data.get('is_active', True)
        usuario.is_staff = data.get('is_staff', False)
        usuario.is_superuser = data.get('is_superuser', False)
        
        # ✅ DETERMINAR Y ACTUALIZAR EL ROL
        rol_anterior = usuario.get_rol_display()
        
        # Limpiar grupos
        usuario.groups.clear()
        
        # Si es superusuario, es admin
        if usuario.is_superuser:
            usuario.rol = 'admin'
            cambios.append(f"Rol: {rol_anterior} → Administrador (Superusuario)")
        # Si tiene grupo asignado
        elif data.get('group_id'):
            try:
                grupo = Group.objects.get(pk=data['group_id'])
                usuario.groups.add(grupo)
                
                # Mapear grupo a rol
                grupo_nombre = grupo.name.lower()
                if 'vendedor' in grupo_nombre:
                    nuevo_rol = 'vendedor'
                elif 'admin' in grupo_nombre or 'administrador' in grupo_nombre:
                    nuevo_rol = 'admin'
                else:
                    nuevo_rol = 'cliente'
                
                if usuario.rol != nuevo_rol:
                    cambios.append(f"Rol: {rol_anterior} → {dict(usuario.ROLE_CHOICES).get(nuevo_rol)}")
                    usuario.rol = nuevo_rol
                    
            except Group.DoesNotExist:
                usuario.rol = 'cliente'
        # Sin grupo ni superuser
        else:
            if usuario.rol != 'cliente':
                cambios.append(f"Rol: {rol_anterior} → Cliente")
                usuario.rol = 'cliente'
        
        usuario.save()
        
        # REGISTRAR MODIFICACIÓN EN LOGENTRY
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(usuario).pk,
            object_id=usuario.pk,
            object_repr=str(usuario),
            action_flag=CHANGE,
            change_message=f'Modificado: {", ".join(cambios) if cambios else "Datos actualizados"}'
        )
        
        messages.success(request, f'Usuario {usuario.username} actualizado exitosamente')
        return JsonResponse({'success': True})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def usuario_delete_api(request, pk):
    """API para eliminar usuario"""
    try:
        usuario = get_object_or_404(User, pk=pk)
        
        # No permitir eliminar al propio usuario
        if usuario == request.user:
            return JsonResponse({'success': False, 'error': 'No puedes eliminar tu propio usuario'})
        
        username = usuario.username
        user_id = usuario.pk
        
        # REGISTRAR ELIMINACIÓN EN LOGENTRY ANTES DE BORRAR
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(usuario).pk,
            object_id=user_id,
            object_repr=username,
            action_flag=DELETION,
            change_message=f'Eliminado usuario: {username}'
        )
        
        usuario.delete()
        
        messages.success(request, f'Usuario {username} eliminado exitosamente')
        return JsonResponse({'success': True, 'message': 'Usuario eliminado exitosamente'})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def usuario_change_password_api(request, pk):
    """API para cambiar contraseña"""
    try:
        data = json.loads(request.body)
        usuario = User.objects.get(pk=pk)
        
        # Validar longitud mínima de contraseña
        if len(data['password']) < 8:
            return JsonResponse({'success': False, 'error': 'La contraseña debe tener al menos 8 caracteres'})
        
        usuario.set_password(data['password'])
        usuario.save()
        
        # REGISTRAR CAMBIO DE CONTRASEÑA EN LOGENTRY
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(usuario).pk,
            object_id=usuario.pk,
            object_repr=str(usuario),
            action_flag=CHANGE,
            change_message='Contraseña actualizada'
        )
        
        messages.success(request, f'Contraseña actualizada para {usuario.username}')
        return JsonResponse({'success': True})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ============= VISTAS DE GRUPOS =============
@login_required
@user_passes_test(is_admin)
def grupos_list(request):
    """Lista de grupos/roles del sistema"""
    grupos = Group.objects.all().annotate(
        usuarios_count=Count('user')
    )
    
    # Estadísticas
    total_grupos = grupos.count()
    total_permisos = Permission.objects.count()
    
    context = {
        'grupos': grupos,
        'total_grupos': total_grupos,
        'total_permisos': total_permisos,
    }
    return render(request, 'custom_admin/grupos/list.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def grupo_create_api(request):
    """API para crear grupo"""
    try:
        data = json.loads(request.body)
        
        # Validar que el nombre no exista
        if Group.objects.filter(name=data.get('name')).exists():
            return JsonResponse({
                'success': False,
                'error': 'Ya existe un grupo con ese nombre'
            })
        
        grupo = Group.objects.create(
            name=data.get('name')
        )
        
        # Asignar permisos si se enviaron
        permisos_ids = data.get('permissions', [])
        if permisos_ids:
            permisos = Permission.objects.filter(id__in=permisos_ids)
            grupo.permissions.set(permisos)
        
        # REGISTRAR EN LOGENTRY
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(grupo).pk,
            object_id=grupo.pk,
            object_repr=str(grupo),
            action_flag=ADDITION,
            change_message=f'Grupo creado: {grupo.name}'
        )
        
        return JsonResponse({
            'success': True,
            'id': grupo.id,
            'message': 'Grupo creado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def grupo_update_api(request, pk):
    """API para actualizar grupo"""
    try:
        grupo = get_object_or_404(Group, pk=pk)
        
        if request.method == 'GET':
            # Obtener información del grupo
            return JsonResponse({
                'success': True,
                'data': {
                    'id': grupo.id,
                    'name': grupo.name,
                    'permissions': list(grupo.permissions.values_list('id', flat=True)),
                    'usuarios_count': grupo.user_set.count()
                }
            })
        
        elif request.method == 'PUT':
            data = json.loads(request.body)
            nombre_anterior = grupo.name
            
            # Verificar si el nuevo nombre ya existe (excepto el actual)
            nuevo_nombre = data.get('name')
            if nuevo_nombre != grupo.name and Group.objects.filter(name=nuevo_nombre).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe otro grupo con ese nombre'
                })
            
            grupo.name = nuevo_nombre
            grupo.save()
            
            # Actualizar permisos
            permisos_ids = data.get('permissions', [])
            if permisos_ids is not None:
                permisos = Permission.objects.filter(id__in=permisos_ids)
                grupo.permissions.set(permisos)
            
            # REGISTRAR EN LOGENTRY
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(grupo).pk,
                object_id=grupo.pk,
                object_repr=str(grupo),
                action_flag=CHANGE,
                change_message=f'Modificado: {nombre_anterior} → {nuevo_nombre}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Grupo actualizado exitosamente'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
@require_POST
def grupo_delete_api(request, pk):
    """API para eliminar grupo"""
    try:
        grupo = get_object_or_404(Group, pk=pk)
        nombre = grupo.name
        grupo_id = grupo.pk
        
        # Verificar si hay usuarios en el grupo
        if grupo.user_set.exists():
            return JsonResponse({
                'success': False,
                'error': f'No se puede eliminar el grupo porque tiene {grupo.user_set.count()} usuario(s) asignado(s)'
            })
        
        # REGISTRAR EN LOGENTRY ANTES DE ELIMINAR
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(grupo).pk,
            object_id=grupo_id,
            object_repr=nombre,
            action_flag=DELETION,
            change_message=f'Grupo eliminado: {nombre}'
        )
        
        grupo.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Grupo eliminado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@user_passes_test(is_admin)
def grupo_usuarios_api(request, pk):
    """API para obtener usuarios de un grupo"""
    try:
        grupo = get_object_or_404(Group, pk=pk)
        usuarios = grupo.user_set.all().values(
            'id', 'username', 'email', 'first_name', 'last_name', 'is_active'
        )
        
        return JsonResponse({
            'success': True,
            'grupo': grupo.name,
            'usuarios': list(usuarios)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ============= VISTAS DE HISTORIAL =============
@login_required
@user_passes_test(is_admin)
def historial_list(request):
    """Lista del historial de actividades usando LogEntry de Django"""
    
    # Filtros
    usuario_id = request.GET.get('usuario')
    accion = request.GET.get('accion')
    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')
    
    # Obtener todas las entradas del log
    actividades = LogEntry.objects.all().select_related('user', 'content_type')
    
    if usuario_id:
        actividades = actividades.filter(user_id=usuario_id)
    if accion:
        actividades = actividades.filter(action_flag=accion)
    if fecha_desde:
        actividades = actividades.filter(action_time__gte=fecha_desde)
    if fecha_hasta:
        actividades = actividades.filter(action_time__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(actividades, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_actividades = LogEntry.objects.count()
    actividades_hoy = LogEntry.objects.filter(
        action_time__date=timezone.now().date()
    ).count()
    
    # Usuarios más activos
    usuarios_activos = LogEntry.objects.values(
        'user__username', 'user__first_name', 'user__last_name'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Modelos más modificados
    modelos_frecuentes = LogEntry.objects.values(
        'content_type__model'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Acciones para el filtro
    acciones = [
        (ADDITION, 'Creación'),
        (CHANGE, 'Modificación'),
        (DELETION, 'Eliminación'),
    ]
    
    context = {
        'actividades': page_obj,
        'total_actividades': total_actividades,
        'actividades_hoy': actividades_hoy,
        'usuarios_activos': usuarios_activos,
        'modelos_frecuentes': modelos_frecuentes,
        'usuarios': User.objects.filter(is_staff=True),
        'acciones': acciones,
        'filtros': {
            'usuario': usuario_id,
            'accion': accion,
            'desde': fecha_desde,
            'hasta': fecha_hasta,
        }
    }
    
    return render(request, 'custom_admin/historial/list.html', context)

# ============= VISTAS DE CUÑAS =============
@login_required
@user_passes_test(is_admin)
def cunas_list(request):
    """Lista de cuñas publicitarias"""
    if not CONTENT_MODELS_AVAILABLE:
        context = {'mensaje': 'Módulo de Cuñas no disponible'}
        return render(request, 'custom_admin/en_desarrollo.html', context)
    
    query = request.GET.get('q')
    estado = request.GET.get('estado')
    cliente_id = request.GET.get('cliente')
    
    # ✅ CORREGIDO: vendedor_asignado en lugar de vendedor
    cunas = CuñaPublicitaria.objects.all().select_related('cliente', 'vendedor_asignado', 'categoria', 'tipo_contrato').order_by('-created_at')
    
    if query:
        cunas = cunas.filter(
            Q(titulo__icontains=query) |
            Q(codigo__icontains=query)
        )
    
    if estado:
        cunas = cunas.filter(estado=estado)
        
    if cliente_id:
        cunas = cunas.filter(cliente_id=cliente_id)
    
    # Estadísticas
    cunas_activas = CuñaPublicitaria.objects.filter(estado='activa').count()
    cunas_por_vencer = CuñaPublicitaria.objects.filter(
        fecha_fin__lte=timezone.now().date() + timedelta(days=7),
        estado='activa'
    ).count()
    valor_total = cunas.aggregate(Sum('precio_total'))['precio_total__sum'] or 0
    
    paginator = Paginator(cunas, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener clientes usando CustomUser con rol='cliente'
    clientes = CustomUser.objects.filter(
        rol='cliente',
        is_active=True
    ).order_by('empresa', 'username')
    
    # Obtener vendedores usando CustomUser con rol='vendedor'
    vendedores = CustomUser.objects.filter(
        rol='vendedor',
        is_active=True
    ).order_by('first_name', 'last_name')
    
    # ✅ CORREGIDO: Usar CategoriaPublicitaria (nombre correcto del modelo)
    categorias = []
    if CONTENT_MODELS_AVAILABLE:
        try:
            from apps.content_management.models import CategoriaPublicitaria
            categorias = CategoriaPublicitaria.objects.filter(is_active=True)
        except:
            categorias = []
    
    # Obtener tipos de contrato
    tipos_contrato = []
    if CONTENT_MODELS_AVAILABLE:
        try:
            tipos_contrato = TipoContrato.objects.all()
        except:
            tipos_contrato = []
    
    context = {
        'cunas': page_obj,
        'query': query,
        'estados': CuñaPublicitaria.ESTADO_CHOICES if hasattr(CuñaPublicitaria, 'ESTADO_CHOICES') else [
            ('borrador', 'Borrador'),
            ('activa', 'Activa'),
            ('pausada', 'Pausada'),
            ('finalizada', 'Finalizada'),
            ('cancelada', 'Cancelada'),
        ],
        'estado_seleccionado': estado,
        'cunas_activas': cunas_activas,
        'cunas_por_vencer': cunas_por_vencer,
        'valor_total': valor_total,
        'clientes': clientes,
        'vendedores': vendedores,
        'categorias': categorias,
        'tipos_contrato': tipos_contrato,
    }
    return render(request, 'custom_admin/cunas/list.html', context)

# ============= APIs DE CUÑAS =============
@login_required
@user_passes_test(is_admin)
def cunas_detail_api(request, cuna_id):
    """API para obtener detalles de una cuña"""
    from apps.content_management.models import CuñaPublicitaria
    
    try:
        # ✅ CORREGIDO: vendedor_asignado en lugar de vendedor
        cuna = CuñaPublicitaria.objects.select_related(
            'cliente', 'vendedor_asignado', 'categoria', 'tipo_contrato'
        ).get(pk=cuna_id)
        
        data = {
            'id': cuna.id,
            'codigo': cuna.codigo,
            'titulo': cuna.titulo,
            'descripcion': cuna.descripcion or '',
            'cliente_id': cuna.cliente.id if cuna.cliente else None,
            'cliente_nombre': cuna.cliente.empresa or cuna.cliente.get_full_name() if cuna.cliente else None,
            # ✅ CORREGIDO: vendedor_asignado en lugar de vendedor
            'vendedor_id': cuna.vendedor_asignado.id if cuna.vendedor_asignado else None,
            'vendedor_nombre': cuna.vendedor_asignado.get_full_name() if cuna.vendedor_asignado else None,
            'categoria_id': cuna.categoria.id if cuna.categoria else None,
            'duracion_planeada': cuna.duracion_planeada,
            'repeticiones_dia': cuna.repeticiones_dia,
            'fecha_inicio': cuna.fecha_inicio.strftime('%Y-%m-%d') if cuna.fecha_inicio else None,
            'fecha_fin': cuna.fecha_fin.strftime('%Y-%m-%d') if cuna.fecha_fin else None,
            'precio_por_segundo': float(cuna.precio_por_segundo),
            'precio_total': float(cuna.precio_total),
            'excluir_sabados': cuna.excluir_sabados,
            'excluir_domingos': cuna.excluir_domingos,
            'tipo_contrato_id': cuna.tipo_contrato.id if cuna.tipo_contrato else None,
            'estado': cuna.estado,
            'observaciones': cuna.observaciones or ''
        }
        
        return JsonResponse(data)
    
    except CuñaPublicitaria.DoesNotExist:
        return JsonResponse({'error': 'Cuña no encontrada'}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def cunas_create_api(request):
    """API para crear una nueva cuña publicitaria"""
    from apps.content_management.models import CuñaPublicitaria
    from decimal import Decimal
    from datetime import datetime
    
    try:
        data = json.loads(request.body)
        
        # Validar cliente
        if not data.get('cliente_id'):
            return JsonResponse({'success': False, 'error': 'Cliente es obligatorio'}, status=400)
        
        try:
            cliente = CustomUser.objects.get(pk=data['cliente_id'], rol='cliente')
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
        
        # Convertir valores a tipos correctos
        try:
            duracion_planeada = int(data.get('duracion_planeada', 30))
            repeticiones_dia = int(data.get('repeticiones_dia', 1))
            precio_por_segundo = float(data.get('precio_por_segundo', 0))
            precio_total = float(data.get('precio_total', 0))
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error en los valores numéricos: {str(e)}'
            }, status=400)
        
        # ✅ CRÍTICO: Convertir fechas de string a objetos date
        fecha_inicio = None
        fecha_fin = None
        
        if data.get('fecha_inicio'):
            try:
                fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Formato de fecha de inicio inválido'}, status=400)
        
        if data.get('fecha_fin'):
            try:
                fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Formato de fecha de fin inválido'}, status=400)
        
        # Crear la cuña
        cuna = CuñaPublicitaria.objects.create(
            titulo=data.get('titulo'),
            descripcion=data.get('descripcion', ''),
            cliente=cliente,
            duracion_planeada=duracion_planeada,
            repeticiones_dia=repeticiones_dia,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            precio_por_segundo=Decimal(str(precio_por_segundo)),
            precio_total=Decimal(str(precio_total)),
            excluir_sabados=data.get('excluir_sabados', False),
            excluir_domingos=data.get('excluir_domingos', False),
            estado=data.get('estado', 'borrador'),
            observaciones=data.get('observaciones', '')
        )
        
        # Asignar vendedor si se proporciona
        if data.get('vendedor_id'):
            try:
                vendedor = CustomUser.objects.get(pk=data['vendedor_id'], rol='vendedor')
                cuna.vendedor_asignado = vendedor
            except CustomUser.DoesNotExist:
                pass
        
        # Asignar categoría si se proporciona
        if data.get('categoria_id'):
            from apps.content_management.models import CategoriaPublicitaria
            try:
                categoria = CategoriaPublicitaria.objects.get(pk=data['categoria_id'])
                cuna.categoria = categoria
            except CategoriaPublicitaria.DoesNotExist:
                pass
        
        # Asignar tipo de contrato si se proporciona
        if data.get('tipo_contrato_id'):
            from apps.content_management.models import TipoContrato
            try:
                tipo_contrato = TipoContrato.objects.get(pk=data['tipo_contrato_id'])
                cuna.tipo_contrato = tipo_contrato
            except TipoContrato.DoesNotExist:
                pass
        
        cuna.save()
        
        # Registrar en historial
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.contenttypes.models import ContentType
        
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(cuna).pk,
            object_id=cuna.pk,
            object_repr=str(cuna.titulo),
            action_flag=ADDITION,
            change_message=f'Cuña creada: {cuna.titulo} - Cliente: {cliente.empresa or cliente.username}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Cuña creada exitosamente',
            'cuna_id': cuna.id
        })
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT"])
def cunas_update_api(request, cuna_id):
    """API para actualizar una cuña publicitaria - VERSIÓN COMPLETA CON SEMÁFORO"""
    from apps.content_management.models import CuñaPublicitaria
    from decimal import Decimal
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # ✅ 1. OBTENER LA CUÑA
        cuna = CuñaPublicitaria.objects.get(pk=cuna_id)
        data = json.loads(request.body)
        
        print(f"🔄 Actualizando cuña {cuna_id}: {cuna.titulo}")
        print(f"📊 Datos recibidos: {data}")
        
        # ✅ 2. CAPTURAR ESTADO ANTERIOR PARA EL SEMÁFORO
        estado_anterior = cuna.estado
        fecha_inicio_anterior = cuna.fecha_inicio
        fecha_fin_anterior = cuna.fecha_fin
        
        # ✅ 3. DESACTIVAR TODAS LAS SEÑALES TEMPORALMENTE
        from django.db import transaction
        from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
        
        # Guardar receivers originales
        original_receivers = {}
        signals_to_disconnect = [pre_save, post_save, pre_delete, post_delete]
        
        for signal in signals_to_disconnect:
            original_receivers[signal] = signal.receivers
            signal.receivers = []
        
        # ✅ 4. ACTUALIZAR CAMPOS EN UNA TRANSACCIÓN ATOMIC
        try:
            with transaction.atomic():
                # Campos básicos
                if 'titulo' in data:
                    cuna.titulo = data['titulo']
                
                if 'descripcion' in data:
                    cuna.descripcion = data['descripcion']
                
                if 'estado' in data:
                    estado_anterior = cuna.estado
                    cuna.estado = data['estado']
                    print(f"🔄 Cambio de estado: {estado_anterior} → {cuna.estado}")
                
                if 'observaciones' in data:
                    cuna.observaciones = data['observaciones']
                
                if 'excluir_sabados' in data:
                    cuna.excluir_sabados = data['excluir_sabados']
                
                if 'excluir_domingos' in data:
                    cuna.excluir_domingos = data['excluir_domingos']
                
                # Fechas
                if 'fecha_inicio' in data and data['fecha_inicio']:
                    try:
                        cuna.fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
                        print(f"📅 Nueva fecha inicio: {cuna.fecha_inicio}")
                    except ValueError as e:
                        print(f"⚠️ Error en fecha inicio: {e}")
                
                if 'fecha_fin' in data and data['fecha_fin']:
                    try:
                        cuna.fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
                        print(f"📅 Nueva fecha fin: {cuna.fecha_fin}")
                    except ValueError as e:
                        print(f"⚠️ Error en fecha fin: {e}")
                
                # Campos numéricos
                if 'duracion_planeada' in data:
                    cuna.duracion_planeada = int(data['duracion_planeada'])
                
                if 'repeticiones_dia' in data:
                    cuna.repeticiones_dia = int(data['repeticiones_dia'])
                
                if 'precio_por_segundo' in data:
                    cuna.precio_por_segundo = Decimal(str(float(data['precio_por_segundo'])))
                
                if 'precio_total' in data:
                    cuna.precio_total = Decimal(str(float(data['precio_total'])))
                
                # Relaciones
                if data.get('cliente_id'):
                    try:
                        cliente = CustomUser.objects.get(pk=data['cliente_id'], rol='cliente')
                        cuna.cliente = cliente
                    except CustomUser.DoesNotExist:
                        pass
                
                if 'vendedor_id' in data:
                    if data['vendedor_id']:
                        try:
                            vendedor = CustomUser.objects.get(pk=data['vendedor_id'], rol='vendedor')
                            cuna.vendedor_asignado = vendedor
                        except CustomUser.DoesNotExist:
                            cuna.vendedor_asignado = None
                    else:
                        cuna.vendedor_asignado = None
                
                if 'categoria_id' in data:
                    if data['categoria_id']:
                        try:
                            from apps.content_management.models import CategoriaPublicitaria
                            categoria = CategoriaPublicitaria.objects.get(pk=data['categoria_id'])
                            cuna.categoria = categoria
                        except CategoriaPublicitaria.DoesNotExist:
                            cuna.categoria = None
                    else:
                        cuna.categoria = None
                
                if 'tipo_contrato_id' in data:
                    if data['tipo_contrato_id']:
                        try:
                            from apps.content_management.models import TipoContrato
                            tipo_contrato = TipoContrato.objects.get(pk=data['tipo_contrato_id'])
                            cuna.tipo_contrato = tipo_contrato
                        except TipoContrato.DoesNotExist:
                            cuna.tipo_contrato = None
                    else:
                        cuna.tipo_contrato = None
                
                # ✅ 5. GUARDAR DIRECTAMENTE SIN SEÑALES
                cuna.save()
                print(f"✅ Cuña {cuna_id} guardada exitosamente. Estado: {cuna.estado}")
                
        except Exception as e:
            print(f"❌ Error en transacción: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error al guardar la cuña: {str(e)}'
            }, status=500)
        
        finally:
            # ✅ 6. RESTAURAR SEÑALES (aunque falle)
            try:
                for signal, receivers in original_receivers.items():
                    signal.receivers = receivers
            except Exception as e:
                print(f"⚠️ Error restaurando señales: {e}")
        
        # ✅ 7. ACTUALIZAR SEMÁFORO INMEDIATAMENTE DESPUÉS DE GUARDAR
        estado_semaforo_actualizado = None
        try:
            from apps.traffic_light_system.utils.status_calculator import StatusCalculator
            
            calculator = StatusCalculator()
            estado_semaforo_actualizado = calculator.actualizar_estado_cuña(cuna, crear_historial=True)
            
            print(f"✅ Semáforo actualizado: {estado_semaforo_actualizado.color_actual} - {estado_semaforo_actualizado.razon_color}")
            
        except Exception as e:
            print(f"⚠️ Error actualizando semáforo: {e}")
            # No fallar la operación principal por error en semáforo
        
        # ✅ 8. VERIFICAR QUE REALMENTE SE GUARDÓ
        try:
            cuna_refreshed = CuñaPublicitaria.objects.get(pk=cuna_id)
            estado_final = cuna_refreshed.estado
            print(f"✅ Verificación: Cuña {cuna_id} tiene estado {estado_final}")
        except Exception as e:
            print(f"⚠️ Error verificando estado final: {e}")
            estado_final = "desconocido"
        
        # ✅ 9. REGISTRAR EN HISTORIAL
        try:
            from django.contrib.admin.models import LogEntry, CHANGE
            from django.contrib.contenttypes.models import ContentType
            
            cambios = []
            if 'estado' in data and estado_anterior != data['estado']:
                cambios.append(f"Estado: {estado_anterior} → {data['estado']}")
            if 'fecha_inicio' in data and fecha_inicio_anterior != cuna.fecha_inicio:
                cambios.append("Fecha inicio modificada")
            if 'fecha_fin' in data and fecha_fin_anterior != cuna.fecha_fin:
                cambios.append("Fecha fin modificada")
            
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(cuna).pk,
                object_id=cuna.pk,
                object_repr=f"Cuña {cuna.codigo}",
                action_flag=CHANGE,
                change_message=f'Cuña actualizada: {", ".join(cambios) if cambios else "Datos modificados"} | Semáforo: {estado_semaforo_actualizado.color_actual if estado_semaforo_actualizado else "No actualizado"}'
            )
            
        except Exception as e:
            print(f"⚠️ Error registrando en historial: {e}")
        
        # ✅ 10. RESPUESTA EXITOSA
        return JsonResponse({
            'success': True,
            'message': f'Cuña actualizada exitosamente a estado: {estado_final}',
            'estado_actual': estado_final,
            'semaforo_actualizado': estado_semaforo_actualizado.color_actual if estado_semaforo_actualizado else None,
            'razon_semaforo': estado_semaforo_actualizado.razon_color if estado_semaforo_actualizado else 'No se pudo actualizar',
            'cuna_id': cuna_id,
            'cambios_realizados': {
                'estado_cambiado': 'estado' in data and estado_anterior != data['estado'],
                'fechas_cambiadas': any(key in data for key in ['fecha_inicio', 'fecha_fin'])
            }
        })
    
    except CuñaPublicitaria.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cuña no encontrada'}, status=404)
    except Exception as e:
        import traceback
        print(f"❌ ERROR CRÍTICO en cunas_update_api:")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error crítico: {str(e)}'
        }, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def cunas_delete_api(request, cuna_id):
    """API para eliminar una cuña publicitaria"""
    from apps.content_management.models import CuñaPublicitaria
    
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        cuna = CuñaPublicitaria.objects.get(pk=cuna_id)
        titulo = cuna.titulo
        
        # Registrar en historial antes de eliminar
        from django.contrib.admin.models import LogEntry, DELETION
        from django.contrib.contenttypes.models import ContentType
        
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(cuna).pk,
            object_id=cuna.pk,
            object_repr=str(titulo),
            action_flag=DELETION,
            change_message=f'Cuña eliminada: {titulo}'
        )
        
        cuna.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Cuña eliminada exitosamente'
        })
    
    except CuñaPublicitaria.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cuña no encontrada'}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Vistas de compatibilidad
@login_required
@user_passes_test(is_admin)
def cuna_create(request):
    return redirect('custom_admin:cunas_list')

@login_required
@user_passes_test(is_admin)
def cuna_edit(request, pk):
    return redirect('custom_admin:cunas_list')

@login_required
@user_passes_test(is_admin)
def cuna_detail(request, pk):
    return redirect('custom_admin:cunas_list')

@login_required
@user_passes_test(is_admin)
def cuna_delete(request, pk):
    return redirect('custom_admin:cunas_list')

# ==============================================================================
# VISTAS DE CATEGORÍAS
# ==============================================================================

@login_required
@user_passes_test(is_admin)
def categorias_list(request):
    """Lista de categorías publicitarias"""
    if not CONTENT_MODELS_AVAILABLE:
        context = {'mensaje': 'Módulo no disponible'}
        return render(request, 'custom_admin/en_desarrollo.html', context)
    
    categorias = CategoriaPublicitaria.objects.all().order_by('nombre')
    
    context = {
        'categorias': categorias,
    }
    return render(request, 'custom_admin/categorias/list.html', context)

@login_required
def categoria_detail_api(request, categoria_id):
    """API para obtener detalles de una categoría"""
    from apps.content_management.models import CategoriaPublicitaria
    
    try:
        categoria = CategoriaPublicitaria.objects.get(pk=categoria_id)
        
        data = {
            'id': categoria.id,
            'nombre': categoria.nombre,
            'descripcion': categoria.descripcion,
            'color_codigo': categoria.color_codigo,
            'tarifa_base': float(categoria.tarifa_base),  # Tarifa por segundo
        }
        
        return JsonResponse(data)
    
    except CategoriaPublicitaria.DoesNotExist:
        return JsonResponse({'error': 'Categoría no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def categoria_create_api(request):
    """API para crear categoría"""
    if not CONTENT_MODELS_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'Módulo no disponible'}, status=503)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            categoria = CategoriaPublicitaria.objects.create(
                nombre=data['nombre'],
                descripcion=data.get('descripcion', ''),
                color_codigo=data.get('color_codigo', '#007bff'),
                tarifa_base=Decimal(data.get('tarifa_base', '0.00'))
            )
            
            # REGISTRAR EN LOGENTRY
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(categoria).pk,
                object_id=categoria.pk,
                object_repr=str(categoria),
                action_flag=ADDITION,
                change_message=f'Categoría creada: {categoria.nombre}'
            )
            
            return JsonResponse({
                'success': True,
                'categoria': {
                    'id': categoria.id,
                    'nombre': categoria.nombre,
                    'tarifa_base': str(categoria.tarifa_base)
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
@user_passes_test(is_admin)
def categoria_update_api(request, pk):
    """API para actualizar categoría"""
    if not CONTENT_MODELS_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'Módulo no disponible'}, status=503)
    
    if request.method == 'PUT':
        try:
            categoria = get_object_or_404(CategoriaPublicitaria, pk=pk)
            data = json.loads(request.body)
            
            nombre_anterior = categoria.nombre
            
            categoria.nombre = data.get('nombre', categoria.nombre)
            categoria.descripcion = data.get('descripcion', categoria.descripcion)
            categoria.color_codigo = data.get('color_codigo', categoria.color_codigo)
            categoria.tarifa_base = Decimal(data.get('tarifa_base', str(categoria.tarifa_base)))
            categoria.save()
            
            # REGISTRAR EN LOGENTRY
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(categoria).pk,
                object_id=categoria.pk,
                object_repr=str(categoria),
                action_flag=CHANGE,
                change_message=f'Modificado: {nombre_anterior} → {categoria.nombre}'
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
@user_passes_test(is_admin)
def categoria_delete_api(request, pk):
    """API para eliminar categoría"""
    if not CONTENT_MODELS_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'Módulo no disponible'}, status=503)
    
    if request.method == 'DELETE':
        try:
            categoria = get_object_or_404(CategoriaPublicitaria, pk=pk)
            nombre = categoria.nombre
            categoria_id = categoria.pk
            
            # REGISTRAR EN LOGENTRY ANTES DE ELIMINAR
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(categoria).pk,
                object_id=categoria_id,
                object_repr=nombre,
                action_flag=DELETION,
                change_message=f'Categoría eliminada: {nombre}'
            )
            
            categoria.delete()
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

# ============= VISTAS DE CONTRATOS =============
@login_required
@user_passes_test(is_admin)
def contrato_create_api(request):
    """API para crear contrato"""
    if not CONTENT_MODELS_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'Módulo no disponible'}, status=503)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            contrato = TipoContrato.objects.create(
                nombre=data['nombre'],
                descripcion=data.get('descripcion', ''),
                duracion_tipo=data.get('duracion_tipo', 'mensual'),
                duracion_dias=int(data.get('duracion_dias', 30)),
                repeticiones_minimas=int(data.get('repeticiones_minimas', 1)),
                descuento_porcentaje=Decimal(data.get('descuento_porcentaje', '0.00'))
            )
            
            # REGISTRAR EN LOGENTRY
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(contrato).pk,
                object_id=contrato.pk,
                object_repr=str(contrato),
                action_flag=ADDITION,
                change_message=f'Contrato creado: {contrato.nombre}'
            )
            
            return JsonResponse({'success': True, 'id': contrato.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
@user_passes_test(is_admin)
def contrato_detail_api(request, pk):
    """API para obtener detalle de contrato"""
    if not CONTENT_MODELS_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'Módulo no disponible'}, status=503)
    
    try:
        contrato = get_object_or_404(TipoContrato, pk=pk)
        return JsonResponse({
            'id': contrato.id,
            'nombre': contrato.nombre,
            'descripcion': contrato.descripcion,
            'duracion_tipo': contrato.duracion_tipo,
            'duracion_dias': contrato.duracion_dias,
            'repeticiones_minimas': contrato.repeticiones_minimas,
            'descuento_porcentaje': str(contrato.descuento_porcentaje)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=404)

@login_required
@user_passes_test(is_admin)
def contrato_update_api(request, pk):
    """API para actualizar contrato"""
    if not CONTENT_MODELS_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'Módulo no disponible'}, status=503)
    
    if request.method == 'PUT':
        try:
            contrato = get_object_or_404(TipoContrato, pk=pk)
            data = json.loads(request.body)
            
            nombre_anterior = contrato.nombre
            
            contrato.nombre = data.get('nombre', contrato.nombre)
            contrato.descripcion = data.get('descripcion', contrato.descripcion)
            contrato.save()
            
            # REGISTRAR EN LOGENTRY
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(contrato).pk,
                object_id=contrato.pk,
                object_repr=str(contrato),
                action_flag=CHANGE,
                change_message=f'Modificado: {nombre_anterior} → {contrato.nombre}'
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

# ============= VISTAS DE TRANSMISIONES =============
@login_required
@user_passes_test(is_admin)
def transmisiones_list(request):
    """Lista de transmisiones"""
    context = {'mensaje': 'Módulo de Transmisiones - En desarrollo'}
    return render(request, 'custom_admin/en_desarrollo.html', context)

@login_required
@user_passes_test(is_admin)
def programacion_list_api(request):
    """API para listar programaciones"""
    return JsonResponse({'programaciones': []})

@login_required
@user_passes_test(is_admin)
def programacion_create_api(request):
    """API para crear programación"""
    return JsonResponse({'success': False, 'error': 'No implementado'}, status=501)

# ============= VISTAS DE SEMÁFOROS =============
@login_required
@user_passes_test(is_admin)
def semaforos_list(request):
    """Lista de estados de semáforos para cuñas"""
    if not TRAFFIC_MODELS_AVAILABLE or not CONTENT_MODELS_AVAILABLE:
        context = {'mensaje': 'Módulo de Semáforos no disponible'}
        return render(request, 'custom_admin/en_desarrollo.html', context)
    
    query = request.GET.get('q')
    color = request.GET.get('color')
    prioridad = request.GET.get('prioridad')
    
    # Obtener estados de semáforo con información de cuñas
    estados_semaforo = EstadoSemaforo.objects.select_related(
        'cuña', 'cuña__cliente', 'cuña__vendedor_asignado', 'configuracion_utilizada'
    ).all().order_by('-ultimo_calculo')
    
    if query:
        estados_semaforo = estados_semaforo.filter(
            Q(cuña__titulo__icontains=query) |
            Q(cuña__codigo__icontains=query) |
            Q(cuña__cliente__empresa__icontains=query) |
            Q(cuña__cliente__first_name__icontains=query) |
            Q(cuña__cliente__last_name__icontains=query)
        )
    
    if color:
        estados_semaforo = estados_semaforo.filter(color_actual=color)
        
    if prioridad:
        estados_semaforo = estados_semaforo.filter(prioridad=prioridad)
    
    # Estadísticas
    total_semaforos = estados_semaforo.count()
    semaforos_verde = estados_semaforo.filter(color_actual='verde').count()
    semaforos_amarillo = estados_semaforo.filter(color_actual='amarillo').count()
    semaforos_rojo = estados_semaforo.filter(color_actual='rojo').count()
    semaforos_gris = estados_semaforo.filter(color_actual='gris').count()
    
    # Cuñas que requieren atención (amarillo y rojo)
    cuñas_problema = estados_semaforo.filter(
        color_actual__in=['amarillo', 'rojo']
    ).count()
    
    paginator = Paginator(estados_semaforo, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'estados_semaforo': page_obj,
        'query': query,
        'color_seleccionado': color,
        'prioridad_seleccionada': prioridad,
        'total_semaforos': total_semaforos,
        'semaforos_verde': semaforos_verde,
        'semaforos_amarillo': semaforos_amarillo,
        'semaforos_rojo': semaforos_rojo,
        'semaforos_gris': semaforos_gris,
        'cuñas_problema': cuñas_problema,
        'colores': EstadoSemaforo.COLOR_CHOICES,
        'prioridades': EstadoSemaforo.PRIORIDAD_CHOICES,
    }
    return render(request, 'custom_admin/semaforos/list.html', context)

@login_required
@user_passes_test(is_admin)
def semaforo_detail_api(request, estado_id):
    """API para obtener detalles de un estado de semáforo"""
    try:
        estado = EstadoSemaforo.objects.select_related(
            'cuña', 'cuña__cliente', 'cuña__vendedor_asignado', 
            'cuña__categoria', 'configuracion_utilizada'
        ).get(pk=estado_id)
        
        data = {
            'id': estado.id,
            'cuña': {
                'id': estado.cuña.id,
                'titulo': estado.cuña.titulo,
                'codigo': estado.cuña.codigo,
                'cliente_nombre': estado.cuña.cliente.empresa if estado.cuña.cliente else 'Sin cliente',
                'vendedor_nombre': estado.cuña.vendedor_asignado.get_full_name() if estado.cuña.vendedor_asignado else 'Sin vendedor',
                'fecha_inicio': estado.cuña.fecha_inicio.strftime('%Y-%m-%d') if estado.cuña.fecha_inicio else None,
                'fecha_fin': estado.cuña.fecha_fin.strftime('%Y-%m-%d') if estado.cuña.fecha_fin else None,
                'estado': estado.cuña.estado,
            },
            'color_actual': estado.color_actual,
            'color_anterior': estado.color_anterior,
            'prioridad': estado.prioridad,
            'dias_restantes': estado.dias_restantes,
            'porcentaje_tiempo_transcurrido': float(estado.porcentaje_tiempo_transcurrido) if estado.porcentaje_tiempo_transcurrido else None,
            'razon_color': estado.razon_color,
            'necesita_atencion': estado.necesita_atencion,
            'cambio_color': estado.cambio_color,
            'empeoro_estado': estado.empeoro_estado,
            'configuracion_utilizada': estado.configuracion_utilizada.nombre if estado.configuracion_utilizada else 'Por defecto',
            'ultimo_calculo': estado.ultimo_calculo.strftime('%d/%m/%Y %H:%M'),
        }
        
        return JsonResponse(data)
    
    except EstadoSemaforo.DoesNotExist:
        return JsonResponse({'error': 'Estado de semáforo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def semaforo_recalcular_api(request, estado_id):
    """API para recalcular un estado de semáforo"""
    try:
        estado = EstadoSemaforo.objects.get(pk=estado_id)
        
        # Aquí iría la lógica para recalcular el estado
        # Por ahora simulamos una actualización
        estado.ultimo_calculo = timezone.now()
        estado.save()
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(estado).pk,
            object_id=estado.pk,
            object_repr=f"Semáforo recalculado - {estado.cuña.codigo}",
            action_flag=CHANGE,
            change_message=f'Semáforo recalculado manualmente para {estado.cuña.titulo}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Semáforo recalculado exitosamente',
            'ultimo_calculo': estado.ultimo_calculo.strftime('%d/%m/%Y %H:%M')
        })
    
    except EstadoSemaforo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Estado de semáforo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def configuracion_semaforos(request):
    """Configuración del sistema de semáforos"""
    if not TRAFFIC_MODELS_AVAILABLE:
        context = {'mensaje': 'Módulo de Semáforos no disponible'}
        return render(request, 'custom_admin/en_desarrollo.html', context)
    
    configuraciones = ConfiguracionSemaforo.objects.all()
    configuracion_activa = ConfiguracionSemaforo.get_active()
    
    context = {
        'configuraciones': configuraciones,
        'configuracion_activa': configuracion_activa,
    }
    return render(request, 'custom_admin/semaforos/configuracion.html', context)

@login_required
@user_passes_test(is_admin)
def semaforos_estados_api(request):
    """API para estados de semáforos (para dashboard)"""
    if not TRAFFIC_MODELS_AVAILABLE:
        return JsonResponse({'estados': []})
    
    try:
        estados = EstadoSemaforo.objects.values('color_actual').annotate(
            total=Count('id')
        )
        
        data = {
            'verde': 0,
            'amarillo': 0,
            'rojo': 0,
            'gris': 0
        }
        
        for estado in estados:
            data[estado['color_actual']] = estado['total']
        
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============= VISTAS DE REPORTES =============
@login_required
@user_passes_test(is_admin)
def reportes_dashboard(request):
    """Dashboard de reportes"""
    context = {'mensaje': 'Módulo de Reportes - En desarrollo'}
    return render(request, 'custom_admin/en_desarrollo.html', context)

# ==============================================================================
# GESTIÓN DE CLIENTES
# ==============================================================================

from apps.content_management.forms import ClienteForm

@login_required
def clientes_list(request):
    """Vista principal para gestión de clientes"""
    
    # Verificar permisos
    if not request.user.es_admin and not request.user.es_vendedor:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('custom_admin:dashboard')
    
    # Si es vendedor, solo ver sus clientes
    if request.user.es_vendedor:
        clientes = CustomUser.objects.filter(
            rol='cliente',
            vendedor_asignado=request.user
        ).select_related('vendedor_asignado')
    else:
        clientes = CustomUser.objects.filter(
            rol='cliente'
        ).select_related('vendedor_asignado')
    
    # Filtros
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    vendedor_filter = request.GET.get('vendedor', '')
    
    if search:
        clientes = clientes.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(empresa__icontains=search) |
            Q(ruc_dni__icontains=search) |
            Q(email__icontains=search)
        )
    
    if status_filter:
        clientes = clientes.filter(status=status_filter)
    
    if vendedor_filter and request.user.es_admin:
        clientes = clientes.filter(vendedor_asignado_id=vendedor_filter)
    
    # Ordenar
    clientes = clientes.order_by('-created_at')
    
    # Estadísticas
    total_clientes = clientes.count()
    clientes_activos = clientes.filter(status='activo').count()
    clientes_inactivos = clientes.filter(status='inactivo').count()
    
    # Vendedores para filtro (solo admins)
    vendedores = CustomUser.objects.filter(
        rol='vendedor',
        status='activo'
    ).order_by('first_name', 'last_name') if request.user.es_admin else []
    
    context = {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'clientes_inactivos': clientes_inactivos,
        'vendedores': vendedores,
        'search': search,
        'status_filter': status_filter,
        'vendedor_filter': vendedor_filter,
    }
    
    return render(request, 'custom_admin/clientes/list.html', context)

@login_required
def cliente_detail_api(request, cliente_id):
    """API para obtener detalles de un cliente"""
    
    if not request.user.es_admin and not request.user.es_vendedor:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        cliente = CustomUser.objects.select_related('vendedor_asignado').get(
            pk=cliente_id,
            rol='cliente'
        )
        
        # Verificar permisos de vendedor
        if request.user.es_vendedor and cliente.vendedor_asignado != request.user:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = {
            'id': cliente.id,
            'username': cliente.username,
            'first_name': cliente.first_name,
            'last_name': cliente.last_name,
            'email': cliente.email,
            'telefono': cliente.telefono or '',
            'empresa': cliente.empresa or '',
            'ruc_dni': cliente.ruc_dni or '',
            'razon_social': cliente.razon_social or '',
            'giro_comercial': cliente.giro_comercial or '',
            'ciudad': cliente.ciudad or '',
            'provincia': cliente.provincia or '',
            'direccion_exacta': cliente.direccion_exacta or '',
            'vendedor_asignado_id': cliente.vendedor_asignado.id if cliente.vendedor_asignado else None,
            'vendedor_asignado_nombre': cliente.vendedor_asignado.get_full_name() if cliente.vendedor_asignado else '',
            'limite_credito': str(cliente.limite_credito) if cliente.limite_credito else '0.00',
            'dias_credito': cliente.dias_credito or 0,
            'status': cliente.status,
            'fecha_registro': cliente.fecha_registro.strftime('%d/%m/%Y %H:%M') if cliente.fecha_registro else '',
            # --- LOS DOS CAMPOS NUEVOS ---
            'cargo_empresa': cliente.cargo_empresa or '',
            'profesion': cliente.profesion or '',
        }
        
        return JsonResponse(data)
    
    except CustomUser.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def cliente_create_api(request):
    """API para crear un nuevo cliente - VERSIÓN SIN ORDEN AUTOMÁTICA"""
    if not request.user.es_admin and not request.user.es_vendedor:
        messages.error(request, 'No tienes permisos para crear clientes')
        return redirect('custom_admin:clientes_list')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('custom_admin:clientes_list')
    
    try:
        print("🟡 INICIANDO CREACIÓN DE CLIENTE...")
        
        # Validar que no exista el username
        username = request.POST.get('username')
        print(f"🟡 Username: {username}")
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f'El usuario "{username}" ya existe')
            return redirect('custom_admin:clientes_list')

        # Validar que no exista el email
        email = request.POST.get('email')
        print(f"🟡 Email: {email}")
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, f'El email "{email}" ya está registrado')
            return redirect('custom_admin:clientes_list')

        # ✅ CREAR CLIENTE
        print("🟡 Creando objeto cliente...")
        cliente = CustomUser.objects.create(
            username=username,
            email=email,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
        )

        # ✅ CONFIGURAR CAMPOS ADICIONALES
        print("🟡 Configurando campos adicionales...")
        cliente.set_unusable_password()
        cliente.rol = 'cliente'
        cliente.is_active = True

        # Campos adicionales del cliente
        cliente.telefono = request.POST.get('telefono', '')
        cliente.empresa = request.POST.get('empresa', '')
        cliente.ruc_dni = request.POST.get('ruc_dni', '')
        cliente.razon_social = request.POST.get('razon_social', '')
        cliente.giro_comercial = request.POST.get('giro_comercial', '')
        cliente.ciudad = request.POST.get('ciudad', '')
        cliente.provincia = request.POST.get('provincia', '')
        cliente.direccion_exacta = request.POST.get('direccion_exacta', '')
        cliente.cargo_empresa = request.POST.get('cargo_empresa', '')
        cliente.profesion = request.POST.get('profesion', '')

        # Manejar valores numéricos
        try:
            cliente.limite_credito = float(request.POST.get('limite_credito', 0))
        except (ValueError, TypeError):
            cliente.limite_credito = 0
            
        try:
            cliente.dias_credito = int(request.POST.get('dias_credito', 0))
        except (ValueError, TypeError):
            cliente.dias_credito = 0

        cliente.status = request.POST.get('status', 'activo')

        # Asignar vendedor
        if request.user.es_vendedor:
            cliente.vendedor_asignado = request.user
        elif request.POST.get('vendedor_asignado'):
            vendedor_id = request.POST.get('vendedor_asignado')
            if vendedor_id:
                try:
                    vendedor = CustomUser.objects.get(pk=vendedor_id, rol='vendedor')
                    cliente.vendedor_asignado = vendedor
                except CustomUser.DoesNotExist:
                    pass

        # ✅ GUARDAR EL CLIENTE SIN CREAR ORDEN
        print("🟡 Guardando cliente en BD...")
        cliente.save()
        print(f"✅ CLIENTE GUARDADO - ID: {cliente.id}")

        # ❌ ELIMINADO: Creación automática de orden de toma
        print("🟡 Cliente creado exitosamente - SIN orden automática")

        # Registrar en historial
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.contenttypes.models import ContentType
        
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(cliente).pk,
            object_id=cliente.pk,
            object_repr=str(cliente.empresa or cliente.username),
            action_flag=ADDITION,
            change_message=f'Cliente creado: {cliente.empresa} ({cliente.ruc_dni}) - Sin orden automática'
        )

        messages.success(request, f'✓ Cliente "{cliente.empresa}" creado exitosamente')
        print("✅ PROCESO COMPLETADO - Redirigiendo...")
        return redirect('custom_admin:clientes_list')
    
    except Exception as e:
        print(f"❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error al crear el cliente: {str(e)}')
        return redirect('custom_admin:clientes_list')
@login_required
def cliente_update_api(request, cliente_id):
    """API para actualizar un cliente existente"""
    if not request.user.es_admin and not request.user.es_vendedor:
        messages.error(request, 'No tienes permisos para editar clientes')
        return redirect('custom_admin:clientes_list')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('custom_admin:clientes_list')
    
    try:
        cliente = CustomUser.objects.get(pk=cliente_id, rol='cliente')
        
        # Verificar permisos de vendedor
        if request.user.es_vendedor and cliente.vendedor_asignado != request.user:
            messages.error(request, 'No tienes permisos para editar este cliente')
            return redirect('custom_admin:clientes_list')

        # Actualizar datos
        cliente.first_name = request.POST.get('first_name', cliente.first_name)
        cliente.last_name = request.POST.get('last_name', cliente.last_name)
        cliente.telefono = request.POST.get('telefono', cliente.telefono)
        cliente.empresa = request.POST.get('empresa', cliente.empresa)
        cliente.ruc_dni = request.POST.get('ruc_dni', cliente.ruc_dni)
        cliente.razon_social = request.POST.get('razon_social', cliente.razon_social)
        cliente.giro_comercial = request.POST.get('giro_comercial', cliente.giro_comercial)
        cliente.ciudad = request.POST.get('ciudad', cliente.ciudad)
        cliente.provincia = request.POST.get('provincia', cliente.provincia)
        cliente.direccion_exacta = request.POST.get('direccion_exacta', cliente.direccion_exacta)
        
        # --- LOS DOS CAMPOS NUEVOS ---
        cliente.cargo_empresa = request.POST.get('cargo_empresa', cliente.cargo_empresa)
        cliente.profesion = request.POST.get('profesion', cliente.profesion)

        try:
            cliente.limite_credito = float(request.POST.get('limite_credito', cliente.limite_credito))
        except (ValueError, TypeError):
            pass
        try:
            cliente.dias_credito = int(request.POST.get('dias_credito', cliente.dias_credito))
        except (ValueError, TypeError):
            pass

        cliente.status = request.POST.get('status', cliente.status)

        if request.user.es_admin and request.POST.get('vendedor_asignado'):
            vendedor_id = request.POST.get('vendedor_asignado')
            if vendedor_id:
                try:
                    vendedor = CustomUser.objects.get(pk=vendedor_id, rol='vendedor')
                    cliente.vendedor_asignado = vendedor
                except CustomUser.DoesNotExist:
                    pass

        cliente.save()

        # Registrar en historial con LogEntry
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.contenttypes.models import ContentType
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(cliente).pk,
            object_id=cliente.pk,
            object_repr=str(cliente.empresa or cliente.username),
            action_flag=CHANGE,
            change_message=f'Cliente actualizado: {cliente.empresa} ({cliente.ruc_dni})'
        )

        messages.success(request, f'✓ Cliente "{cliente.empresa}" actualizado exitosamente')
        return redirect('custom_admin:clientes_list')
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        messages.error(request, f'Error al actualizar el cliente: {str(e)}')
        return redirect('custom_admin:clientes_list')
@login_required
def cliente_delete_api(request, cliente_id):
    """API para eliminar/inactivar un cliente"""
    
    if not request.user.es_admin:
        messages.error(request, 'Solo administradores pueden eliminar clientes')
        return redirect('custom_admin:clientes_list')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('custom_admin:clientes_list')
    
    try:
        cliente = CustomUser.objects.get(pk=cliente_id, rol='cliente')
        empresa = cliente.empresa or cliente.username
        
        # Verificar si tiene cuñas asociadas
        if CONTENT_MODELS_AVAILABLE:
            from apps.content_management.models import CuñaPublicitaria
            tiene_cuñas = CuñaPublicitaria.objects.filter(cliente=cliente).exists()
            
            if tiene_cuñas:
                # No eliminar, solo inactivar
                cliente.status = 'inactivo'
                cliente.is_active = False
                cliente.save()
                
                mensaje = f'Cliente "{empresa}" inactivado (tiene cuñas asociadas)'
                messages.warning(request, mensaje)
            else:
                # Eliminar completamente
                cliente.delete()
                mensaje = f'Cliente "{empresa}" eliminado exitosamente'
                messages.success(request, mensaje)
        else:
            # Si no hay módulo de cuñas, eliminar directamente
            cliente.delete()
            mensaje = f'Cliente "{empresa}" eliminado exitosamente'
            messages.success(request, mensaje)
        
        # Registrar en historial con LogEntry
        from django.contrib.admin.models import LogEntry, DELETION
        from django.contrib.contenttypes.models import ContentType
        
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(cliente).pk,
            object_id=cliente_id,
            object_repr=empresa,
            action_flag=DELETION,
            change_message=mensaje
        )
        
        return redirect('custom_admin:clientes_list')
    
    except CustomUser.DoesNotExist:
        messages.error(request, 'Cliente no encontrado')
        return redirect('custom_admin:clientes_list')
    except Exception as e:
        messages.error(request, f'Error al eliminar el cliente: {str(e)}')
        return redirect('custom_admin:clientes_list')

# ============= VISTAS DE CONFIGURACIÓN =============
@login_required
@user_passes_test(is_admin)
def configuracion(request):
    """Configuración del sistema"""
    context = {'mensaje': 'Configuración del Sistema - En desarrollo'}
    return render(request, 'custom_admin/en_desarrollo.html', context)
# ==================== VISTAS COMPLETAS DE ÓRDENES ====================
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
@user_passes_test(is_admin)
def orders_list(request):
    from apps.orders.models import OrdenToma
    from apps.authentication.models import CustomUser

    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    prioridad_filter = request.GET.get('prioridad', '')

    ordenes = OrdenToma.objects.select_related('cliente', 'vendedor_asignado').all()
    
    if search:
        ordenes = ordenes.filter(
            Q(codigo__icontains=search) |
            Q(nombre_cliente__icontains=search) |
            Q(ruc_dni_cliente__icontains=search) |
            Q(empresa_cliente__icontains=search)
        )
    
    if estado_filter:
        ordenes = ordenes.filter(estado=estado_filter)
    
    if prioridad_filter:
        ordenes = ordenes.filter(prioridad=prioridad_filter)

    total_ordenes = OrdenToma.objects.count()
    ordenes_pendientes = OrdenToma.objects.filter(estado='pendiente').count()
    ordenes_validadas = OrdenToma.objects.filter(estado='validado').count()
    ordenes_completadas = OrdenToma.objects.filter(estado='completado').count()

    # Paginación
    paginator = Paginator(ordenes, 20)
    page = request.GET.get('page', 1)
    
    try:
        ordenes_paginadas = paginator.page(page)
    except:
        ordenes_paginadas = paginator.page(1)

    clientes = CustomUser.objects.filter(rol='cliente', is_active=True).order_by('empresa', 'first_name')

    context = {
        'ordenes': ordenes_paginadas,
        'total_ordenes': total_ordenes,
        'ordenes_pendientes': ordenes_pendientes,
        'ordenes_validadas': ordenes_validadas,
        'ordenes_completadas': ordenes_completadas,
        'search': search,
        'estado_filter': estado_filter,
        'prioridad_filter': prioridad_filter,
        'clientes': clientes,
    }
    return render(request, 'custom_admin/orders/list.html', context)
@login_required
@user_passes_test(is_admin)
def order_detail_api(request, order_id):
    """API para obtener detalle de orden - MEJORADO con órdenes generadas"""
    try:
        from apps.orders.models import OrdenToma
        
        orden = get_object_or_404(OrdenToma, pk=order_id)
        
        # Obtener órdenes generadas relacionadas
        ordenes_generadas_data = []
        for og in orden.ordenes_generadas.all().order_by('-fecha_generacion'):
            ordenes_generadas_data.append({
                'id': og.id,
                'numero_orden': og.numero_orden,
                'archivo_orden_pdf': og.archivo_orden_pdf.url if og.archivo_orden_pdf else None,
                'estado': og.estado,
                'fecha_generacion': og.fecha_generacion.strftime('%d/%m/%Y %H:%M'),
                'plantilla_usada': og.plantilla_usada.nombre if og.plantilla_usada else None
            })
        
        return JsonResponse({
            'success': True,
            'orden': {
                'id': orden.id,
                'codigo': orden.codigo,
                'cliente_id': orden.cliente.id if orden.cliente else None,
                'nombre_cliente': orden.nombre_cliente,
                'ruc_dni_cliente': orden.ruc_dni_cliente,
                'empresa_cliente': orden.empresa_cliente,
                'ciudad_cliente': orden.ciudad_cliente,
                'direccion_cliente': orden.direccion_cliente,
                'telefono_cliente': orden.telefono_cliente,
                'email_cliente': orden.email_cliente,
                'detalle_productos': orden.detalle_productos,
                'cantidad': orden.cantidad,
                'total': str(orden.total),
                'estado': orden.estado,
                'prioridad': orden.prioridad,
                'observaciones': orden.observaciones,
                'fecha_orden': orden.fecha_orden.strftime('%d/%m/%Y %H:%M'),
                'vendedor': orden.vendedor_asignado.get_full_name() if orden.vendedor_asignado else None,
                # Campos adicionales para completar toma
                'proyecto_campania': orden.proyecto_campania,
                'titulo_material': orden.titulo_material,
                'descripcion_breve': orden.descripcion_breve,
                'locaciones': orden.locaciones,
                'fecha_produccion_inicio': orden.fecha_produccion_inicio.strftime('%Y-%m-%d') if orden.fecha_produccion_inicio else None,
                'fecha_produccion_fin': orden.fecha_produccion_fin.strftime('%Y-%m-%d') if orden.fecha_produccion_fin else None,
                'hora_inicio': orden.hora_inicio.strftime('%H:%M') if orden.hora_inicio else None,
                'hora_fin': orden.hora_fin.strftime('%H:%M') if orden.hora_fin else None,
                'equipo_asignado': orden.equipo_asignado,
                'recursos_necesarios': orden.recursos_necesarios,
                'observaciones_completado': orden.observaciones_completado,
                # Órdenes generadas
                'ordenes_generadas': ordenes_generadas_data
            }
        })
        
    except Exception as e:
        print(f"❌ ERROR en order_detail_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def order_create_api(request):
    """API para crear orden manualmente"""
    try:
        from apps.orders.models import OrdenToma
        
        data = json.loads(request.body)
        
        cliente_id = data.get('cliente_id')
        if not cliente_id:
            return JsonResponse({'success': False, 'error': 'Cliente requerido'}, status=400)
        
        cliente = get_object_or_404(CustomUser, pk=cliente_id, rol='cliente')
        
        orden = OrdenToma.objects.create(
            cliente=cliente,
            detalle_productos=data.get('detalle_productos', ''),
            cantidad=int(data.get('cantidad', 1)),
            total=Decimal(data.get('total', '0.00')),
            prioridad=data.get('prioridad', 'normal'),
            observaciones=data.get('observaciones', ''),
            created_by=request.user,
            estado='pendiente'
        )
        
        # Registrar en LogEntry
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=orden.codigo,
            action_flag=ADDITION,
            change_message=f'Orden creada manualmente'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden creada exitosamente',
            'orden_id': orden.id,
            'codigo': orden.codigo
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "POST"])
def order_update_api(request, order_id):
    """API para actualizar orden - CORREGIDO para guardar todos los campos del modal"""
    try:
        from apps.orders.models import OrdenToma
        from datetime import datetime
        
        orden = get_object_or_404(OrdenToma, pk=order_id)
        data = json.loads(request.body)
        
        print(f"📥 Datos recibidos para orden {order_id}:", data)  # Debug
        
        # Si estamos completando la toma (estado cambia a completado)
        nuevo_estado = data.get('estado')
        if nuevo_estado and nuevo_estado == 'completado' and orden.estado != 'completado':
            # Validar campos requeridos para completar la toma
            campos_requeridos = [
                'proyecto_campania', 'titulo_material', 'descripcion_breve',
                'locaciones', 'fecha_produccion_inicio', 'fecha_produccion_fin',
                'hora_inicio', 'hora_fin', 'equipo_asignado'
            ]
            
            campos_faltantes = []
            for campo in campos_requeridos:
                if not data.get(campo):
                    campos_faltantes.append(campo.replace('_', ' ').title())
            
            if campos_faltantes:
                return JsonResponse({
                    'success': False, 
                    'error': f'Campos requeridos faltantes para completar la toma: {", ".join(campos_faltantes)}'
                }, status=400)
            
            # ✅ ACTUALIZAR TODOS LOS CAMPOS ADICIONALES DE LA TOMA
            orden.proyecto_campania = data.get('proyecto_campania')
            orden.titulo_material = data.get('titulo_material')
            orden.descripcion_breve = data.get('descripcion_breve')
            orden.locaciones = data.get('locaciones')
            
            # Convertir fechas y horas
            try:
                if data.get('fecha_produccion_inicio'):
                    orden.fecha_produccion_inicio = datetime.strptime(data.get('fecha_produccion_inicio'), '%Y-%m-%d').date()
                if data.get('fecha_produccion_fin'):
                    orden.fecha_produccion_fin = datetime.strptime(data.get('fecha_produccion_fin'), '%Y-%m-%d').date()
                if data.get('hora_inicio'):
                    orden.hora_inicio = datetime.strptime(data.get('hora_inicio'), '%H:%M').time()
                if data.get('hora_fin'):
                    orden.hora_fin = datetime.strptime(data.get('hora_fin'), '%H:%M').time()
            except ValueError as e:
                return JsonResponse({'success': False, 'error': f'Error en formato de fecha/hora: {str(e)}'}, status=400)
            
            orden.equipo_asignado = data.get('equipo_asignado')
            orden.recursos_necesarios = data.get('recursos_necesarios', '')
            orden.observaciones_completado = data.get('observaciones_completado', '')
            
            # Completar la orden
            orden.estado = 'completado'
            orden.completado_por = request.user
            orden.fecha_completado = timezone.now()
            orden.save()
            
            print(f"✅ Orden {orden.codigo} completada con datos de producción")  # Debug
            
        else:
            # Actualización normal (sin completar)
            orden.detalle_productos = data.get('detalle_productos', orden.detalle_productos)
            orden.cantidad = int(data.get('cantidad', orden.cantidad))
            orden.total = Decimal(data.get('total', orden.total))
            orden.prioridad = data.get('prioridad', orden.prioridad)
            orden.observaciones = data.get('observaciones', orden.observaciones)
            
            # ✅ ACTUALIZAR CAMPOS DE PRODUCCIÓN SI ESTÁN PRESENTES
            if data.get('proyecto_campania') is not None:
                orden.proyecto_campania = data.get('proyecto_campania')
            if data.get('titulo_material') is not None:
                orden.titulo_material = data.get('titulo_material')
            if data.get('descripcion_breve') is not None:
                orden.descripcion_breve = data.get('descripcion_breve')
            if data.get('locaciones') is not None:
                orden.locaciones = data.get('locaciones')
            if data.get('equipo_asignado') is not None:
                orden.equipo_asignado = data.get('equipo_asignado')
            if data.get('recursos_necesarios') is not None:
                orden.recursos_necesarios = data.get('recursos_necesarios')
            if data.get('observaciones_completado') is not None:
                orden.observaciones_completado = data.get('observaciones_completado')
            
            # Manejar fechas si vienen
            try:
                if data.get('fecha_produccion_inicio'):
                    orden.fecha_produccion_inicio = datetime.strptime(data.get('fecha_produccion_inicio'), '%Y-%m-%d').date()
                if data.get('fecha_produccion_fin'):
                    orden.fecha_produccion_fin = datetime.strptime(data.get('fecha_produccion_fin'), '%Y-%m-%d').date()
                if data.get('hora_inicio'):
                    orden.hora_inicio = datetime.strptime(data.get('hora_inicio'), '%H:%M').time()
                if data.get('hora_fin'):
                    orden.hora_fin = datetime.strptime(data.get('hora_fin'), '%H:%M').time()
            except ValueError as e:
                print(f"⚠️ Error en fechas: {e}")  # Debug
            
            # Cambio de estado normal
            if nuevo_estado and nuevo_estado != orden.estado:
                if nuevo_estado == 'validado':
                    orden.validar(request.user)
                elif nuevo_estado == 'en_produccion':
                    orden.enviar_a_produccion()
                elif nuevo_estado == 'cancelado':
                    orden.cancelar()
                else:
                    orden.estado = nuevo_estado
                    orden.save()
            else:
                orden.save()
        
        # Registrar en LogEntry
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=orden.codigo,
            action_flag=CHANGE,
            change_message=f'Orden actualizada - Estado: {orden.estado} - Datos producción guardados'
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Orden actualizada exitosamente',
            'orden_actualizada': {
                'id': orden.id,
                'estado': orden.estado,
                'proyecto_campania': orden.proyecto_campania,
                'titulo_material': orden.titulo_material,
                'descripcion_breve': orden.descripcion_breve,
                'locaciones': orden.locaciones,
                'equipo_asignado': orden.equipo_asignado
            }
        })
        
    except Exception as e:
        import traceback
        print("❌ ERROR en order_update_api:")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE", "POST"])
def order_delete_api(request, order_id):
    """API para eliminar orden"""
    try:
        from apps.orders.models import OrdenToma
        
        orden = get_object_or_404(OrdenToma, pk=order_id)
        codigo = orden.codigo
        
        # Registrar en LogEntry antes de eliminar
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=codigo,
            action_flag=DELETION,
            change_message=f'Orden eliminada'
        )
        
        orden.delete()
        
        return JsonResponse({'success': True, 'message': f'Orden {codigo} eliminada exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== VISTAS PARA PLANTILLAS DE ORDEN ====================

@login_required
@user_passes_test(is_admin)
def plantillas_orden_list(request):
    """Lista de plantillas de orden"""
    plantillas = PlantillaOrden.objects.all().order_by('-created_at')
    
    # Estadísticas
    total_plantillas = plantillas.count()
    plantillas_activas = plantillas.filter(is_active=True).count()
    plantillas_default = plantillas.filter(is_default=True).count()
    total_ordenes_generadas = OrdenGenerada.objects.count()
    
    context = {
        'plantillas': plantillas,
        'total_plantillas': total_plantillas,
        'plantillas_activas': plantillas_activas,
        'plantillas_default': plantillas_default,
        'total_ordenes_generadas': total_ordenes_generadas,
    }
    return render(request, 'custom_admin/orders/plantillas_list.html', context)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def plantilla_orden_crear_api(request):
    """API para crear plantilla de orden - VERSIÓN CORREGIDA"""
    try:
        nombre = request.POST.get('nombre')
        tipo_orden = request.POST.get('tipo_orden')
        version = request.POST.get('version', '1.0')
        descripcion = request.POST.get('descripcion', '')
        is_active = request.POST.get('is_active') == 'true'
        is_default = request.POST.get('is_default') == 'false'  # Por defecto False para evitar conflictos
        instrucciones = request.POST.get('instrucciones', '')
        archivo_plantilla = request.FILES.get('archivo_plantilla')
        
        # Validaciones
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        if not tipo_orden:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de orden es obligatorio'
            }, status=400)
        
        if not archivo_plantilla:
            return JsonResponse({
                'success': False,
                'error': 'El archivo de plantilla es obligatorio'
            }, status=400)
        
        # Validar que sea archivo .docx
        if not archivo_plantilla.name.endswith('.docx'):
            return JsonResponse({
                'success': False,
                'error': 'Solo se permiten archivos .docx'
            }, status=400)
        
        # Validar tamaño (máx 10MB)
        if archivo_plantilla.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'El archivo no debe superar los 10MB'
            }, status=400)
        
        # Si se marca como default, desmarcar las demás del mismo tipo
        if is_default:
            PlantillaOrden.objects.filter(
                tipo_orden=tipo_orden,
                is_default=True
            ).update(is_default=False)
        
        # Crear la plantilla
        plantilla = PlantillaOrden.objects.create(
            nombre=nombre,
            tipo_orden=tipo_orden,
            version=version,
            descripcion=descripcion,
            is_active=is_active,
            is_default=is_default,
            instrucciones=instrucciones,
            archivo_plantilla=archivo_plantilla,
            created_by=request.user
        )
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(plantilla).pk,
            object_id=plantilla.pk,
            object_repr=str(plantilla.nombre),
            action_flag=ADDITION,
            change_message=f'Plantilla de orden creada: {plantilla.nombre} - Tipo: {plantilla.get_tipo_orden_display()}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla creada exitosamente',
            'id': plantilla.id
        })
        
    except Exception as e:
        import traceback
        print("ERROR al crear plantilla:", traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al crear la plantilla: {str(e)}'
        }, status=500)
# ==================== VISTAS PARA GENERAR ÓRDENES ====================

@login_required
@user_passes_test(is_admin)
def orden_generar_api(request, orden_toma_id):
    """API para generar orden desde orden de toma"""
    try:
        from apps.orders.models import OrdenToma
        
        orden_toma = get_object_or_404(OrdenToma, pk=orden_toma_id)
        data = json.loads(request.body)
        
        plantilla_id = data.get('plantilla_id')
        
        # Generar la orden
        orden_generada = orden_toma.generar_orden_impresion(
            plantilla_id=plantilla_id,
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden generada exitosamente',
            'orden_generada_id': orden_generada.id,
            'numero_orden': orden_generada.numero_orden,
            'archivo_url': orden_generada.archivo_orden_pdf.url if orden_generada.archivo_orden_pdf else None
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_completar_y_generar_api(request, orden_toma_id):
    """Completa la orden y genera la orden para imprimir"""
    try:
        from apps.orders.models import OrdenToma
        from datetime import datetime
        
        orden_toma = get_object_or_404(OrdenToma, pk=orden_toma_id)
        data = json.loads(request.body)
        
        # Validar campos requeridos para completar
        campos_requeridos = [
            'proyecto_campania', 'titulo_material', 'descripcion_breve',
            'locaciones', 'fecha_produccion_inicio', 'fecha_produccion_fin',
            'hora_inicio', 'hora_fin', 'equipo_asignado'
        ]
        
        campos_faltantes = []
        for campo in campos_requeridos:
            if not data.get(campo):
                campos_faltantes.append(campo.replace('_', ' ').title())
        
        if campos_faltantes:
            return JsonResponse({
                'success': False, 
                'error': f'Campos requeridos faltantes: {", ".join(campos_faltantes)}'
            }, status=400)
        
        # Convertir fechas
        try:
            if data.get('fecha_produccion_inicio'):
                data['fecha_produccion_inicio'] = datetime.strptime(data['fecha_produccion_inicio'], '%Y-%m-%d').date()
            if data.get('fecha_produccion_fin'):
                data['fecha_produccion_fin'] = datetime.strptime(data['fecha_produccion_fin'], '%Y-%m-%d').date()
            if data.get('hora_inicio'):
                data['hora_inicio'] = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            if data.get('hora_fin'):
                data['hora_fin'] = datetime.strptime(data['hora_fin'], '%H:%M').time()
        except ValueError as e:
            return JsonResponse({'success': False, 'error': f'Error en formato de fecha/hora: {str(e)}'}, status=400)
        
        # Completar y generar orden
        orden_generada = orden_toma.completar_y_generar_orden(
            user=request.user,
            datos_completado=data
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden completada y generada exitosamente',
            'orden_generada_id': orden_generada.id,
            'numero_orden': orden_generada.numero_orden,
            'orden_toma_estado': 'completado'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_subir_validada_api(request, orden_generada_id):
    """API para subir orden validada - CORREGIDA para crear orden de producción"""
    try:
        orden_generada = get_object_or_404(OrdenGenerada, pk=orden_generada_id)
        
        if 'archivo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar un archivo PDF'
            }, status=400)
        
        archivo = request.FILES['archivo']
        
        if not archivo.name.endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'El archivo debe ser un PDF'
            }, status=400)
        
        # ✅ Obtener la orden de toma relacionada
        orden_toma = orden_generada.orden_toma
        
        # ✅ Marcar como validada
        orden_generada.marcar_como_validada(request.user, archivo)
        
        # ✅ CREAR ORDEN DE PRODUCCIÓN AUTOMÁTICAMENTE
        from apps.orders.models import OrdenProduccion, HistorialOrdenProduccion
        
        orden_produccion_creada = False
        
        # Verificar si ya existe una orden de producción para esta orden de toma
        if not OrdenProduccion.objects.filter(orden_toma=orden_toma).exists():
            try:
                orden_produccion = OrdenProduccion.objects.create(
                    orden_toma=orden_toma,
                    created_by=request.user,
                    estado='pendiente',
                    # Copiar datos automáticamente desde la orden de toma
                    nombre_cliente=orden_toma.nombre_cliente,
                    ruc_dni_cliente=orden_toma.ruc_dni_cliente,
                    empresa_cliente=orden_toma.empresa_cliente,
                    proyecto_campania=orden_toma.proyecto_campania or 'Proyecto por definir',
                    titulo_material=orden_toma.titulo_material or 'Material por definir',
                    descripcion_breve=orden_toma.descripcion_breve or 'Descripción por completar',
                    equipo_asignado=orden_toma.equipo_asignado or 'Equipo por asignar',
                    recursos_necesarios=orden_toma.recursos_necesarios or '',
                    fecha_inicio_planeada=orden_toma.fecha_produccion_inicio or timezone.now().date(),
                    fecha_fin_planeada=orden_toma.fecha_produccion_fin or (timezone.now() + timezone.timedelta(days=7)).date(),
                    tipo_produccion='video'  # Valor por defecto
                )
                
                print(f"✅ Orden de producción creada automáticamente: {orden_produccion.codigo}")
                
                # Crear entrada en el historial
                HistorialOrdenProduccion.objects.create(
                    orden_produccion=orden_produccion,
                    accion='creada',
                    usuario=request.user,
                    descripcion=f'Orden de producción creada automáticamente al validar orden de toma {orden_toma.codigo}'
                )
                
                orden_produccion_creada = True
                
            except Exception as e:
                print(f"❌ Error al crear orden de producción automática: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Orden validada exitosamente' + (' y orden de producción creada' if orden_produccion_creada else ''),
            'orden_produccion_creada': orden_produccion_creada
        })
        
    except Exception as e:
        import traceback
        print("❌ ERROR en orden_subir_validada_api:")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al subir el archivo: {str(e)}'
        }, status=500)
@login_required
@user_passes_test(is_admin)
def orden_descargar_api(request, orden_generada_id):
    """Descargar orden generada"""
    try:
        orden_generada = get_object_or_404(OrdenGenerada, pk=orden_generada_id)
        
        if not orden_generada.archivo_orden_pdf:
            messages.error(request, 'La orden no ha sido generada aún.')
            return redirect('custom_admin:orders_list')
        
        response = FileResponse(
            orden_generada.archivo_orden_pdf.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="Orden_{orden_generada.numero_orden}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al descargar la orden: {str(e)}')
        return redirect('custom_admin:orders_list')
        # ==================== APIs PARA PLANTILLAS DE ORDEN ====================

@login_required
@user_passes_test(is_admin)
def plantilla_orden_detalle_api(request, id):
    """API para obtener detalles de una plantilla de orden"""
    try:
        plantilla = PlantillaOrden.objects.get(pk=id)
        
        data = {
            'id': plantilla.id,
            'nombre': plantilla.nombre,
            'tipo_orden': plantilla.tipo_orden,
            'tipo_orden_display': plantilla.get_tipo_orden_display(),
            'version': plantilla.version,
            'descripcion': plantilla.descripcion or '',
            'is_active': plantilla.is_active,
            'is_default': plantilla.is_default,
            'instrucciones': plantilla.instrucciones or '',
            'archivo_plantilla': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None,
            'created_by': plantilla.created_by.username if plantilla.created_by else None,
            'created_at': plantilla.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': plantilla.updated_at.strftime('%d/%m/%Y %H:%M'),
            'ordenes_count': plantilla.ordenes_generadas.count(),
            'variables_disponibles': plantilla.variables_disponibles
        }
        
        return JsonResponse(data)
    except PlantillaOrden.DoesNotExist:
        return JsonResponse({'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "POST"])
def plantilla_orden_actualizar_api(request, id):
    """API para actualizar una plantilla de orden"""
    try:
        plantilla = PlantillaOrden.objects.get(pk=id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            nombre = data.get('nombre', plantilla.nombre)
            tipo_orden = data.get('tipo_orden', plantilla.tipo_orden)
            version = data.get('version', plantilla.version)
            descripcion = data.get('descripcion', plantilla.descripcion)
            is_active = data.get('is_active', plantilla.is_active)
            is_default = data.get('is_default', plantilla.is_default)
            instrucciones = data.get('instrucciones', plantilla.instrucciones)
            archivo_plantilla = None
        else:
            nombre = request.POST.get('nombre', plantilla.nombre)
            tipo_orden = request.POST.get('tipo_orden', plantilla.tipo_orden)
            version = request.POST.get('version', plantilla.version)
            descripcion = request.POST.get('descripcion', plantilla.descripcion)
            is_active = request.POST.get('is_active') == 'true'
            is_default = request.POST.get('is_default') == 'true'
            instrucciones = request.POST.get('instrucciones', plantilla.instrucciones)
            archivo_plantilla = request.FILES.get('archivo_plantilla')
        
        # Si se marca como default, desmarcar las demás del mismo tipo
        if is_default and not plantilla.is_default:
            PlantillaOrden.objects.filter(
                tipo_orden=plantilla.tipo_orden,
                is_default=True
            ).exclude(pk=id).update(is_default=False)
        
        plantilla.nombre = nombre
        plantilla.tipo_orden = tipo_orden
        plantilla.version = version
        plantilla.descripcion = descripcion
        plantilla.is_active = is_active
        plantilla.is_default = is_default
        plantilla.instrucciones = instrucciones
        
        if archivo_plantilla:
            plantilla.archivo_plantilla = archivo_plantilla
        
        plantilla.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla actualizada exitosamente'
        })
        
    except PlantillaOrden.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def plantilla_orden_eliminar_api(request, id):
    """API para eliminar una plantilla de orden"""
    try:
        plantilla = PlantillaOrden.objects.get(pk=id)
        
        # Verificar si tiene órdenes generadas
        if plantilla.ordenes_generadas.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar la plantilla porque tiene órdenes generadas asociadas'
            }, status=400)
        
        plantilla.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla eliminada exitosamente'
        })
    except PlantillaOrden.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def plantilla_orden_marcar_default_api(request, id):
    """API para marcar una plantilla como predeterminada"""
    try:
        plantilla = PlantillaOrden.objects.get(pk=id)
        
        # Desmarcar todas las demás plantillas del mismo tipo como default
        PlantillaOrden.objects.filter(
            tipo_orden=plantilla.tipo_orden,
            is_default=True
        ).exclude(pk=id).update(is_default=False)
        
        # Marcar esta plantilla como default
        plantilla.is_default = True
        plantilla.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Plantilla "{plantilla.nombre}" marcada como predeterminada'
        })
        
    except PlantillaOrden.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def plantilla_orden_descargar_api(request, id):
    """API para descargar el archivo de plantilla"""
    try:
        from django.http import FileResponse
        import os
        
        plantilla = PlantillaOrden.objects.get(pk=id)
        
        if not plantilla.archivo_plantilla:
            return JsonResponse({
                'success': False,
                'error': 'La plantilla no tiene un archivo adjunto'
            }, status=404)
        
        file_name = os.path.basename(plantilla.archivo_plantilla.name)
        response = FileResponse(
            plantilla.archivo_plantilla.open('rb'),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        return response
        
    except PlantillaOrden.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

        # Agregar estas vistas en custom_admin/views.py

@login_required
@user_passes_test(is_admin)
def api_plantillas_orden(request):
    """API para obtener todas las plantillas de orden activas"""
    try:
        plantillas = PlantillaOrden.objects.filter(is_active=True).order_by('-is_default', 'nombre')
        
        data = []
        for plantilla in plantillas:
            data.append({
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'tipo_orden': plantilla.tipo_orden,
                'tipo_orden_display': plantilla.get_tipo_orden_display(),
                'version': plantilla.version,
                'is_default': plantilla.is_default,
                'descripcion': plantilla.descripcion or '',
                'archivo_url': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None
            })
        
        return JsonResponse({'success': True, 'plantillas': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def orden_verificar_api(request, orden_generada_id):
    """API para verificar si una orden ya fue generada"""
    try:
        orden_generada = OrdenGenerada.objects.get(pk=orden_generada_id)
        
        return JsonResponse({
            'success': True,
            'archivo_url': orden_generada.archivo_orden_pdf.url if orden_generada.archivo_orden_pdf else None,
            'numero_orden': orden_generada.numero_orden,
            'estado': orden_generada.estado
        })
    
    except OrdenGenerada.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Orden no generada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
def actualizar_datos_clientes_ordenes():
    """Actualiza los datos de cliente en todas las órdenes"""
    ordenes = OrdenToma.objects.all()
    for orden in ordenes:
        if orden.cliente:
            print(f"Actualizando orden {orden.codigo} - Cliente: {orden.cliente.username}")
            orden.copiar_datos_cliente()
            orden.save()
    print("✅ Todas las órdenes actualizadas")    
# ==================== VISTAS PARA ÓRDENES DE PRODUCCIÓN ====================
@login_required
@user_passes_test(is_admin)
def ordenes_produccion_list(request):
    """Lista de órdenes de producción"""
    from apps.orders.models import OrdenProduccion
    
    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    tipo_filter = request.GET.get('tipo', '')
    prioridad_filter = request.GET.get('prioridad', '')

    ordenes = OrdenProduccion.objects.select_related(
        'orden_toma', 'productor_asignado', 'created_by'
    ).all()
    
    if search:
        ordenes = ordenes.filter(
            Q(codigo__icontains=search) |
            Q(orden_toma__codigo__icontains=search) |
            Q(nombre_cliente__icontains=search) |
            Q(proyecto_campania__icontains=search)
        )
    
    if estado_filter:
        ordenes = ordenes.filter(estado=estado_filter)
    
    if tipo_filter:
        ordenes = ordenes.filter(tipo_produccion=tipo_filter)
    
    if prioridad_filter:
        ordenes = ordenes.filter(prioridad=prioridad_filter)

    # Precalcular el valor absoluto para cada orden
    ordenes_con_abs = []
    for orden in ordenes:
        # Calcular valor absoluto para días de retraso negativos
        if orden.dias_retraso < 0:
            orden.dias_retraso_abs = abs(orden.dias_retraso)
        else:
            orden.dias_retraso_abs = orden.dias_retraso
        ordenes_con_abs.append(orden)

    # Estadísticas
    total_ordenes = OrdenProduccion.objects.count()
    ordenes_pendientes = OrdenProduccion.objects.filter(estado='pendiente').count()
    ordenes_en_produccion = OrdenProduccion.objects.filter(estado='en_produccion').count()
    ordenes_completadas = OrdenProduccion.objects.filter(estado='completado').count()
    ordenes_validadas = OrdenProduccion.objects.filter(estado='validado').count()

    # Paginación
    paginator = Paginator(ordenes_con_abs, 20)
    page = request.GET.get('page', 1)
    
    try:
        ordenes_paginadas = paginator.page(page)
    except:
        ordenes_paginadas = paginator.page(1)

    # Obtener productores para filtros
    productores = CustomUser.objects.filter(rol='productor', is_active=True).order_by('first_name', 'last_name')

    context = {
        'ordenes': ordenes_paginadas,
        'total_ordenes': total_ordenes,
        'ordenes_pendientes': ordenes_pendientes,
        'ordenes_en_produccion': ordenes_en_produccion,
        'ordenes_completadas': ordenes_completadas,
        'ordenes_validadas': ordenes_validadas,
        'search': search,
        'estado_filter': estado_filter,
        'tipo_filter': tipo_filter,
        'prioridad_filter': prioridad_filter,
        'productores': productores,
        'tipos_produccion': OrdenProduccion._meta.get_field('tipo_produccion').choices,
    }
    return render(request, 'custom_admin/ordenes_produccion/list.html', context)
@login_required
@user_passes_test(is_admin)
def orden_produccion_detail_api(request, order_id):
    """API para obtener detalle de orden de producción"""
    try:
        from apps.orders.models import OrdenProduccion
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        
        # Calcular valor absoluto para días de retraso
        dias_retraso_abs = abs(orden.dias_retraso) if orden.dias_retraso else 0
        
        return JsonResponse({
            'success': True,
            'orden': {
                'id': orden.id,
                'codigo': orden.codigo,
                'orden_toma_id': orden.orden_toma.id,
                'orden_toma_codigo': orden.orden_toma.codigo,
                'nombre_cliente': orden.nombre_cliente,
                'ruc_dni_cliente': orden.ruc_dni_cliente,
                'empresa_cliente': orden.empresa_cliente,
                'proyecto_campania': orden.proyecto_campania,
                'titulo_material': orden.titulo_material,
                'descripcion_breve': orden.descripcion_breve,
                'tipo_produccion': orden.tipo_produccion,
                'especificaciones_tecnicas': orden.especificaciones_tecnicas,
                'fecha_inicio_planeada': orden.fecha_inicio_planeada.strftime('%Y-%m-%d') if orden.fecha_inicio_planeada else None,
                'fecha_fin_planeada': orden.fecha_fin_planeada.strftime('%Y-%m-%d') if orden.fecha_fin_planeada else None,
                'fecha_inicio_real': orden.fecha_inicio_real.strftime('%Y-%m-%d') if orden.fecha_inicio_real else None,
                'fecha_fin_real': orden.fecha_fin_real.strftime('%Y-%m-%d') if orden.fecha_fin_real else None,
                'equipo_asignado': orden.equipo_asignado,
                'recursos_necesarios': orden.recursos_necesarios,
                'archivos_entregables': orden.archivos_entregables,
                'observaciones_produccion': orden.observaciones_produccion,
                'estado': orden.estado,
                'prioridad': orden.prioridad,
                'productor_asignado_id': orden.productor_asignado.id if orden.productor_asignado else None,
                'productor_asignado_nombre': orden.productor_asignado.get_full_name() if orden.productor_asignado else None,
                'dias_retraso': orden.dias_retraso,
                'dias_retraso_abs': dias_retraso_abs,  # Nuevo campo
                'fecha_creacion': orden.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_produccion_create_api(request):
    """API para crear orden de producción manualmente"""
    try:
        from apps.orders.models import OrdenProduccion, OrdenToma
        
        data = json.loads(request.body)
        
        orden_toma_id = data.get('orden_toma_id')
        if not orden_toma_id:
            return JsonResponse({'success': False, 'error': 'Orden de toma requerida'}, status=400)
        
        orden_toma = get_object_or_404(OrdenToma, pk=orden_toma_id)
        
        # Verificar si ya existe una orden de producción para esta orden de toma
        if OrdenProduccion.objects.filter(orden_toma=orden_toma).exists():
            return JsonResponse({
                'success': False, 
                'error': 'Ya existe una orden de producción para esta orden de toma'
            }, status=400)
        
        orden = OrdenProduccion.objects.create(
            orden_toma=orden_toma,
            prioridad=data.get('prioridad', 'normal'),
            tipo_produccion=data.get('tipo_produccion', 'video'),
            productor_asignado_id=data.get('productor_asignado_id'),
            created_by=request.user,
        )
        
        # Registrar en LogEntry
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=orden.codigo,
            action_flag=ADDITION,
            change_message=f'Orden de producción creada manualmente desde orden de toma {orden_toma.codigo}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden de producción creada exitosamente',
            'orden_id': orden.id,
            'codigo': orden.codigo
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "POST"])
def orden_produccion_update_api(request, order_id):
    """API para actualizar orden de producción"""
    try:
        from apps.orders.models import OrdenProduccion
        from datetime import datetime
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        data = json.loads(request.body)
        
        # Actualizar campos
        orden.tipo_produccion = data.get('tipo_produccion', orden.tipo_produccion)
        orden.especificaciones_tecnicas = data.get('especificaciones_tecnicas', orden.especificaciones_tecnicas)
        orden.archivos_entregables = data.get('archivos_entregables', orden.archivos_entregables)
        orden.observaciones_produccion = data.get('observaciones_produccion', orden.observaciones_produccion)
        orden.prioridad = data.get('prioridad', orden.prioridad)
        
        # Fechas
        if data.get('fecha_inicio_planeada'):
            orden.fecha_inicio_planeada = datetime.strptime(data.get('fecha_inicio_planeada'), '%Y-%m-%d').date()
        if data.get('fecha_fin_planeada'):
            orden.fecha_fin_planeada = datetime.strptime(data.get('fecha_fin_planeada'), '%Y-%m-%d').date()
        
        # Productor asignado
        if data.get('productor_asignado_id'):
            try:
                productor = CustomUser.objects.get(pk=data['productor_asignado_id'], rol='productor')
                orden.productor_asignado = productor
            except CustomUser.DoesNotExist:
                pass
        
        orden.save()
        
        # Registrar en LogEntry
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=orden.codigo,
            action_flag=CHANGE,
            change_message=f'Orden de producción actualizada'
        )
        
        return JsonResponse({'success': True, 'message': 'Orden de producción actualizada exitosamente'})
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE", "POST"])
def orden_produccion_delete_api(request, order_id):
    """API para eliminar orden de producción"""
    try:
        from apps.orders.models import OrdenProduccion
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        codigo = orden.codigo
        
        # Registrar en LogEntry antes de eliminar
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(orden).pk,
            object_id=orden.pk,
            object_repr=codigo,
            action_flag=DELETION,
            change_message=f'Orden de producción eliminada'
        )
        
        orden.delete()
        
        return JsonResponse({'success': True, 'message': f'Orden de producción {codigo} eliminada exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_produccion_iniciar_api(request, order_id):
    """API para iniciar producción"""
    try:
        from apps.orders.models import OrdenProduccion
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        
        if orden.estado != 'pendiente':
            return JsonResponse({
                'success': False, 
                'error': 'Solo se pueden iniciar órdenes en estado pendiente'
            }, status=400)
        
        orden.iniciar_produccion()
        
        return JsonResponse({
            'success': True, 
            'message': 'Producción iniciada exitosamente',
            'nuevo_estado': orden.estado
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_produccion_completar_api(request, order_id):
    """API para completar producción"""
    try:
        from apps.orders.models import OrdenProduccion
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        
        if orden.estado != 'en_produccion':
            return JsonResponse({
                'success': False, 
                'error': 'Solo se pueden completar órdenes en estado de producción'
            }, status=400)
        
        orden.completar(request.user)
        
        return JsonResponse({
            'success': True, 
            'message': 'Producción completada exitosamente',
            'nuevo_estado': orden.estado
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_produccion_validar_api(request, order_id):
    """API para validar orden de producción"""
    try:
        from apps.orders.models import OrdenProduccion
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        
        if orden.estado != 'completado':
            return JsonResponse({
                'success': False, 
                'error': 'Solo se pueden validar órdenes completadas'
            }, status=400)
        
        orden.validar(request.user)
        
        return JsonResponse({
            'success': True, 
            'message': 'Orden de producción validada exitosamente',
            'nuevo_estado': orden.estado
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
# Añade estas APIs en views.py
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_produccion_generar_api(request, order_id):
    """API para generar orden de producción desde plantilla - VERSIÓN CORREGIDA"""
    try:
        from apps.orders.models import OrdenProduccion, OrdenGenerada
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        data = json.loads(request.body)
        
        plantilla_id = data.get('plantilla_id')
        
        if not plantilla_id:
            return JsonResponse({
                'success': False,
                'error': 'Plantilla requerida'
            }, status=400)
        
        try:
            plantilla = PlantillaOrden.objects.get(id=plantilla_id, is_active=True)
        except PlantillaOrden.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Plantilla no encontrada o no activa'
            }, status=404)
        
        # ✅ USAR EL MÉTODO CORREGIDO
        orden_generada = orden.generar_orden_desde_plantilla(
            plantilla_id=plantilla_id,
            user=request.user
        )
        
        if orden_generada:
            return JsonResponse({
                'success': True,
                'message': 'Orden de producción generada exitosamente',
                'orden_generada_id': orden_generada.id,
                'numero_orden': orden_generada.numero_orden,
                'archivo_url': orden_generada.archivo_orden_pdf.url if orden_generada.archivo_orden_pdf else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error al generar la orden'
            }, status=500)
        
    except Exception as e:
        print(f"❌ ERROR en orden_produccion_generar_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
        
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def orden_produccion_subir_firmada_api(request, order_id):
    """API para subir orden de producción firmada"""
    try:
        from apps.orders.models import OrdenProduccion
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        
        if 'archivo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar un archivo PDF'
            }, status=400)
        
        archivo = request.FILES['archivo']
        
        if not archivo.name.endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'El archivo debe ser un PDF'
            }, status=400)
        
        # Procesar la orden firmada
        if orden.subir_orden_firmada(archivo, request.user):
            return JsonResponse({
                'success': True,
                'message': 'Orden de producción validada exitosamente',
                'nuevo_estado': orden.estado
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error al procesar la orden firmada'
            }, status=500)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def orden_produccion_descargar_plantilla_api(request, order_id):
    """API para descargar la orden generada desde plantilla"""
    try:
        from apps.orders.models import OrdenProduccion
        from django.http import FileResponse
        import os
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        
        # Buscar si ya existe una orden generada
        orden_generada = orden.ordenes_generadas_produccion.filter(
            estado='generada'
        ).first()
        
        if orden_generada and orden_generada.archivo_orden_pdf:
            # Si ya existe PDF generado, descargarlo
            file_name = f"Orden_Produccion_{orden.codigo}.pdf"
            response = FileResponse(
                orden_generada.archivo_orden_pdf.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
        else:
            # Si no existe, generar una nueva
            if not orden.plantilla_orden:
                return JsonResponse({
                    'success': False,
                    'error': 'No hay plantilla asignada para esta orden'
                }, status=400)
            
            # Generar orden desde plantilla
            temp_file_path = orden.generar_orden_desde_plantilla().archivo_orden_pdf.path
            
            # Crear respuesta de descarga
            file_name = f"Orden_Produccion_{orden.codigo}.pdf"
            response = FileResponse(
                open(temp_file_path, 'rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            
            return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def orden_produccion_obtener_plantillas_api(request, order_id):
    """API para obtener plantillas disponibles para orden de producción - MEJORADO"""
    try:
        from apps.orders.models import OrdenProduccion
        
        orden = get_object_or_404(OrdenProduccion, pk=order_id)
        
        # Obtener plantillas activas de todos los tipos relevantes para producción
        plantillas = PlantillaOrden.objects.filter(
            is_active=True
        ).order_by('-is_default', 'nombre')
        
        data = []
        for plantilla in plantillas:
            data.append({
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'tipo_orden': plantilla.tipo_orden,
                'tipo_orden_display': plantilla.get_tipo_orden_display(),
                'version': plantilla.version,
                'is_default': plantilla.is_default,
                'descripcion': plantilla.descripcion or '',
                'archivo_url': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None
            })
        
        return JsonResponse({'success': True, 'plantillas': data})
    
    except Exception as e:
        print(f"❌ ERROR en orden_produccion_obtener_plantillas_api: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
# ==================== VISTAS PARA PARTE MORTORIOS ====================

@login_required
@user_passes_test(is_admin)
def parte_mortorios_list(request):
    """Lista de partes mortorios del sistema"""
    
    # ✅ Verificar disponibilidad del módulo
    if not PARTE_MORTORIO_MODELS_AVAILABLE:
        context = {'mensaje': 'Módulo de Parte Mortorios no disponible'}
        return render(request, 'custom_admin/en_desarrollo.html', context)
    
    try:
        # Filtros
        search = request.GET.get('search', '')
        estado_filter = request.GET.get('estado', '')
        urgencia_filter = request.GET.get('urgencia', '')
        cliente_filter = request.GET.get('cliente', '')
        fecha_filter = request.GET.get('fecha', '')
        
        partes = ParteMortorio.objects.select_related(
            'cliente', 'creado_por'
        ).all().order_by('-fecha_solicitud')
        
        if search:
            partes = partes.filter(
                Q(codigo__icontains=search) |
                Q(nombre_fallecido__icontains=search) |
                Q(dni_fallecido__icontains=search) |
                Q(nombre_esposa__icontains=search) |
                Q(nombres_hijos__icontains=search) |
                Q(familiares_adicionales__icontains=search)
            )
        
        if estado_filter:
            partes = partes.filter(estado=estado_filter)
        
        if urgencia_filter:
            partes = partes.filter(urgencia=urgencia_filter)
            
        if cliente_filter:
            partes = partes.filter(cliente_id=cliente_filter)
            
        if fecha_filter:
            try:
                fecha = datetime.strptime(fecha_filter, '%Y-%m-%d').date()
                partes = partes.filter(fecha_fallecimiento=fecha)
            except ValueError:
                # Si la fecha no es válida, ignorar el filtro
                pass
        
        # Estadísticas
        total_partes = partes.count()
        partes_solicitados = partes.filter(estado='solicitado').count()
        partes_programados = partes.filter(estado='programado').count()
        partes_transmitidos = partes.filter(estado='transmitido').count()
        partes_cancelados = partes.filter(estado='cancelado').count()
        
        # Obtener clientes para filtro
        clientes = CustomUser.objects.filter(
            rol='cliente',
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Paginación
        paginator = Paginator(partes, 20)
        page = request.GET.get('page', 1)
        
        try:
            partes_paginadas = paginator.page(page)
        except PageNotAnInteger:
            partes_paginadas = paginator.page(1)
        except EmptyPage:
            partes_paginadas = paginator.page(paginator.num_pages)
        
        context = {
            'partes': partes_paginadas,
            'total_partes': total_partes,
            'partes_solicitados': partes_solicitados,
            'partes_programados': partes_programados,
            'partes_transmitidos': partes_transmitidos,
            'partes_cancelados': partes_cancelados,
            'search': search,
            'estado_filter': estado_filter,
            'urgencia_filter': urgencia_filter,
            'cliente_filter': cliente_filter,
            'fecha_filter': fecha_filter,
            'clientes': clientes,
            'estados': ParteMortorio.ESTADO_CHOICES,
            'urgencias': ParteMortorio.URGENCIA_CHOICES,
        }
        
        return render(request, 'custom_admin/parte_mortorios/list.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en parte_mortorios_list: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback a datos de ejemplo si hay error
        context = {
            'partes': [],
            'total_partes': 0,
            'partes_solicitados': 0,
            'partes_programados': 0,
            'partes_transmitidos': 0,
            'partes_cancelados': 0,
            'search': search if 'search' in locals() else '',
            'estado_filter': estado_filter if 'estado_filter' in locals() else '',
            'urgencia_filter': urgencia_filter if 'urgencia_filter' in locals() else '',
            'cliente_filter': cliente_filter if 'cliente_filter' in locals() else '',
            'fecha_filter': fecha_filter if 'fecha_filter' in locals() else '',
            'clientes': CustomUser.objects.filter(rol='cliente', is_active=True).order_by('first_name', 'last_name')[:10],
            'estados': [
                ('solicitado', 'Solicitado'),
                ('programado', 'Programado'),
                ('transmitido', 'Transmitido'),
                ('cancelado', 'Cancelado'),
            ],
            'urgencias': [
                ('normal', 'Normal'),
                ('urgente', 'Urgente'),
                ('muy_urgente', 'Muy Urgente'),
            ],
        }
        return render(request, 'custom_admin/parte_mortorios/list.html', context)
@login_required
@user_passes_test(is_admin)
def parte_mortorio_detail_api(request, parte_id):
    """API para obtener detalles de un parte mortorio - VERSIÓN CORREGIDA"""
    
    if not PARTE_MORTORIO_MODELS_AVAILABLE:
        return JsonResponse({'error': 'Módulo de Parte Mortorios no disponible'}, status=503)
    
    try:
        parte = get_object_or_404(ParteMortorio, pk=parte_id)
        
        data = {
            'id': parte.id,
            'codigo': parte.codigo,
            'cliente_id': parte.cliente.id,
            'cliente_nombre': parte.cliente.get_full_name(),
            'nombre_fallecido': parte.nombre_fallecido,
            'edad_fallecido': parte.edad_fallecido,
            'dni_fallecido': parte.dni_fallecido,
            'fecha_nacimiento': parte.fecha_nacimiento.strftime('%Y-%m-%d') if parte.fecha_nacimiento else None,
            'fecha_fallecimiento': parte.fecha_fallecimiento.strftime('%Y-%m-%d') if parte.fecha_fallecimiento else None,
            # Información familiar
            'nombre_esposa': parte.nombre_esposa,
            'cantidad_hijos': parte.cantidad_hijos,
            'hijos_vivos': parte.hijos_vivos,
            'hijos_fallecidos': parte.hijos_fallecidos,
            'nombres_hijos': parte.nombres_hijos,
            'familiares_adicionales': parte.familiares_adicionales,
            # Información de ceremonia
            'tipo_ceremonia': parte.tipo_ceremonia,
            'tipo_ceremonia_display': parte.get_tipo_ceremonia_display(),
            'fecha_misa': parte.fecha_misa.strftime('%Y-%m-%d') if parte.fecha_misa else None,
            'hora_misa': parte.hora_misa.strftime('%H:%M') if parte.hora_misa else None,
            'lugar_misa': parte.lugar_misa,
            # Información de transmisión
            'fecha_inicio_transmision': parte.fecha_inicio_transmision.strftime('%Y-%m-%d') if parte.fecha_inicio_transmision else None,
            'fecha_fin_transmision': parte.fecha_fin_transmision.strftime('%Y-%m-%d') if parte.fecha_fin_transmision else None,
            'hora_transmision': parte.hora_transmision.strftime('%H:%M') if parte.hora_transmision else None,
            'duracion_transmision': parte.duracion_transmision,
            'repeticiones_dia': parte.repeticiones_dia,
            # ✅ SOLO PRECIO TOTAL - SIN precio_por_segundo
            'precio_total': str(parte.precio_total),
            # Configuración
            'estado': parte.estado,
            'estado_display': parte.get_estado_display(),
            'urgencia': parte.urgencia,
            'urgencia_display': parte.get_urgencia_display(),
            'observaciones': parte.observaciones,
            'mensaje_personalizado': parte.mensaje_personalizado,
            'fecha_solicitud': parte.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
            'creado_por_nombre': parte.creado_por.get_full_name() if parte.creado_por else '',
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        print(f"❌ ERROR en parte_mortorio_detail_api: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_create_api(request):
    """API para crear un nuevo parte mortorio - VERSIÓN CORREGIDA SIN precio_por_segundo"""
    try:
        # ✅ IMPORTACIÓN CORRECTA
        from apps.parte_mortorios.models import ParteMortorio
        from datetime import datetime
        from decimal import Decimal
        
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['cliente_id', 'nombre_fallecido', 'fecha_fallecimiento', 'precio_total']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'El campo {field} es obligatorio'
                }, status=400)
        
        # Obtener cliente
        try:
            cliente = CustomUser.objects.get(pk=data['cliente_id'], rol='cliente')
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cliente no encontrado'
            }, status=404)
        
        # Crear el parte mortorio
        parte = ParteMortorio.objects.create(
            cliente=cliente,
            nombre_fallecido=data['nombre_fallecido'],
            edad_fallecido=data.get('edad_fallecido'),
            dni_fallecido=data.get('dni_fallecido'),
            fecha_fallecimiento=datetime.strptime(data['fecha_fallecimiento'], '%Y-%m-%d').date(),
            # ✅ PRECIO TOTAL MANUAL - SIN precio_por_segundo
            precio_total=Decimal(data['precio_total']),
            # Nuevos campos familiares
            nombre_esposa=data.get('nombre_esposa'),
            cantidad_hijos=int(data.get('cantidad_hijos', 0)),
            hijos_vivos=int(data.get('hijos_vivos', 0)),
            hijos_fallecidos=int(data.get('hijos_fallecidos', 0)),
            nombres_hijos=data.get('nombres_hijos'),
            familiares_adicionales=data.get('familiares_adicionales'),
            # Información de ceremonia
            tipo_ceremonia=data.get('tipo_ceremonia', 'misa'),
            # Información de transmisión
            duracion_transmision=int(data.get('duracion_transmision', 1)),
            repeticiones_dia=int(data.get('repeticiones_dia', 1)),
            # Configuración
            estado=data.get('estado', 'solicitado'),
            urgencia=data.get('urgencia', 'normal'),
            observaciones=data.get('observaciones'),
            mensaje_personalizado=data.get('mensaje_personalizado'),
            creado_por=request.user
        )
        
        # Manejar campos opcionales de fecha
        if data.get('fecha_nacimiento'):
            parte.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
        
        if data.get('fecha_misa'):
            parte.fecha_misa = datetime.strptime(data['fecha_misa'], '%Y-%m-%d').date()
        
        if data.get('hora_misa'):
            parte.hora_misa = datetime.strptime(data['hora_misa'], '%H:%M').time()
            
        if data.get('hora_transmision'):
            parte.hora_transmision = datetime.strptime(data['hora_transmision'], '%H:%M').time()
        
        if data.get('fecha_inicio_transmision'):
            parte.fecha_inicio_transmision = datetime.strptime(data['fecha_inicio_transmision'], '%Y-%m-%d').date()
        
        if data.get('fecha_fin_transmision'):
            parte.fecha_fin_transmision = datetime.strptime(data['fecha_fin_transmision'], '%Y-%m-%d').date()
        
        parte.lugar_misa = data.get('lugar_misa')
        parte.save()
        
        # Registrar en historial
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.contenttypes.models import ContentType
        
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(parte).pk,
            object_id=parte.pk,
            object_repr=f"Parte mortorio creado: {parte.codigo}",
            action_flag=ADDITION,
            change_message=f'Parte mortorio creado: {parte.codigo} - Fallecido: {parte.nombre_fallecido} - Precio: ${parte.precio_total}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio creado exitosamente',
            'parte_id': parte.id,
            'codigo': parte.codigo,
            'precio_total': str(parte.precio_total)
        })
        
    except Exception as e:
        import traceback
        print("❌ ERROR en parte_mortorio_create_api:")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al crear el parte mortorio: {str(e)}'
        }, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "POST"])
def parte_mortorio_update_api(request, parte_id):
    """API para actualizar un parte mortorio existente - VERSIÓN CORREGIDA"""
    try:
        from apps.parte_mortorios.models import ParteMortorio
        from datetime import datetime
        from decimal import Decimal
        
        parte = get_object_or_404(ParteMortorio, pk=parte_id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # Actualizar campos básicos
        if 'nombre_fallecido' in data:
            parte.nombre_fallecido = data['nombre_fallecido']
        
        if 'edad_fallecido' in data:
            parte.edad_fallecido = int(data['edad_fallecido']) if data['edad_fallecido'] else None
        
        if 'dni_fallecido' in data:
            parte.dni_fallecido = data['dni_fallecido']
        
        if 'fecha_fallecimiento' in data and data['fecha_fallecimiento']:
            parte.fecha_fallecimiento = datetime.strptime(data['fecha_fallecimiento'], '%Y-%m-%d').date()
        
        # ✅ ACTUALIZAR PRECIO TOTAL (sin precio_por_segundo)
        if 'precio_total' in data:
            parte.precio_total = Decimal(data['precio_total'])
        
        # Información familiar
        if 'nombre_esposa' in data:
            parte.nombre_esposa = data['nombre_esposa']
        
        if 'cantidad_hijos' in data:
            parte.cantidad_hijos = int(data['cantidad_hijos']) if data['cantidad_hijos'] else 0
        
        if 'hijos_vivos' in data:
            parte.hijos_vivos = int(data['hijos_vivos']) if data['hijos_vivos'] else 0
        
        if 'hijos_fallecidos' in data:
            parte.hijos_fallecidos = int(data['hijos_fallecidos']) if data['hijos_fallecidos'] else 0
        
        if 'nombres_hijos' in data:
            parte.nombres_hijos = data['nombres_hijos']
        
        if 'familiares_adicionales' in data:
            parte.familiares_adicionales = data['familiares_adicionales']
        
        # Información de ceremonia
        if 'tipo_ceremonia' in data:
            parte.tipo_ceremonia = data['tipo_ceremonia']
        
        if 'fecha_misa' in data and data['fecha_misa']:
            parte.fecha_misa = datetime.strptime(data['fecha_misa'], '%Y-%m-%d').date()
        
        if 'hora_misa' in data and data['hora_misa']:
            parte.hora_misa = datetime.strptime(data['hora_misa'], '%H:%M').time()
        
        if 'lugar_misa' in data:
            parte.lugar_misa = data['lugar_misa']
        
        # Información de transmisión
        if 'fecha_inicio_transmision' in data and data['fecha_inicio_transmision']:
            parte.fecha_inicio_transmision = datetime.strptime(data['fecha_inicio_transmision'], '%Y-%m-%d').date()
        
        if 'fecha_fin_transmision' in data and data['fecha_fin_transmision']:
            parte.fecha_fin_transmision = datetime.strptime(data['fecha_fin_transmision'], '%Y-%m-%d').date()
        
        if 'hora_transmision' in data and data['hora_transmision']:
            parte.hora_transmision = datetime.strptime(data['hora_transmision'], '%H:%M').time()
        
        if 'duracion_transmision' in data:
            parte.duracion_transmision = int(data['duracion_transmision'])
        
        if 'repeticiones_dia' in data:
            parte.repeticiones_dia = int(data['repeticiones_dia'])
        
        # Configuración
        if 'estado' in data:
            parte.estado = data['estado']
        
        if 'urgencia' in data:
            parte.urgencia = data['urgencia']
        
        if 'observaciones' in data:
            parte.observaciones = data['observaciones']
        
        if 'mensaje_personalizado' in data:
            parte.mensaje_personalizado = data['mensaje_personalizado']
        
        # Actualizar cliente si se proporciona
        if 'cliente_id' in data and data['cliente_id']:
            try:
                cliente = CustomUser.objects.get(pk=data['cliente_id'], rol='cliente')
                parte.cliente = cliente
            except CustomUser.DoesNotExist:
                pass
        
        parte.save()
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(parte).pk,
            object_id=parte.pk,
            object_repr=f"Parte mortorio actualizado: {parte.codigo}",
            action_flag=CHANGE,
            change_message=f'Parte mortorio {parte.codigo} actualizado - Precio: ${parte.precio_total}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio actualizado exitosamente'
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar el parte mortorio: {str(e)}'
        }, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE", "POST"])
def parte_mortorio_delete_api(request, parte_id):
    """API para eliminar un parte mortorio"""
    try:
        from .models import ParteMortorio
        
        parte = get_object_or_404(ParteMortorio, pk=parte_id)
        codigo = parte.codigo
        
        # Registrar en historial antes de eliminar
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(parte).pk,
            object_id=parte.pk,
            object_repr=f"Parte mortorio eliminado: {codigo}",
            action_flag=DELETION,
            change_message=f'Parte mortorio {codigo} eliminado'
        )
        
        parte.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar el parte mortorio: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_programar_api(request, parte_id):
    """API para programar un parte mortorio"""
    try:
        from .models import ParteMortorio
        
        parte = get_object_or_404(ParteMortorio, pk=parte_id)
        parte.programar(request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio programado exitosamente',
            'nuevo_estado': parte.estado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al programar el parte mortorio: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_marcar_transmitido_api(request, parte_id):
    """API para marcar un parte mortorio como transmitido"""
    try:
        from .models import ParteMortorio
        
        parte = get_object_or_404(ParteMortorio, pk=parte_id)
        parte.marcar_transmitido(request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio marcado como transmitido',
            'nuevo_estado': parte.estado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al marcar como transmitido: {str(e)}'
        }, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_cambiar_estado_api(request, parte_id):
    """API para cambiar el estado de un parte mortorio - VERSIÓN SIMPLIFICADA"""
    try:
        from apps.parte_mortorios.models import ParteMortorio
        
        parte = get_object_or_404(ParteMortorio, pk=parte_id)
        data = json.loads(request.body)
        
        nuevo_estado = data.get('estado')
        estados_permitidos = ['pendiente', 'al_aire', 'pausado', 'finalizado']
        
        if nuevo_estado not in estados_permitidos:
            return JsonResponse({
                'success': False,
                'error': f'Estado no válido: {nuevo_estado}'
            }, status=400)
        
        estado_anterior = parte.estado
        parte.estado = nuevo_estado
        
        # Registrar fecha según el estado
        if nuevo_estado == 'al_aire':
            parte.fecha_programacion = timezone.now()
        elif nuevo_estado == 'finalizado':
            parte.fecha_transmision_completada = timezone.now()
        
        parte.save()
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(parte).pk,
            object_id=parte.pk,
            object_repr=f"Parte {parte.codigo}",
            action_flag=CHANGE,
            change_message=f'Estado cambiado: {estado_anterior} → {nuevo_estado}'
        )
        
        mensajes_estado = {
            'pendiente': '🟡 Parte marcado como Pendiente',
            'al_aire': '🟢 Parte puesto Al Aire',
            'pausado': '⏸️ Parte Pausado',
            'finalizado': '🔴 Parte Finalizado'
        }
        
        return JsonResponse({
            'success': True,
            'message': mensajes_estado.get(nuevo_estado, 'Estado actualizado'),
            'nuevo_estado': nuevo_estado,
            'estado_display': parte.get_estado_display()
        })
        
    except Exception as e:
        import traceback
        print(f"❌ ERROR en parte_mortorio_cambiar_estado_api: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al cambiar el estado: {str(e)}'
        }, status=500)
@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_cancelar_api(request, parte_id):
    """API para cancelar un parte mortorio"""
    try:
        from .models import ParteMortorio
        
        parte = get_object_or_404(ParteMortorio, pk=parte_id)
        parte.cancelar(request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio cancelado',
            'nuevo_estado': parte.estado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al cancelar el parte mortorio: {str(e)}'
        }, status=500)
# ==================== VISTAS PARA PLANTILLAS DE PARTE MORTORIO ====================

@login_required
@user_passes_test(is_admin)
def plantillas_parte_mortorio_list(request):
    """Lista de plantillas de parte mortorio"""
    
    # ✅ Verificar disponibilidad del módulo
    if not PARTE_MORTORIO_MODELS_AVAILABLE or PlantillaParteMortorio is None:
        context = {
            'plantillas': [],
            'total_plantillas': 0,
            'plantillas_activas': 0,
            'plantillas_default': 0,
            'total_partes_generados': 0,
            'mensaje_error': 'Módulo de Plantillas de Parte Mortorio no disponible'
        }
        return render(request, 'custom_admin/parte_mortorios/plantillas_list.html', context)
    
    try:
        plantillas = PlantillaParteMortorio.objects.all().order_by('-created_at')
        
        # Estadísticas
        total_plantillas = plantillas.count()
        plantillas_activas = plantillas.filter(is_active=True).count()
        plantillas_default = plantillas.filter(is_default=True).count()
        
        # Contar partes generados si el modelo está disponible
        total_partes_generados = 0
        if ParteMortorioGenerado is not None:
            total_partes_generados = ParteMortorioGenerado.objects.count()
        
        context = {
            'plantillas': plantillas,
            'total_plantillas': total_plantillas,
            'plantillas_activas': plantillas_activas,
            'plantillas_default': plantillas_default,
            'total_partes_generados': total_partes_generados,
        }
        
        return render(request, 'custom_admin/parte_mortorios/plantillas_list.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en plantillas_parte_mortorio_list: {str(e)}")
        
        # Fallback en caso de error
        context = {
            'plantillas': [],
            'total_plantillas': 0,
            'plantillas_activas': 0,
            'plantillas_default': 0,
            'total_partes_generados': 0,
            'mensaje_error': f'Error al cargar las plantillas: {str(e)}'
        }
        return render(request, 'custom_admin/parte_mortorios/plantillas_list.html', context)
@login_required
@user_passes_test(is_admin)
def plantilla_parte_mortorio_detalle_api(request, id):
    """API para obtener detalles de una plantilla de parte mortorio"""
    try:
        plantilla = PlantillaParteMortorio.objects.get(pk=id)
        
        data = {
            'id': plantilla.id,
            'nombre': plantilla.nombre,
            'tipo_parte': plantilla.tipo_parte,
            'tipo_parte_display': plantilla.get_tipo_parte_display(),
            'version': plantilla.version,
            'descripcion': plantilla.descripcion or '',
            'is_active': plantilla.is_active,
            'is_default': plantilla.is_default,
            'instrucciones': plantilla.instrucciones or '',
            'archivo_plantilla': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None,
            'created_by': plantilla.created_by.username if plantilla.created_by else None,
            'created_at': plantilla.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': plantilla.updated_at.strftime('%d/%m/%Y %H:%M'),
            'partes_count': plantilla.partes_generados.count(),
            'variables_disponibles': plantilla.variables_disponibles
        }
        
        return JsonResponse(data)
    except PlantillaParteMortorio.DoesNotExist:
        return JsonResponse({'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def plantilla_parte_mortorio_crear_api(request):
    """API para crear una plantilla de parte mortorio"""
    try:
        nombre = request.POST.get('nombre')
        tipo_parte = request.POST.get('tipo_parte')
        version = request.POST.get('version', '1.0')
        descripcion = request.POST.get('descripcion', '')
        is_active = request.POST.get('is_active') == 'true'
        is_default = request.POST.get('is_default') == 'false'
        instrucciones = request.POST.get('instrucciones', '')
        archivo_plantilla = request.FILES.get('archivo_plantilla')
        
        # Validaciones
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre es obligatorio'
            }, status=400)
        
        if not tipo_parte:
            return JsonResponse({
                'success': False,
                'error': 'El tipo de parte es obligatorio'
            }, status=400)
        
        if not archivo_plantilla:
            return JsonResponse({
                'success': False,
                'error': 'El archivo de plantilla es obligatorio'
            }, status=400)
        
        # Validar que sea archivo .docx
        if not archivo_plantilla.name.endswith('.docx'):
            return JsonResponse({
                'success': False,
                'error': 'Solo se permiten archivos .docx'
            }, status=400)
        
        # Validar tamaño (máx 10MB)
        if archivo_plantilla.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'El archivo no debe superar los 10MB'
            }, status=400)
        
        # Si se marca como default, desmarcar las demás del mismo tipo
        if is_default:
            PlantillaParteMortorio.objects.filter(
                tipo_parte=tipo_parte,
                is_default=True
            ).update(is_default=False)
        
        # Crear la plantilla
        plantilla = PlantillaParteMortorio.objects.create(
            nombre=nombre,
            tipo_parte=tipo_parte,
            version=version,
            descripcion=descripcion,
            is_active=is_active,
            is_default=is_default,
            instrucciones=instrucciones,
            archivo_plantilla=archivo_plantilla,
            created_by=request.user
        )
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(plantilla).pk,
            object_id=plantilla.pk,
            object_repr=str(plantilla.nombre),
            action_flag=ADDITION,
            change_message=f'Plantilla de parte mortorio creada: {plantilla.nombre} - Tipo: {plantilla.get_tipo_parte_display()}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla creada exitosamente',
            'id': plantilla.id
        })
        
    except Exception as e:
        import traceback
        print("ERROR al crear plantilla:", traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al crear la plantilla: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["PUT", "POST"])
def plantilla_parte_mortorio_actualizar_api(request, id):
    """API para actualizar una plantilla de parte mortorio"""
    try:
        plantilla = PlantillaParteMortorio.objects.get(pk=id)
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            nombre = data.get('nombre', plantilla.nombre)
            tipo_parte = data.get('tipo_parte', plantilla.tipo_parte)
            version = data.get('version', plantilla.version)
            descripcion = data.get('descripcion', plantilla.descripcion)
            is_active = data.get('is_active', plantilla.is_active)
            is_default = data.get('is_default', plantilla.is_default)
            instrucciones = data.get('instrucciones', plantilla.instrucciones)
            archivo_plantilla = None
        else:
            nombre = request.POST.get('nombre', plantilla.nombre)
            tipo_parte = request.POST.get('tipo_parte', plantilla.tipo_parte)
            version = request.POST.get('version', plantilla.version)
            descripcion = request.POST.get('descripcion', plantilla.descripcion)
            is_active = request.POST.get('is_active') == 'true'
            is_default = request.POST.get('is_default') == 'true'
            instrucciones = request.POST.get('instrucciones', plantilla.instrucciones)
            archivo_plantilla = request.FILES.get('archivo_plantilla')
        
        # Si se marca como default, desmarcar las demás del mismo tipo
        if is_default and not plantilla.is_default:
            PlantillaParteMortorio.objects.filter(
                tipo_parte=plantilla.tipo_parte,
                is_default=True
            ).exclude(pk=id).update(is_default=False)
        
        plantilla.nombre = nombre
        plantilla.tipo_parte = tipo_parte
        plantilla.version = version
        plantilla.descripcion = descripcion
        plantilla.is_active = is_active
        plantilla.is_default = is_default
        plantilla.instrucciones = instrucciones
        
        if archivo_plantilla:
            plantilla.archivo_plantilla = archivo_plantilla
        
        plantilla.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla actualizada exitosamente'
        })
        
    except PlantillaParteMortorio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def plantilla_parte_mortorio_eliminar_api(request, id):
    """API para eliminar una plantilla de parte mortorio"""
    try:
        plantilla = PlantillaParteMortorio.objects.get(pk=id)
        
        # Verificar si tiene partes generados
        if plantilla.partes_generados.exists():
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar la plantilla porque tiene partes generados asociados'
            }, status=400)
        
        plantilla.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Plantilla eliminada exitosamente'
        })
    except PlantillaParteMortorio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def plantilla_parte_mortorio_marcar_default_api(request, id):
    """API para marcar una plantilla como predeterminada"""
    try:
        plantilla = PlantillaParteMortorio.objects.get(pk=id)
        
        # Desmarcar todas las demás plantillas del mismo tipo como default
        PlantillaParteMortorio.objects.filter(
            tipo_parte=plantilla.tipo_parte,
            is_default=True
        ).exclude(pk=id).update(is_default=False)
        
        # Marcar esta plantilla como default
        plantilla.is_default = True
        plantilla.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Plantilla "{plantilla.nombre}" marcada como predeterminada'
        })
        
    except PlantillaParteMortorio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def plantilla_parte_mortorio_descargar_api(request, id):
    """API para descargar el archivo de plantilla"""
    try:
        from django.http import FileResponse
        import os
        
        plantilla = PlantillaParteMortorio.objects.get(pk=id)
        
        if not plantilla.archivo_plantilla:
            return JsonResponse({
                'success': False,
                'error': 'La plantilla no tiene un archivo adjunto'
            }, status=404)
        
        file_name = os.path.basename(plantilla.archivo_plantilla.name)
        response = FileResponse(
            plantilla.archivo_plantilla.open('rb'),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        return response
        
    except PlantillaParteMortorio.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Plantilla no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ==================== APIs PARA GENERAR PARTES MORTORIOS ====================

@login_required
@user_passes_test(is_admin)
def api_plantillas_parte_mortorio(request):
    """API para obtener todas las plantillas de parte mortorio activas"""
    try:
        plantillas = PlantillaParteMortorio.objects.filter(is_active=True).order_by('-is_default', 'nombre')
        
        data = []
        for plantilla in plantillas:
            data.append({
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'tipo_parte': plantilla.tipo_parte,
                'tipo_parte_display': plantilla.get_tipo_parte_display(),
                'version': plantilla.version,
                'is_default': plantilla.is_default,
                'descripcion': plantilla.descripcion or '',
                'archivo_url': plantilla.archivo_plantilla.url if plantilla.archivo_plantilla else None
            })
        
        return JsonResponse({'success': True, 'plantillas': data})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_generar_api(request, parte_id):
    """API para generar parte mortorio desde plantilla"""
    try:
        parte_mortorio = get_object_or_404(ParteMortorio, pk=parte_id)
        data = json.loads(request.body)
        
        plantilla_id = data.get('plantilla_id')
        
        if not plantilla_id:
            return JsonResponse({
                'success': False,
                'error': 'Plantilla requerida'
            }, status=400)
        
        try:
            plantilla = PlantillaParteMortorio.objects.get(id=plantilla_id, is_active=True)
        except PlantillaParteMortorio.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Plantilla no encontrada o no activa'
            }, status=404)
        
        # Crear parte generado
        parte_generado = ParteMortorioGenerado.objects.create(
            parte_mortorio=parte_mortorio,
            plantilla_usada=plantilla,
            generado_por=request.user,
            estado='borrador'
        )
        
        # Generar el PDF
        if parte_generado.generar_parte_pdf():
            return JsonResponse({
                'success': True,
                'message': 'Parte mortorio generado exitosamente',
                'parte_generado_id': parte_generado.id,
                'numero_parte': parte_generado.numero_parte,
                'archivo_url': parte_generado.archivo_parte_pdf.url if parte_generado.archivo_parte_pdf else None
            })
        else:
            parte_generado.delete()
            return JsonResponse({
                'success': False,
                'error': 'Error al generar el archivo del parte mortorio'
            }, status=500)
        
    except Exception as e:
        import traceback
        print("ERROR al generar parte mortorio:", traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Error al generar el parte mortorio: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
def parte_mortorio_verificar_api(request, parte_generado_id):
    """API para verificar si un parte ya fue generado"""
    try:
        parte_generado = ParteMortorioGenerado.objects.get(pk=parte_generado_id)
        
        return JsonResponse({
            'success': True,
            'archivo_url': parte_generado.archivo_parte_pdf.url if parte_generado.archivo_parte_pdf else None,
            'numero_parte': parte_generado.numero_parte,
            'estado': parte_generado.estado
        })
    
    except ParteMortorioGenerado.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Parte no generado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def parte_mortorio_descargar_api(request, parte_generado_id):
    """Descargar parte generado"""
    try:
        parte_generado = get_object_or_404(ParteMortorioGenerado, pk=parte_generado_id)
        
        if not parte_generado.archivo_parte_pdf:
            messages.error(request, 'El parte no ha sido generado aún.')
            return redirect('custom_admin:parte_mortorios_list')
        
        response = FileResponse(
            parte_generado.archivo_parte_pdf.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="Parte_Mortorio_{parte_generado.numero_parte}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al descargar el parte: {str(e)}')
        return redirect('custom_admin:parte_mortorios_list')
# ==================== VISTAS DE REPORTES DE CONTRATOS ====================
@login_required
@user_passes_test(is_admin)
def reports_dashboard_contratos(request):
    """Dashboard principal de contratos - ACTUALIZADO con gráficas Plotly"""
    
    # Verificar disponibilidad de modelos
    if not CONTENT_MODELS_AVAILABLE:
        context = {
            'error': 'Módulo de Contratos no disponible',
            'mensaje': 'No se pueden cargar los reportes en este momento.',
            'models_available': False,
            'total_contratos': 0,
            'contratos_activos': 0,
            'contratos_pendientes': 0,
            'contratos_por_vencer': 0,
            'contratos_vencidos': 0,
            'contratos_cancelados': 0,
            'ingresos_totales': Decimal('0.00'),
            'ingresos_activos': Decimal('0.00'),
            'contratos_recientes': [],
            'grafica_pastel_html': '',
            'grafica_barras_html': '',
        }
        return render(request, 'custom_admin/reports/contratos/list.html', context)
    
    try:
        hoy = timezone.now().date()
        
        # Contratos por estado con manejo de errores
        try:
            total_contratos = ContratoGenerado.objects.count()
        except Exception as e:
            print(f"❌ Error contando contratos: {e}")
            total_contratos = 0
        
        # ✅ CORREGIDO: Contratos "activos" son los que tienen estado 'validado' (con cuñas)
        try:
            contratos_activos = ContratoGenerado.objects.filter(estado='validado').count()
        except Exception as e:
            print(f"❌ Error contando contratos activos: {e}")
            contratos_activos = 0
        
        # ✅ CORREGIDO: Contratos pendientes son los que tienen estado 'generado'
        try:
            contratos_pendientes = ContratoGenerado.objects.filter(estado='generado').count()
        except Exception as e:
            print(f"❌ Error contando contratos pendientes: {e}")
            contratos_pendientes = 0
        
        # ✅ CORREGIDO: Contratos por vencer (validados que están cerca de vencer)
        try:
            fecha_limite_vencimiento = hoy + timedelta(days=30)
            contratos_por_vencer = ContratoGenerado.objects.filter(
                estado='validado',  # Solo los validados pueden vencer
                cuña__fecha_fin__lte=fecha_limite_vencimiento,
                cuña__fecha_fin__gte=hoy
            ).count()
        except Exception as e:
            print(f"❌ Error contando contratos por vencer: {e}")
            contratos_por_vencer = 0
        
        # ✅ CORREGIDO: Contratos vencidos (validados cuya fecha fin ya pasó)
        try:
            contratos_vencidos = ContratoGenerado.objects.filter(
                estado='validado',  # Solo los validados pueden estar vencidos
                cuña__fecha_fin__lt=hoy
            ).count()
        except Exception as e:
            print(f"❌ Error contando contratos vencidos: {e}")
            contratos_vencidos = 0
        
        # ✅ CORREGIDO: Contratos cancelados
        try:
            contratos_cancelados = ContratoGenerado.objects.filter(estado='cancelado').count()
        except Exception as e:
            print(f"❌ Error contando contratos cancelados: {e}")
            contratos_cancelados = 0
        
        # Ingresos con manejo de errores
        try:
            ingresos_totales_result = ContratoGenerado.objects.aggregate(
                total=Sum('valor_total')
            )
            ingresos_totales = ingresos_totales_result['total'] or Decimal('0.00')
        except Exception as e:
            print(f"❌ Error calculando ingresos totales: {e}")
            ingresos_totales = Decimal('0.00')
        
        # ✅ CORREGIDO: Ingresos de contratos validados (activos)
        try:
            ingresos_activos_result = ContratoGenerado.objects.filter(estado='validado').aggregate(
                total=Sum('valor_total')
            )
            ingresos_activos = ingresos_activos_result['total'] or Decimal('0.00')
        except Exception as e:
            print(f"❌ Error calculando ingresos activos: {e}")
            ingresos_activos = Decimal('0.00')
        
        # ✅ CORREGIDO: Ingresos de contratos pendientes
        try:
            ingresos_pendientes_result = ContratoGenerado.objects.filter(estado='generado').aggregate(
                total=Sum('valor_total')
            )
            ingresos_pendientes = ingresos_pendientes_result['total'] or Decimal('0.00')
        except Exception as e:
            print(f"❌ Error calculando ingresos pendientes: {e}")
            ingresos_pendientes = Decimal('0.00')
        
        # Contratos recientes
        try:
            contratos_recientes = ContratoGenerado.objects.select_related(
                'cliente', 'cuña', 'plantilla_usada'
            ).order_by('-fecha_generacion')[:10]
            
            # Asegurarnos de que cada contrato tenga el método get_estado_display
            for contrato in contratos_recientes:
                if not hasattr(contrato, 'get_estado_display'):
                    contrato.get_estado_display = lambda: dict(ContratoGenerado.ESTADO_CHOICES).get(contrato.estado, contrato.estado)
                    
        except Exception as e:
            print(f"❌ Error obteniendo contratos recientes: {e}")
            contratos_recientes = []
        
        # ==================== GRÁFICAS CON PLOTLY ====================
        
        # 1. Gráfico de pastel - Contratos por Estado
        datos_estados = {
            'Estado': ['Validados', 'Pendientes', 'Por Vencer', 'Vencidos', 'Cancelados'],
            'Cantidad': [contratos_activos, contratos_pendientes, contratos_por_vencer, contratos_vencidos, contratos_cancelados]
        }
        
        fig_pastel = px.pie(
            datos_estados,
            values='Cantidad',
            names='Estado',
            title='Contratos por Estado',
            color='Estado',
            color_discrete_map={
                'Validados': '#28a745',
                'Pendientes': '#ffc107',
                'Por Vencer': '#17a2b8', 
                'Vencidos': '#dc3545',
                'Cancelados': '#6c757d'
            }
        )
        
        fig_pastel.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}'
        )
        
        fig_pastel.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )
        
        # 2. Gráfico de barras - Ingresos Mensuales (últimos 6 meses)
        ingresos_mensuales = []
        meses_nombres = []
        
        try:
            for i in range(5, -1, -1):
                mes_fecha = hoy - timedelta(days=30*i)
                mes_str = mes_fecha.strftime('%Y-%m')
                mes_nombre = mes_fecha.strftime('%b %Y')
                
                # Calcular ingresos del mes
                ingresos_mes_result = ContratoGenerado.objects.filter(
                    fecha_generacion__year=mes_fecha.year,
                    fecha_generacion__month=mes_fecha.month
                ).aggregate(total=Sum('valor_total'))
                
                ingresos_mes = ingresos_mes_result['total'] or Decimal('0.00')
                
                ingresos_mensuales.append(float(ingresos_mes))
                meses_nombres.append(mes_nombre)
                
        except Exception as e:
            print(f"❌ Error calculando ingresos mensuales: {e}")
            # Datos de ejemplo en caso de error
            for i in range(6):
                ingresos_mensuales.append(0)
                meses_nombres.append(f'Mes {i+1}')
        
        datos_ingresos = {
            'Mes': meses_nombres,
            'Ingresos': ingresos_mensuales
        }
        
        fig_barras = px.bar(
            datos_ingresos,
            x='Mes',
            y='Ingresos',
            title='Ingresos Mensuales',
            color='Ingresos',
            color_continuous_scale='Blues'
        )
        
        fig_barras.update_traces(
            hovertemplate='<b>%{x}</b><br>Ingresos: $%{y:,.2f}'
        )
        
        fig_barras.update_layout(
            height=400,
            xaxis_title="Mes",
            yaxis_title="Ingresos ($)",
            coloraxis_showscale=False
        )
        
        # Formatear ejes
        fig_barras.update_yaxes(tickprefix="$", tickformat=",.")
        
        # Convertir gráficas a HTML
        grafica_pastel_html = pyo.plot(fig_pastel, output_type='div', include_plotlyjs=False)
        grafica_barras_html = pyo.plot(fig_barras, output_type='div', include_plotlyjs=False)
        
        context = {
            'total_contratos': total_contratos,
            'contratos_activos': contratos_activos,
            'contratos_pendientes': contratos_pendientes,
            'contratos_por_vencer': contratos_por_vencer,
            'contratos_vencidos': contratos_vencidos,
            'contratos_cancelados': contratos_cancelados,
            'ingresos_totales': ingresos_totales,
            'ingresos_activos': ingresos_activos,
            'ingresos_pendientes': ingresos_pendientes,
            'contratos_recientes': contratos_recientes,
            'grafica_pastel_html': grafica_pastel_html,
            'grafica_barras_html': grafica_barras_html,
            'models_available': True,
        }
        
        print(f"✅ Dashboard de Reportes cargado exitosamente:")
        print(f"   - Total contratos: {total_contratos}")
        print(f"   - Activos (validados): {contratos_activos}")
        print(f"   - Pendientes (generados): {contratos_pendientes}")
        print(f"   - Por vencer: {contratos_por_vencer}")
        print(f"   - Vencidos: {contratos_vencidos}")
        print(f"   - Cancelados: {contratos_cancelados}")
        print(f"   - Ingresos totales: {ingresos_totales}")
        print(f"   - Ingresos activos: {ingresos_activos}")
        print(f"   - Ingresos pendientes: {ingresos_pendientes}")
        print(f"   - Contratos recientes: {len(contratos_recientes)}")
        
        return render(request, 'custom_admin/reports/contratos/list.html', context)
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO en reports_dashboard_contratos: {e}")
        import traceback
        traceback.print_exc()
        
        context = {
            'error': 'Error al cargar el dashboard',
            'mensaje': str(e),
            'models_available': False,
            'total_contratos': 0,
            'contratos_activos': 0,
            'contratos_pendientes': 0,
            'contratos_por_vencer': 0,
            'contratos_vencidos': 0,
            'contratos_cancelados': 0,
            'ingresos_totales': Decimal('0.00'),
            'ingresos_activos': Decimal('0.00'),
            'ingresos_pendientes': Decimal('0.00'),
            'contratos_recientes': [],
            'grafica_pastel_html': '',
            'grafica_barras_html': '',
        }
        return render(request, 'custom_admin/reports/contratos/list.html', context)
@login_required
@user_passes_test(is_admin)
def reports_api_estadisticas_contratos(request):
    hoy = timezone.now().date()
    # Contratos por estado (puedes ajustar la lista de estados si necesitas)
    contratos_por_estado = list(
        ContratoGenerado.objects.values('estado').annotate(total=Count('id')).order_by('estado')
    )

    # Ingresos por mes (últimos 6 meses)
    ingresos_mensuales = []
    for i in range(5, -1, -1):
        mes_fecha = hoy - timezone.timedelta(days=30 * i)
        mes_nombre = mes_fecha.strftime('%Y-%m')
        ingreso_mes = (
            ContratoGenerado.objects
            .filter(fecha_generacion__year=mes_fecha.year, fecha_generacion__month=mes_fecha.month)
            .aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        )
        ingresos_mensuales.append({'mes': mes_nombre, 'ingresos': float(ingreso_mes)})

    # DEVOLVER claves TAL CUAL espera tu frontend
    return JsonResponse({
        'success': True,
        'contratosporestado': contratos_por_estado,
        'ingresosmensuales': ingresos_mensuales
    })
@login_required
@user_passes_test(is_admin)
def reports_vencimiento_contratos(request):
    """Genera reporte de contratos por vencimiento - CON MANEJO DE ERRORES"""
    
    if not CONTENT_MODELS_AVAILABLE:
        messages.error(request, 'Módulo de Contratos no disponible')
        return redirect('custom_admin:reports_dashboard_contratos')
    
    try:
        hoy = timezone.now().date()
        dias_aviso = int(request.GET.get('dias_aviso', 30))
        formato = request.GET.get('formato', 'html')
        
        fecha_limite = hoy + timedelta(days=dias_aviso)
        
        # Contratos por vencer
        try:
            contratos_por_vencer = ContratoGenerado.objects.filter(
                estado='activo',
                cuña__fecha_fin__lte=fecha_limite,
                cuña__fecha_fin__gte=hoy
            ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
        except Exception as e:
            print(f"❌ Error obteniendo contratos por vencer: {e}")
            contratos_por_vencer = []
        
        # Contratos vencidos
        try:
            contratos_vencidos = ContratoGenerado.objects.filter(
                estado='activo',
                cuña__fecha_fin__lt=hoy
            ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
        except Exception as e:
            print(f"❌ Error obteniendo contratos vencidos: {e}")
            contratos_vencidos = []
        
        # Contratos con buena vigencia
        try:
            contratos_vigentes = ContratoGenerado.objects.filter(
                estado='activo',
                cuña__fecha_fin__gt=fecha_limite
            ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
        except Exception as e:
            print(f"❌ Error obteniendo contratos vigentes: {e}")
            contratos_vigentes = []
        
        # Exportar si se solicita
        if formato == 'csv':
            return _generar_reporte_csv_vencimiento(contratos_por_vencer, contratos_vencidos, contratos_vigentes)
        elif formato == 'excel':
            return _generar_reporte_excel_vencimiento(contratos_por_vencer, contratos_vencidos, contratos_vigentes)
        
        context = {
            'contratos_por_vencer': contratos_por_vencer,
            'contratos_vencidos': contratos_vencidos,
            'contratos_vigentes': contratos_vigentes,
            'dias_aviso': dias_aviso,
            'fecha_limite': fecha_limite,
            'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        return render(request, 'custom_admin/reports/vencimiento_contratos.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en reports_vencimiento_contratos: {e}")
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('custom_admin:reports_dashboard_contratos')

@login_required
@user_passes_test(is_admin)
def reports_ingresos_contratos(request):
    """Genera reporte de ingresos por contratos - CON MANEJO DE ERRORES"""
    
    if not CONTENT_MODELS_AVAILABLE:
        messages.error(request, 'Módulo de Contratos no disponible')
        return redirect('custom_admin:reports_dashboard_contratos')
    
    try:
        # Parámetros
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        agrupar_por = request.GET.get('agrupar_por', 'mes')
        formato = request.GET.get('formato', 'html')
        
        # Base query
        contratos = ContratoGenerado.objects.select_related('cliente', 'cuña').all()
        
        if fecha_inicio:
            contratos = contratos.filter(fecha_generacion__date__gte=fecha_inicio)
        if fecha_fin:
            contratos = contratos.filter(fecha_generacion__date__lte=fecha_fin)
        
        # Agrupar datos
        ingresos_data = []
        try:
            if agrupar_por == 'mes':
                # Para PostgreSQL
                ingresos_data = contratos.extra(
                    select={'periodo': "TO_CHAR(fecha_generacion, 'YYYY-MM')"}
                ).values('periodo').annotate(
                    total_contratos=Count('id'),
                    ingresos_totales=Sum('valor_total'),
                    promedio_contrato=Avg('valor_total')
                ).order_by('periodo')
            elif agrupar_por == 'estado':
                ingresos_data = contratos.values('estado').annotate(
                    total_contratos=Count('id'),
                    ingresos_totales=Sum('valor_total'),
                    promedio_contrato=Avg('valor_total')
                ).order_by('estado')
            elif agrupar_por == 'cliente':
                ingresos_data = contratos.values('cliente__empresa', 'cliente__ruc_dni').annotate(
                    total_contratos=Count('id'),
                    ingresos_totales=Sum('valor_total'),
                    promedio_contrato=Avg('valor_total')
                ).order_by('-ingresos_totales')
        except Exception as e:
            print(f"❌ Error agrupando datos: {e}")
            # Datos vacíos en caso de error
            ingresos_data = []
        
        # Exportar si se solicita
        if formato == 'csv':
            return _generar_reporte_csv_ingresos(ingresos_data, agrupar_por)
        elif formato == 'excel':
            return _generar_reporte_excel_ingresos(ingresos_data, agrupar_por)
        
        context = {
            'ingresos_data': ingresos_data,
            'agrupar_por': agrupar_por,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_ingresos': contratos.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00'),
            'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        return render(request, 'custom_admin/reports/ingresos_contratos.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en reports_ingresos_contratos: {e}")
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('custom_admin:reports_dashboard_contratos')

# ==================== FUNCIONES AUXILIARES PARA EXPORTACIÓN ====================

def _generar_reporte_csv_estado(contratos_por_estado, detalle_estados):
    """Genera reporte CSV para estado de contratos"""
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_estado_contratos.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Reporte de Contratos por Estado', datetime.now().strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        writer.writerow(['Estado', 'Cantidad', 'Valor Total'])
        
        for item in contratos_por_estado:
            writer.writerow([
                dict(ContratoGenerado.ESTADO_CHOICES).get(item['estado'], item['estado']),
                item['total'],
                item['valor_total']
            ])
        
        return response
    except Exception as e:
        print(f"❌ Error generando CSV: {e}")
        return HttpResponse("Error al generar el archivo CSV")

def _generar_reporte_csv_vencimiento(por_vencer, vencidos, vigentes):
    """Genera reporte CSV para vencimiento de contratos"""
    try:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_vencimiento_contratos.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Reporte de Contratos por Vencimiento', datetime.now().strftime('%d/%m/%Y %H:%M')])
        writer.writerow([])
        
        # Contratos por vencer
        writer.writerow(['CONTRATOS POR VENCER'])
        writer.writerow(['Código', 'Cliente', 'Fecha Fin', 'Días Restantes', 'Valor'])
        for contrato in por_vencer:
            dias_restantes = (contrato.cuña.fecha_fin - timezone.now().date()).days
            writer.writerow([
                contrato.numero_contrato,
                contrato.nombre_cliente,
                contrato.cuña.fecha_fin.strftime('%d/%m/%Y'),
                dias_restantes,
                contrato.valor_total
            ])
        
        writer.writerow([])
        
        # Contratos vencidos
        writer.writerow(['CONTRATOS VENCIDOS'])
        writer.writerow(['Código', 'Cliente', 'Fecha Fin', 'Días Vencidos', 'Valor'])
        for contrato in vencidos:
            dias_vencidos = (timezone.now().date() - contrato.cuña.fecha_fin).days
            writer.writerow([
                contrato.numero_contrato,
                contrato.nombre_cliente,
                contrato.cuña.fecha_fin.strftime('%d/%m/%Y'),
                dias_vencidos,
                contrato.valor_total
            ])
        
        return response
    except Exception as e:
        print(f"❌ Error generando CSV vencimiento: {e}")
        return HttpResponse("Error al generar el archivo CSV")
# ==================== REPORTES DE CONTRATOS - FUNCIONES FALTANTES ====================

@login_required
@user_passes_test(is_admin)
def reports_estado_contratos(request):
    """Genera reporte de contratos por estado - CON MANEJO DE ERRORES"""
    
    if not CONTENT_MODELS_AVAILABLE:
        messages.error(request, 'Módulo de Contratos no disponible')
        return redirect('custom_admin:reports_dashboard_contratos')
    
    try:
        # Parámetros del reporte
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        formato = request.GET.get('formato', 'html')
        
        # Filtrar contratos
        contratos = ContratoGenerado.objects.select_related(
            'cliente', 'cuña', 'plantilla_usada'
        ).all()
        
        if fecha_inicio:
            contratos = contratos.filter(fecha_generacion__date__gte=fecha_inicio)
        if fecha_fin:
            contratos = contratos.filter(fecha_generacion__date__lte=fecha_fin)
        
        # Agrupar por estado
        try:
            contratos_por_estado = contratos.values('estado').annotate(
                total=Count('id'),
                valor_total=Sum('valor_total')
            ).order_by('estado')
        except Exception as e:
            print(f"❌ Error agrupando por estado: {e}")
            contratos_por_estado = []
        
        # Detalle por estado
        detalle_estados = {}
        estados = ['borrador', 'generado', 'enviado', 'firmado', 'validado', 'vencido', 'cancelado']
        
        for estado in estados:
            try:
                detalle_estados[estado] = list(contratos.filter(estado=estado))
            except Exception as e:
                print(f"❌ Error obteniendo detalle para estado {estado}: {e}")
                detalle_estados[estado] = []
        
        # Exportar si se solicita
        if formato == 'csv':
            return _generar_reporte_csv_estado(contratos_por_estado, detalle_estados)
        elif formato == 'excel':
            return _generar_reporte_excel_estado(contratos_por_estado, detalle_estados)
        
        context = {
            'contratos_por_estado': contratos_por_estado,
            'detalle_estados': detalle_estados,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_contratos': contratos.count(),
            'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        return render(request, 'custom_admin/reports/contratos/estado.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en reports_estado_contratos: {e}")
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('custom_admin:reports_dashboard_contratos')

@login_required
@user_passes_test(is_admin)
def reports_vencimiento_contratos(request):
    """Genera reporte de contratos por vencimiento - CON MANEJO DE ERRORES"""
    
    if not CONTENT_MODELS_AVAILABLE:
        messages.error(request, 'Módulo de Contratos no disponible')
        return redirect('custom_admin:reports_dashboard_contratos')
    
    try:
        hoy = timezone.now().date()
        dias_aviso = int(request.GET.get('dias_aviso', 30))
        formato = request.GET.get('formato', 'html')
        
        fecha_limite = hoy + timedelta(days=dias_aviso)
        
        # Contratos por vencer (solo los validados pueden vencer)
        try:
            contratos_por_vencer = ContratoGenerado.objects.filter(
                estado='validado',  # Solo contratos validados pueden vencer
                cuña__fecha_fin__lte=fecha_limite,
                cuña__fecha_fin__gte=hoy
            ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
        except Exception as e:
            print(f"❌ Error obteniendo contratos por vencer: {e}")
            contratos_por_vencer = []
        
        # Contratos vencidos (solo los validados pueden estar vencidos)
        try:
            contratos_vencidos = ContratoGenerado.objects.filter(
                estado='validado',  # Solo contratos validados pueden estar vencidos
                cuña__fecha_fin__lt=hoy
            ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
        except Exception as e:
            print(f"❌ Error obteniendo contratos vencidos: {e}")
            contratos_vencidos = []
        
        # Contratos con buena vigencia
        try:
            contratos_vigentes = ContratoGenerado.objects.filter(
                estado='validado',  # Solo contratos validados están vigentes
                cuña__fecha_fin__gt=fecha_limite
            ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
        except Exception as e:
            print(f"❌ Error obteniendo contratos vigentes: {e}")
            contratos_vigentes = []
        
        # Exportar si se solicita
        if formato == 'csv':
            return _generar_reporte_csv_vencimiento(contratos_por_vencer, contratos_vencidos, contratos_vigentes)
        elif formato == 'excel':
            return _generar_reporte_excel_vencimiento(contratos_por_vencer, contratos_vencidos, contratos_vigentes)
        
        context = {
            'contratos_por_vencer': contratos_por_vencer,
            'contratos_vencidos': contratos_vencidos,
            'contratos_vigentes': contratos_vigentes,
            'dias_aviso': dias_aviso,
            'fecha_limite': fecha_limite,
            'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        return render(request, 'custom_admin/reports/contratos/vencimiento.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en reports_vencimiento_contratos: {e}")
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('custom_admin:reports_dashboard_contratos')

@login_required
@user_passes_test(is_admin)
def reports_ingresos_contratos(request):
    """Genera reporte de ingresos por contratos - CON MANEJO DE ERRORES"""
    
    if not CONTENT_MODELS_AVAILABLE:
        messages.error(request, 'Módulo de Contratos no disponible')
        return redirect('custom_admin:reports_dashboard_contratos')
    
    try:
        # Parámetros
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        agrupar_por = request.GET.get('agrupar_por', 'mes')
        formato = request.GET.get('formato', 'html')
        
        # Base query
        contratos = ContratoGenerado.objects.select_related('cliente', 'cuña').all()
        
        if fecha_inicio:
            contratos = contratos.filter(fecha_generacion__date__gte=fecha_inicio)
        if fecha_fin:
            contratos = contratos.filter(fecha_generacion__date__lte=fecha_fin)
        
        # Agrupar datos
        ingresos_data = []
        try:
            if agrupar_por == 'mes':
                # Agrupar por mes usando annotate
                from django.db.models.functions import TruncMonth
                ingresos_data = contratos.annotate(
                    mes=TruncMonth('fecha_generacion')
                ).values('mes').annotate(
                    total_contratos=Count('id'),
                    ingresos_totales=Sum('valor_total'),
                    promedio_contrato=Avg('valor_total')
                ).order_by('mes')
                
                # Formatear meses
                for item in ingresos_data:
                    item['periodo'] = item['mes'].strftime('%Y-%m')
                    
            elif agrupar_por == 'estado':
                ingresos_data = contratos.values('estado').annotate(
                    total_contratos=Count('id'),
                    ingresos_totales=Sum('valor_total'),
                    promedio_contrato=Avg('valor_total')
                ).order_by('estado')
            elif agrupar_por == 'cliente':
                ingresos_data = contratos.values('cliente__empresa', 'cliente__ruc_dni').annotate(
                    total_contratos=Count('id'),
                    ingresos_totales=Sum('valor_total'),
                    promedio_contrato=Avg('valor_total')
                ).order_by('-ingresos_totales')
        except Exception as e:
            print(f"❌ Error agrupando datos: {e}")
            # Datos vacíos en caso de error
            ingresos_data = []
        
        # Exportar si se solicita
        if formato == 'csv':
            return _generar_reporte_csv_ingresos(ingresos_data, agrupar_por)
        elif formato == 'excel':
            return _generar_reporte_excel_ingresos(ingresos_data, agrupar_por)
        
        context = {
            'ingresos_data': ingresos_data,
            'agrupar_por': agrupar_por,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_ingresos': contratos.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00'),
            'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
        }
        
        return render(request, 'custom_admin/reports/contratos/ingresos.html', context)
        
    except Exception as e:
        print(f"❌ ERROR en reports_ingresos_contratos: {e}")
        messages.error(request, f'Error al generar el reporte: {str(e)}')
        return redirect('custom_admin:reports_dashboard_contratos')
