from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import JsonResponse
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

def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_superuser or user.is_staff or getattr(user, 'rol', None) == 'admin'

# ==================== VISTAS DE ÓRDENES ====================

@login_required
@user_passes_test(is_admin)
def ordenes_toma_list(request):
    """Lista de órdenes de toma"""
    context = {
        'title': 'Órdenes de Toma',
        'header_title': 'Gestión de Órdenes de Toma',
        'description': 'Administre las órdenes de toma de audio publicitario'
    }
    return render(request, 'custom_admin/orders/list.html', context)

@login_required
@user_passes_test(is_admin)
def ordenes_produccion_list(request):
    """Lista de órdenes de producción"""
    context = {
        'title': 'Órdenes de Producción',
        'header_title': 'Gestión de Órdenes de Producción',
        'description': 'Administre las órdenes de producción de contenido'
    }
    return render(request, 'custom_admin/ordenes/produccion_list.html', context)

@login_required
@user_passes_test(is_admin)
def ordenes_finalizacion_list(request):
    """Lista de órdenes de finalización"""
    context = {
        'title': 'Órdenes de Finalización',
        'header_title': 'Gestión de Órdenes de Finalización',
        'description': 'Administre las órdenes de finalización de proyectos'
    }
    return render(request, 'custom_admin/ordenes/finalizacion_list.html', context)

# ==================== VISTAS DE PANTEONES ====================

@login_required
@user_passes_test(is_admin)
def panteones_list(request):
    """Lista de panteones"""
    context = {
        'title': 'Gestión de Panteones',
        'header_title': 'Gestión de Panteones',
        'description': 'Administre los panteones del sistema'
    }
    return render(request, 'custom_admin/parte_mortorios/list.html', context)

# ==================== APIs PARA ÓRDENES ====================

@login_required
@user_passes_test(is_admin)
def api_ordenes_toma(request):
    """API para obtener órdenes de toma"""
    try:
        # Datos de ejemplo - reemplazar con tu modelo real
        ordenes = [
            {
                'id': 1,
                'numero_orden': 'OT-001',
                'cliente': 'Cliente Ejemplo 1',
                'fecha_solicitud': '2024-01-15',
                'estado': 'pendiente',
                'prioridad': 'alta',
                'descripcion': 'Toma de audio para spot comercial'
            },
            {
                'id': 2,
                'numero_orden': 'OT-002',
                'cliente': 'Cliente Ejemplo 2',
                'fecha_solicitud': '2024-01-16',
                'estado': 'en_proceso',
                'prioridad': 'media',
                'descripcion': 'Toma de voz para cuña informativa'
            }
        ]
        
        return JsonResponse({'success': True, 'ordenes': ordenes})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def api_ordenes_produccion(request):
    """API para obtener órdenes de producción"""
    try:
        # Datos de ejemplo - reemplazar con tu modelo real
        ordenes = [
            {
                'id': 1,
                'numero_orden': 'OP-001',
                'cliente': 'Cliente Ejemplo 1',
                'fecha_entrega': '2024-01-20',
                'estado': 'en_produccion',
                'tipo_produccion': 'edicion_audio',
                'responsable': 'Producción 1'
            },
            {
                'id': 2,
                'numero_orden': 'OP-002',
                'cliente': 'Cliente Ejemplo 2',
                'fecha_entrega': '2024-01-22',
                'estado': 'pendiente',
                'tipo_produccion': 'mezcla_audio',
                'responsable': 'Producción 2'
            }
        ]
        
        return JsonResponse({'success': True, 'ordenes': ordenes})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def api_ordenes_finalizacion(request):
    """API para obtener órdenes de finalización"""
    try:
        # Datos de ejemplo - reemplazar con tu modelo real
        ordenes = [
            {
                'id': 1,
                'numero_orden': 'OF-001',
                'cliente': 'Cliente Ejemplo 1',
                'fecha_finalizacion': '2024-01-18',
                'estado': 'completado',
                'resultado': 'aprobado',
                'observaciones': 'Proyecto finalizado satisfactoriamente'
            },
            {
                'id': 2,
                'numero_orden': 'OF-002',
                'cliente': 'Cliente Ejemplo 2',
                'fecha_finalizacion': '2024-01-19',
                'estado': 'pendiente_revision',
                'resultado': 'en_revision',
                'observaciones': 'Esperando aprobación del cliente'
            }
        ]
        
        return JsonResponse({'success': True, 'ordenes': ordenes})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

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
                        print(f"   {idx}. ID:{c.id} | Num:{c.numero_contrato} | Cliente:{c.nombre_cliente}")
                
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
                
                print(f"✅ Contratos hoy: {contratos_hoy}")
                print(f"✅ Contratos último mes: {contratos_mes}")
                
                # Detalles de cada contrato reciente
                if contratos_recientes:
                    print("\n📋 Detalles de contratos recientes:")
                    for idx, c in enumerate(contratos_recientes, 1):
                        print(f"   {idx}. {c.numero_contrato} | {c.nombre_cliente} | {c.fecha_generacion}")
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
        'plantillas_activas': plantillas_activas,
    }
    
    print(f"\n📦 CONTEXT FINAL:")
    print(f"   - plantillas: {type(context['plantillas'])} | Count: {context['plantillas'].count()}")
    print(f"   - clientes: {type(context['clientes'])} | Count: {context['clientes'].count()}")
    print(f"   - contratos_recientes: {type(context['contratos_recientes'])} | Len: {len(context['contratos_recientes'])}")
    print(f"   - total_contratos: {context['total_contratos']}")
    print(f"   - contratos_hoy: {context['contratos_hoy']}")
    print(f"   - contratos_mes: {context['contratos_mes']}")
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
        
        # ✅ CREAR CONTRATO SIN CUÑA TEMPORAL
        contrato = ContratoGenerado.objects.create(
            plantilla_usada=plantilla,
            cliente=cliente,
            nombre_cliente=cliente.empresa or cliente.get_full_name(),
            ruc_dni_cliente=cliente.ruc_dni or '',
            valor_sin_iva=Decimal(str(data['valor_contrato'])),
            generado_por=request.user,
            estado='borrador'  # Inicia en borrador
        )
        
        # ✅ GUARDAR DATOS PARA USAR DESPUÉS AL CREAR LA CUÑA
        contrato.datos_generacion = {
            'FECHA_INICIO_RAW': data['fecha_inicio'],
            'FECHA_FIN_RAW': data['fecha_fin'],
            'SPOTS_DIA': data.get('spots_dia', 1),
            'DURACION_SPOT': data.get('duracion_spot', 30),
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
        
        # Validar que sea PDF
        if not archivo.name.endswith('.pdf'):
            return JsonResponse({
                'success': False,
                'error': 'El archivo debe ser un PDF'
            }, status=400)
        
        # Guardar el archivo validado
        contrato.archivo_contrato_validado = archivo
        contrato.save()
        
        # ✅ VALIDAR Y CREAR CUÑA AUTOMÁTICAMENTE
        resultado = contrato.validar_y_crear_cuna(user=request.user)
        
        if resultado['success']:
            # Registrar en historial
            LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ContentType.objects.get_for_model(contrato).pk,
                object_id=contrato.pk,
                object_repr=contrato.numero_contrato,
                action_flag=CHANGE,
                change_message=f'Contrato validado y cuña creada automáticamente (ID: {resultado["cuna_id"]})'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Contrato validado y cuña creada exitosamente',
                'cuna_id': resultado['cuna_id']
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
    """API para actualizar una cuña publicitaria"""
    from apps.content_management.models import CuñaPublicitaria
    from decimal import Decimal
    from datetime import datetime
    
    try:
        cuna = CuñaPublicitaria.objects.get(pk=cuna_id)
        data = json.loads(request.body)
        
        # Actualizar campos básicos
        cuna.titulo = data.get('titulo', cuna.titulo)
        cuna.descripcion = data.get('descripcion', cuna.descripcion)
        cuna.estado = data.get('estado', cuna.estado)
        cuna.observaciones = data.get('observaciones', cuna.observaciones)
        cuna.excluir_sabados = data.get('excluir_sabados', cuna.excluir_sabados)
        cuna.excluir_domingos = data.get('excluir_domingos', cuna.excluir_domingos)
        
        # ✅ CRÍTICO: Convertir fechas de string a objetos date
        if 'fecha_inicio' in data and data['fecha_inicio']:
            try:
                cuna.fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Formato de fecha de inicio inválido'}, status=400)
        
        if 'fecha_fin' in data and data['fecha_fin']:
            try:
                cuna.fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': 'Formato de fecha de fin inválido'}, status=400)
        
        # Actualizar campos numéricos con conversión correcta
        try:
            if 'duracion_planeada' in data:
                cuna.duracion_planeada = int(data['duracion_planeada'])
            if 'repeticiones_dia' in data:
                cuna.repeticiones_dia = int(data['repeticiones_dia'])
            if 'precio_por_segundo' in data:
                cuna.precio_por_segundo = Decimal(str(float(data['precio_por_segundo'])))
            if 'precio_total' in data:
                cuna.precio_total = Decimal(str(float(data['precio_total'])))
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Error en los valores numéricos: {str(e)}'
            }, status=400)
        
        # Actualizar cliente
        if data.get('cliente_id'):
            try:
                cliente = CustomUser.objects.get(pk=data['cliente_id'], rol='cliente')
                cuna.cliente = cliente
            except CustomUser.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Cliente no encontrado'}, status=404)
        
        # Actualizar vendedor
        if 'vendedor_id' in data:
            if data['vendedor_id']:
                try:
                    vendedor = CustomUser.objects.get(pk=data['vendedor_id'], rol='vendedor')
                    cuna.vendedor_asignado = vendedor
                except CustomUser.DoesNotExist:
                    cuna.vendedor_asignado = None
            else:
                cuna.vendedor_asignado = None
        
        # Actualizar categoría
        if 'categoria_id' in data:
            if data['categoria_id']:
                from apps.content_management.models import CategoriaPublicitaria
                try:
                    categoria = CategoriaPublicitaria.objects.get(pk=data['categoria_id'])
                    cuna.categoria = categoria
                except CategoriaPublicitaria.DoesNotExist:
                    cuna.categoria = None
            else:
                cuna.categoria = None
        
        # Actualizar tipo de contrato
        if 'tipo_contrato_id' in data:
            if data['tipo_contrato_id']:
                from apps.content_management.models import TipoContrato
                try:
                    tipo_contrato = TipoContrato.objects.get(pk=data['tipo_contrato_id'])
                    cuna.tipo_contrato = tipo_contrato
                except TipoContrato.DoesNotExist:
                    cuna.tipo_contrato = None
            else:
                cuna.tipo_contrato = None
        
        cuna.save()
        
        # Registrar en historial
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.contenttypes.models import ContentType
        
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(cuna).pk,
            object_id=cuna.pk,
            object_repr=str(cuna.titulo),
            action_flag=CHANGE,
            change_message=f'Cuña actualizada: {cuna.titulo}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Cuña actualizada exitosamente'
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
    """API para crear un nuevo cliente"""
    if not request.user.es_admin and not request.user.es_vendedor:
        messages.error(request, 'No tienes permisos para crear clientes')
        return redirect('custom_admin:clientes_list')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('custom_admin:clientes_list')
    
    try:
        # Validar que no exista el username
        username = request.POST.get('username')
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, f'El usuario "{username}" ya existe')
            return redirect('custom_admin:clientes_list')

        # Validar que no exista el email
        email = request.POST.get('email')
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, f'El email "{email}" ya está registrado')
            return redirect('custom_admin:clientes_list')

        # Crear el cliente sin contraseña
        cliente = CustomUser(
            username=username,
            email=email,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
        )
        # Establecer contraseña como no utilizable (sin contraseña)
        cliente.set_unusable_password()

        # Establecer rol como cliente
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
        
        # --- LOS DOS CAMPOS NUEVOS ---
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

        # Guardar el cliente
        cliente.save()
        
        # Registrar en historial con LogEntry
        from django.contrib.admin.models import LogEntry, ADDITION
        from django.contrib.contenttypes.models import ContentType
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(cliente).pk,
            object_id=cliente.pk,
            object_repr=str(cliente.empresa or cliente.username),
            action_flag=ADDITION,
            change_message=f'Cliente creado: {cliente.empresa} ({cliente.ruc_dni}) - Sin contraseña'
        )

        messages.success(request, f'✓ Cliente "{cliente.empresa}" creado exitosamente')
        return redirect('custom_admin:clientes_list')
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())  # Para debug en consola
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
# ==================== VISTAS PARA ÓRDENES ====================

@login_required
@user_passes_test(is_admin)
def orders_list(request):
    """Lista de órdenes del sistema"""
    
    # Filtros
    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    prioridad_filter = request.GET.get('prioridad', '')
    fecha_filter = request.GET.get('fecha', '')
    
    # Datos de ejemplo - reemplazar con tu modelo real
    ordenes = [
        {
            'id': 1,
            'numero_orden': 'ORD-001',
            'cliente': {
                'empresa': 'Empresa Ejemplo 1',
                'get_full_name': 'Cliente Uno',
                'ruc_dni': '12345678901'
            },
            'fecha_orden': timezone.now().date(),
            'detalle_productos': 'Servicio de publicidad radial - Spot 30 segundos',
            'total': Decimal('1500.00'),
            'prioridad': 'alta',
            'estado': 'pendiente',
            'vendedor': request.user if hasattr(request.user, 'get_full_name') else None
        },
        {
            'id': 2,
            'numero_orden': 'ORD-002',
            'cliente': {
                'empresa': 'Empresa Ejemplo 2', 
                'get_full_name': 'Cliente Dos',
                'ruc_dni': '10987654321'
            },
            'fecha_orden': timezone.now().date() - timedelta(days=1),
            'detalle_productos': 'Producción de cuña publicitaria',
            'total': Decimal('2500.00'),
            'prioridad': 'media',
            'estado': 'procesando',
            'vendedor': request.user if hasattr(request.user, 'get_full_name') else None
        }
    ]
    
    # Aplicar filtros
    if search:
        ordenes = [o for o in ordenes if search.lower() in o['numero_orden'].lower() or 
                 search.lower() in o['cliente']['empresa'].lower()]
    
    if estado_filter:
        ordenes = [o for o in ordenes if o['estado'] == estado_filter]
    
    if prioridad_filter:
        ordenes = [o for o in ordenes if o['prioridad'] == prioridad_filter]
    
    # Estadísticas
    total_ordenes = len(ordenes)
    ordenes_pendientes = len([o for o in ordenes if o['estado'] == 'pendiente'])
    ordenes_procesando = len([o for o in ordenes if o['estado'] == 'procesando'])
    ordenes_completadas = len([o for o in ordenes if o['estado'] == 'completado'])
    
    # Obtener clientes para el formulario
    clientes = CustomUser.objects.filter(rol='cliente', is_active=True)
    
    context = {
        'ordenes': ordenes,
        'total_ordenes': total_ordenes,
        'ordenes_pendientes': ordenes_pendientes,
        'ordenes_procesando': ordenes_procesando,
        'ordenes_completadas': ordenes_completadas,
        'clientes': clientes,
        'search': search,
        'estado_filter': estado_filter,
        'prioridad_filter': prioridad_filter,
        'fecha_filter': fecha_filter,
    }
    
    return render(request, 'custom_admin/orders/list.html', context)

@login_required
@user_passes_test(is_admin)
def order_detail_api(request, order_id):
    """API para obtener detalles de una orden"""
    try:
        # Datos de ejemplo - reemplazar con tu modelo real
        ordenes_data = {
            1: {
                'id': 1,
                'numero_orden': 'ORD-001',
                'cliente_id': 1,
                'cliente_nombre': 'Empresa Ejemplo 1 - Cliente Uno',
                'cliente_ruc': '12345678901',
                'fecha_orden': '2024-01-15',
                'detalle_productos': 'Servicio de publicidad radial - Spot 30 segundos',
                'cantidad': 1,
                'total': '1500.00',
                'prioridad': 'alta',
                'estado': 'pendiente',
                'observaciones': 'Cliente solicita revisión previa',
                'vendedor_nombre': request.user.get_full_name(),
                'fecha_creacion': timezone.now().strftime('%d/%m/%Y %H:%M')
            },
            2: {
                'id': 2,
                'numero_orden': 'ORD-002', 
                'cliente_id': 2,
                'cliente_nombre': 'Empresa Ejemplo 2 - Cliente Dos',
                'cliente_ruc': '10987654321',
                'fecha_orden': '2024-01-14',
                'detalle_productos': 'Producción de cuña publicitaria',
                'cantidad': 1,
                'total': '2500.00',
                'prioridad': 'media',
                'estado': 'procesando',
                'observaciones': 'En proceso de grabación',
                'vendedor_nombre': request.user.get_full_name(),
                'fecha_creacion': timezone.now().strftime('%d/%m/%Y %H:%M')
            }
        }
        
        orden = ordenes_data.get(order_id)
        if not orden:
            return JsonResponse({'error': 'Orden no encontrada'}, status=404)
        
        return JsonResponse(orden)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def order_create_api(request):
    """API para crear una nueva orden"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['numero_orden', 'cliente', 'fecha_orden', 'detalle_productos', 'total']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'El campo {field} es obligatorio'
                }, status=400)
        
        # Aquí iría la lógica para crear la orden en la base de datos
        # Por ahora simulamos la creación
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(CustomUser).pk,  # Temporal
            object_id=request.user.pk,
            object_repr=f"Orden creada: {data['numero_orden']}",
            action_flag=ADDITION,
            change_message=f'Orden creada: {data["numero_orden"]} - Cliente: {data["cliente"]}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden creada exitosamente',
            'order_id': 3  # ID simulado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al crear la orden: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def order_update_api(request, order_id):
    """API para actualizar una orden existente"""
    try:
        data = json.loads(request.body)
        
        # Validar que la orden existe
        # Aquí iría la lógica para buscar y actualizar la orden en la base de datos
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(CustomUser).pk,  # Temporal
            object_id=request.user.pk,
            object_repr=f"Orden actualizada: {data.get('numero_orden', 'N/A')}",
            action_flag=CHANGE,
            change_message=f'Orden {order_id} actualizada'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden actualizada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar la orden: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def order_delete_api(request, order_id):
    """API para eliminar una orden"""
    try:
        # Validar que la orden existe
        # Aquí iría la lógica para eliminar la orden de la base de datos
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(CustomUser).pk,  # Temporal
            object_id=request.user.pk,
            object_repr=f"Orden eliminada: {order_id}",
            action_flag=DELETION,
            change_message=f'Orden {order_id} eliminada'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Orden eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar la orden: {str(e)}'
        }, status=500)

# ==================== VISTAS PARA PARTE MORTORIOS ====================

@login_required
@user_passes_test(is_admin)
def parte_mortorios_list(request):
    """Lista de partes mortorios del sistema"""
    
    # Filtros
    search = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    urgencia_filter = request.GET.get('urgencia', '')
    fecha_filter = request.GET.get('fecha', '')
    
    # Datos de ejemplo - reemplazar con tu modelo real
    partes = [
        {
            'id': 1,
            'numero_parte': 'PM-001',
            'nombre_fallecido': 'Juan Pérez García',
            'edad_fallecido': 75,
            'fecha_registro': timezone.now().date(),
            'lugar_fallecimiento': 'Hospital Regional de Lima',
            'causa_fallecimiento': 'Paro cardíaco',
            'urgencia': 'normal',
            'estado': 'registrado',
            'registrado_por': request.user
        },
        {
            'id': 2,
            'numero_parte': 'PM-002',
            'nombre_fallecido': 'María López Martínez',
            'edad_fallecido': 82,
            'fecha_registro': timezone.now().date() - timedelta(days=1),
            'lugar_fallecimiento': 'Domicilio particular - Av. Principal 123',
            'causa_fallecimiento': 'Insuficiencia respiratoria',
            'urgencia': 'urgente',
            'estado': 'verificado',
            'registrado_por': request.user
        }
    ]
    
    # Aplicar filtros
    if search:
        partes = [p for p in partes if search.lower() in p['numero_parte'].lower() or 
                 search.lower() in p['nombre_fallecido'].lower()]
    
    if estado_filter:
        partes = [p for p in partes if p['estado'] == estado_filter]
    
    if urgencia_filter:
        partes = [p for p in partes if p['urgencia'] == urgencia_filter]
    
    # Estadísticas
    total_partes = len(partes)
    partes_registrados = len([p for p in partes if p['estado'] == 'registrado'])
    partes_verificados = len([p for p in partes if p['estado'] == 'verificado'])
    partes_completados = len([p for p in partes if p['estado'] == 'completado'])
    
    context = {
        'partes': partes,
        'total_partes': total_partes,
        'partes_registrados': partes_registrados,
        'partes_verificados': partes_verificados,
        'partes_completados': partes_completados,
        'search': search,
        'estado_filter': estado_filter,
        'urgencia_filter': urgencia_filter,
        'fecha_filter': fecha_filter,
    }
    
    return render(request, 'custom_admin/parte_mortorios/list.html', context)

@login_required
@user_passes_test(is_admin)
def parte_mortorio_detail_api(request, parte_id):
    """API para obtener detalles de un parte mortorio"""
    try:
        # Datos de ejemplo - reemplazar con tu modelo real
        partes_data = {
            1: {
                'id': 1,
                'numero_parte': 'PM-001',
                'nombre_fallecido': 'Juan Pérez García',
                'edad_fallecido': 75,
                'dni_fallecido': '12345678',
                'urgencia': 'normal',
                'fecha_fallecimiento': '2024-01-15',
                'hora_fallecimiento': '14:30',
                'lugar_fallecimiento': 'Hospital Regional de Lima',
                'causa_fallecimiento': 'Paro cardíaco',
                'estado': 'registrado',
                'observaciones': 'Fallecimiento natural',
                'registrado_por_nombre': request.user.get_full_name(),
                'fecha_registro': timezone.now().strftime('%d/%m/%Y %H:%M'),
                'fecha_actualizacion': timezone.now().strftime('%d/%m/%Y %H:%M')
            },
            2: {
                'id': 2,
                'numero_parte': 'PM-002',
                'nombre_fallecido': 'María López Martínez', 
                'edad_fallecido': 82,
                'dni_fallecido': '87654321',
                'urgencia': 'urgente',
                'fecha_fallecimiento': '2024-01-14',
                'hora_fallecimiento': '09:15',
                'lugar_fallecimiento': 'Domicilio particular - Av. Principal 123',
                'causa_fallecimiento': 'Insuficiencia respiratoria',
                'estado': 'verificado',
                'observaciones': 'Requiere traslado urgente',
                'registrado_por_nombre': request.user.get_full_name(),
                'fecha_registro': (timezone.now() - timedelta(days=1)).strftime('%d/%m/%Y %H:%M'),
                'fecha_actualizacion': timezone.now().strftime('%d/%m/%Y %H:%M')
            }
        }
        
        parte = partes_data.get(parte_id)
        if not parte:
            return JsonResponse({'error': 'Parte mortorio no encontrado'}, status=404)
        
        return JsonResponse(parte)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_create_api(request):
    """API para crear un nuevo parte mortorio"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['numero_parte', 'nombre_fallecido', 'fecha_fallecimiento', 'lugar_fallecimiento']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'El campo {field} es obligatorio'
                }, status=400)
        
        # Aquí iría la lógica para crear el parte mortorio en la base de datos
        # Por ahora simulamos la creación
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(CustomUser).pk,  # Temporal
            object_id=request.user.pk,
            object_repr=f"Parte mortorio creado: {data['numero_parte']}",
            action_flag=ADDITION,
            change_message=f'Parte mortorio creado: {data["numero_parte"]} - Fallecido: {data["nombre_fallecido"]}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio creado exitosamente',
            'parte_id': 3  # ID simulado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al crear el parte mortorio: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_update_api(request, parte_id):
    """API para actualizar un parte mortorio existente"""
    try:
        data = json.loads(request.body)
        
        # Validar que el parte mortorio existe
        # Aquí iría la lógica para buscar y actualizar el parte mortorio en la base de datos
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(CustomUser).pk,  # Temporal
            object_id=request.user.pk,
            object_repr=f"Parte mortorio actualizado: {data.get('numero_parte', 'N/A')}",
            action_flag=CHANGE,
            change_message=f'Parte mortorio {parte_id} actualizado'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio actualizado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar el parte mortorio: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def parte_mortorio_delete_api(request, parte_id):
    """API para eliminar un parte mortorio"""
    try:
        # Validar que el parte mortorio existe
        # Aquí iría la lógica para eliminar el parte mortorio de la base de datos
        
        # Registrar en historial
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(CustomUser).pk,  # Temporal
            object_id=request.user.pk,
            object_repr=f"Parte mortorio eliminado: {parte_id}",
            action_flag=DELETION,
            change_message=f'Parte mortorio {parte_id} eliminado'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Parte mortorio eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al eliminar el parte mortorio: {str(e)}'
        }, status=500)
