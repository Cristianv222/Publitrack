"""
Vistas para el módulo de Control de Transmisiones
Sistema PubliTrack - Gestión y programación de transmisiones de publicidad radial
"""

import json
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .models import (
    ConfiguracionTransmision,
    ProgramacionTransmision,
    TransmisionActual,
    LogTransmision,
    EventoSistema,
    obtener_transmision_actual,
    obtener_proximas_transmisiones,
    verificar_sistema_listo_para_transmitir
)
from .forms import (
    ConfiguracionTransmisionForm,
    ProgramacionTransmisionForm,
    TransmisionManualForm
)
from apps.content_management.models import CuñaPublicitaria


# ==================== VISTAS DEL DASHBOARD ====================

@login_required
def dashboard_transmisiones(request):
    """
    Vista principal del dashboard de transmisiones
    """
    # Verificar permisos
    if not request.user.can_view_reports():
        messages.error(request, 'No tienes permisos para ver este módulo.')
        return redirect('authentication:dashboard')
    
    # Obtener datos del dashboard
    transmision_actual = obtener_transmision_actual()
    proximas_transmisiones = obtener_proximas_transmisiones(5)
    
    # Estadísticas del día
    hoy = timezone.now().date()
    
    transmisiones_hoy = TransmisionActual.objects.filter(
        inicio_programado__date=hoy
    )
    
    stats_hoy = {
        'total_programadas': transmisiones_hoy.count(),
        'completadas': transmisiones_hoy.filter(estado='completada').count(),
        'en_curso': transmisiones_hoy.filter(estado='transmitiendo').count(),
        'con_error': transmisiones_hoy.filter(estado='error').count(),
    }
    
    # Cuñas más transmitidas (últimos 7 días)
    hace_7_dias = timezone.now() - timedelta(days=7)
    cuñas_populares = LogTransmision.objects.filter(
        timestamp__gte=hace_7_dias,
        accion='iniciada',
        cuña__isnull=False
    ).values(
        'cuña__titulo',
        'cuña__codigo'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Estado del sistema
    configuracion = ConfiguracionTransmision.get_configuracion_activa()
    sistema_listo, mensaje_sistema = verificar_sistema_listo_para_transmitir()
    
    # Últimos logs importantes
    logs_recientes = LogTransmision.objects.filter(
        nivel__in=['warning', 'error', 'critical']
    )[:10]
    
    context = {
        'transmision_actual': transmision_actual,
        'proximas_transmisiones': proximas_transmisiones,
        'stats_hoy': stats_hoy,
        'cuñas_populares': cuñas_populares,
        'configuracion': configuracion,
        'sistema_listo': sistema_listo,
        'mensaje_sistema': mensaje_sistema,
        'logs_recientes': logs_recientes,
    }
    
    return render(request, 'transmission_control/dashboard.html', context)


# ==================== MONITOR EN TIEMPO REAL ====================

@method_decorator(never_cache, name='dispatch')
class MonitorTiempoRealView(LoginRequiredMixin, DetailView):
    """
    Vista del monitor en tiempo real
    """
    template_name = 'transmission_control/monitor_tiempo_real.html'
    context_object_name = 'transmision'
    
    def get_object(self):
        return obtener_transmision_actual()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Próximas transmisiones
        context['proximas_transmisiones'] = obtener_proximas_transmisiones(10)
        
        # Estado del sistema
        context['configuracion'] = ConfiguracionTransmision.get_configuracion_activa()
        
        # Estadísticas en tiempo real
        ahora = timezone.now()
        inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
        
        context['stats_tiempo_real'] = {
            'transmisiones_hoy': TransmisionActual.objects.filter(
                inicio_programado__gte=inicio_dia
            ).count(),
            'completadas_hoy': TransmisionActual.objects.filter(
                inicio_programado__gte=inicio_dia,
                estado='completada'
            ).count(),
            'tiempo_total_transmitido': TransmisionActual.objects.filter(
                inicio_programado__gte=inicio_dia,
                duracion_segundos__isnull=False
            ).aggregate(
                total=Sum('duracion_segundos')
            )['total'] or 0,
        }
        
        return context


@login_required
@require_http_methods(["GET"])
def api_estado_transmision(request):
    """
    API para obtener el estado actual de la transmisión (para AJAX)
    """
    transmision = obtener_transmision_actual()
    
    data = {
        'hay_transmision': transmision is not None,
        'timestamp': timezone.now().isoformat(),
    }
    
    if transmision:
        data.update({
            'session_id': str(transmision.session_id),
            'cuña_titulo': transmision.cuña.titulo,
            'cuña_codigo': transmision.cuña.codigo,
            'estado': transmision.estado,
            'progreso_porcentaje': transmision.progreso_porcentaje,
            'posicion_actual': transmision.posicion_actual,
            'duracion_segundos': transmision.duracion_segundos,
            'tiempo_restante': transmision.tiempo_restante,
            'volumen': float(transmision.volumen),
            'pausado_manualmente': transmision.pausado_manualmente,
        })
    
    return JsonResponse(data)


# ==================== CONTROL MANUAL ====================

@login_required
@require_POST
def pausar_transmision(request):
    """
    Pausa la transmisión actual
    """
    if not request.user.can_manage_content():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    transmision = obtener_transmision_actual()
    if not transmision:
        return JsonResponse({'error': 'No hay transmisión activa'}, status=400)
    
    if transmision.estado != 'transmitiendo':
        return JsonResponse({'error': 'La transmisión no está en estado válido'}, status=400)
    
    transmision.pausar_transmision(request.user)
    
    return JsonResponse({
        'success': True,
        'mensaje': 'Transmisión pausada correctamente'
    })


@login_required
@require_POST
def reanudar_transmision(request):
    """
    Reanuda la transmisión actual
    """
    if not request.user.can_manage_content():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    transmision = obtener_transmision_actual()
    if not transmision:
        return JsonResponse({'error': 'No hay transmisión activa'}, status=400)
    
    if transmision.estado != 'pausada':
        return JsonResponse({'error': 'La transmisión no está pausada'}, status=400)
    
    transmision.reanudar_transmision(request.user)
    
    return JsonResponse({
        'success': True,
        'mensaje': 'Transmisión reanudada correctamente'
    })


@login_required
@require_POST
def detener_transmision(request):
    """
    Detiene la transmisión actual
    """
    if not request.user.can_manage_content():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    transmision = obtener_transmision_actual()
    if not transmision:
        return JsonResponse({'error': 'No hay transmisión activa'}, status=400)
    
    if transmision.estado not in ['transmitiendo', 'pausada']:
        return JsonResponse({'error': 'La transmisión no está en estado válido'}, status=400)
    
    transmision.finalizar_transmision(request.user, 'cancelada')
    
    return JsonResponse({
        'success': True,
        'mensaje': 'Transmisión detenida correctamente'
    })


@login_required
@require_POST
def ajustar_volumen(request):
    """
    Ajusta el volumen de la transmisión actual
    """
    if not request.user.can_manage_content():
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        volumen = float(request.POST.get('volumen', 100))
        if not 0 <= volumen <= 100:
            return JsonResponse({'error': 'Volumen debe estar entre 0 y 100'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Volumen inválido'}, status=400)
    
    transmision = obtener_transmision_actual()
    if not transmision:
        return JsonResponse({'error': 'No hay transmisión activa'}, status=400)
    
    transmision.volumen = volumen
    transmision.save(update_fields=['volumen'])
    
    # Crear log
    LogTransmision.log_evento(
        accion='intervencion_manual',
        descripcion=f'Volumen ajustado a {volumen}%',
        transmision=transmision,
        usuario=request.user,
        datos={'volumen_anterior': transmision.volumen, 'volumen_nuevo': volumen}
    )
    
    return JsonResponse({
        'success': True,
        'mensaje': f'Volumen ajustado a {volumen}%'
    })


# ==================== PROGRAMACIONES ====================

class ProgramacionListView(LoginRequiredMixin, ListView):
    """
    Lista de programaciones de transmisión
    """
    model = ProgramacionTransmision
    template_name = 'transmission_control/programacion_list.html'
    context_object_name = 'programaciones'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ProgramacionTransmision.objects.select_related(
            'cuña', 'configuracion', 'created_by'
        )
        
        # Filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_programacion=tipo)
        
        busqueda = self.request.GET.get('busqueda')
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda) |
                Q(codigo__icontains=busqueda) |
                Q(cuña__titulo__icontains=busqueda)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = ProgramacionTransmision.ESTADO_CHOICES
        context['tipos'] = ProgramacionTransmision.TIPO_PROGRAMACION_CHOICES
        return context


class ProgramacionDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle de una programación
    """
    model = ProgramacionTransmision
    template_name = 'transmission_control/programacion_detail.html'
    context_object_name = 'programacion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Historial de transmisiones
        context['transmisiones'] = TransmisionActual.objects.filter(
            programacion=self.object
        ).order_by('-created_at')[:10]
        
        # Logs relacionados
        context['logs'] = LogTransmision.objects.filter(
            programacion=self.object
        ).order_by('-timestamp')[:20]
        
        return context


class ProgramacionCreateView(LoginRequiredMixin, CreateView):
    """
    Crear nueva programación
    """
    model = ProgramacionTransmision
    form_class = ProgramacionTransmisionForm
    template_name = 'transmission_control/programacion_form.html'
    success_url = reverse_lazy('transmission_control:programacion_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Programación creada correctamente.')
        return super().form_valid(form)


class ProgramacionUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar programación existente
    """
    model = ProgramacionTransmision
    form_class = ProgramacionTransmisionForm
    template_name = 'transmission_control/programacion_form.html'
    success_url = reverse_lazy('transmission_control:programacion_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Programación actualizada correctamente.')
        return super().form_valid(form)


@login_required
@require_POST
def activar_programacion(request, pk):
    """
    Activa una programación
    """
    programacion = get_object_or_404(ProgramacionTransmision, pk=pk)
    
    if programacion.estado != 'programada':
        messages.error(request, 'Solo se pueden activar programaciones en estado "programada".')
    else:
        programacion.activar()
        messages.success(request, f'Programación {programacion.codigo} activada.')
    
    return redirect('transmission_control:programacion_detail', pk=pk)


@login_required
@require_POST
def cancelar_programacion(request, pk):
    """
    Cancela una programación
    """
    programacion = get_object_or_404(ProgramacionTransmision, pk=pk)
    
    if programacion.estado in ['completada', 'cancelada']:
        messages.error(request, 'No se puede cancelar esta programación.')
    else:
        programacion.cancelar()
        messages.success(request, f'Programación {programacion.codigo} cancelada.')
    
    return redirect('transmission_control:programacion_detail', pk=pk)


# ==================== CALENDARIO ====================

@login_required
def calendario_transmisiones(request):
    """
    Vista del calendario de transmisiones
    """
    # Obtener fecha desde parámetros o usar fecha actual
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = timezone.now().date()
    else:
        fecha = timezone.now().date()
    
    # Calcular rango de fechas para la semana
    inicio_semana = fecha - timedelta(days=fecha.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    # Obtener transmisiones de la semana
    transmisiones = TransmisionActual.objects.filter(
        inicio_programado__date__range=[inicio_semana, fin_semana]
    ).select_related('cuña', 'programacion').order_by('inicio_programado')
    
    # Organizar por días
    transmisiones_por_dia = {}
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        transmisiones_por_dia[dia] = transmisiones.filter(
            inicio_programado__date=dia
        )
    
    # Navegación
    semana_anterior = inicio_semana - timedelta(days=7)
    semana_siguiente = inicio_semana + timedelta(days=7)
    
    context = {
        'fecha_actual': fecha,
        'inicio_semana': inicio_semana,
        'fin_semana': fin_semana,
        'transmisiones_por_dia': transmisiones_por_dia,
        'semana_anterior': semana_anterior,
        'semana_siguiente': semana_siguiente,
    }
    
    return render(request, 'transmission_control/calendario.html', context)


@login_required
def calendario_mes(request):
    """
    Vista del calendario mensual
    """
    # Obtener año y mes desde parámetros
    año = int(request.GET.get('año', timezone.now().year))
    mes = int(request.GET.get('mes', timezone.now().month))
    
    # Primer y último día del mes
    primer_dia = datetime(año, mes, 1).date()
    if mes == 12:
        ultimo_dia = datetime(año + 1, 1, 1).date() - timedelta(days=1)
    else:
        ultimo_dia = datetime(año, mes + 1, 1).date() - timedelta(days=1)
    
    # Obtener transmisiones del mes
    transmisiones = TransmisionActual.objects.filter(
        inicio_programado__date__range=[primer_dia, ultimo_dia]
    ).select_related('cuña', 'programacion')
    
    # Organizar por días
    transmisiones_por_dia = {}
    dia_actual = primer_dia
    while dia_actual <= ultimo_dia:
        transmisiones_dia = transmisiones.filter(inicio_programado__date=dia_actual)
        if transmisiones_dia.exists():
            transmisiones_por_dia[dia_actual] = {
                'total': transmisiones_dia.count(),
                'completadas': transmisiones_dia.filter(estado='completada').count(),
                'errores': transmisiones_dia.filter(estado='error').count(),
            }
        dia_actual += timedelta(days=1)
    
    # Navegación
    mes_anterior = mes - 1 if mes > 1 else 12
    año_anterior = año if mes > 1 else año - 1
    mes_siguiente = mes + 1 if mes < 12 else 1
    año_siguiente = año if mes < 12 else año + 1
    
    context = {
        'año': año,
        'mes': mes,
        'primer_dia': primer_dia,
        'ultimo_dia': ultimo_dia,
        'transmisiones_por_dia': transmisiones_por_dia,
        'mes_anterior': mes_anterior,
        'año_anterior': año_anterior,
        'mes_siguiente': mes_siguiente,
        'año_siguiente': año_siguiente,
    }
    
    return render(request, 'transmission_control/calendario_mes.html', context)


# ==================== LOGS Y REPORTES ====================

class LogsListView(LoginRequiredMixin, ListView):
    """
    Lista de logs de transmisión
    """
    model = LogTransmision
    template_name = 'transmission_control/logs_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = LogTransmision.objects.select_related(
            'usuario', 'transmision', 'cuña'
        )
        
        # Filtros
        accion = self.request.GET.get('accion')
        if accion:
            queryset = queryset.filter(accion=accion)
        
        nivel = self.request.GET.get('nivel')
        if nivel:
            queryset = queryset.filter(nivel=nivel)
        
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            try:
                fecha = datetime.strptime(fecha_desde, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=fecha)
            except ValueError:
                pass
        
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            try:
                fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__lte=fecha + timedelta(days=1))
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['acciones'] = LogTransmision.ACCION_CHOICES
        context['niveles'] = LogTransmision.NIVEL_CHOICES
        return context


@login_required
def reporte_transmisiones(request):
    """
    Reporte de estadísticas de transmisiones
    """
    # Obtener parámetros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        # Por defecto, últimos 30 días
        fecha_hasta = timezone.now().date()
        fecha_desde = fecha_hasta - timedelta(days=30)
    else:
        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Formato de fecha inválido.')
            fecha_hasta = timezone.now().date()
            fecha_desde = fecha_hasta - timedelta(days=30)
    
    # Obtener estadísticas
    transmisiones = TransmisionActual.objects.filter(
        inicio_programado__date__range=[fecha_desde, fecha_hasta]
    )
    
    stats = {
        'total_transmisiones': transmisiones.count(),
        'completadas': transmisiones.filter(estado='completada').count(),
        'con_error': transmisiones.filter(estado='error').count(),
        'canceladas': transmisiones.filter(estado='cancelada').count(),
        'tiempo_total': transmisiones.filter(
            duracion_segundos__isnull=False
        ).aggregate(total=Sum('duracion_segundos'))['total'] or 0,
    }
    
    # Cuñas más transmitidas
    cuñas_populares = LogTransmision.objects.filter(
        timestamp__date__range=[fecha_desde, fecha_hasta],
        accion='iniciada',
        cuña__isnull=False
    ).values(
        'cuña__titulo',
        'cuña__codigo',
        'cuña__cliente__first_name',
        'cuña__cliente__last_name'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:10]
    
    # Transmisiones por día
    transmisiones_por_dia = []
    dia_actual = fecha_desde
    while dia_actual <= fecha_hasta:
        count = transmisiones.filter(inicio_programado__date=dia_actual).count()
        transmisiones_por_dia.append({
            'fecha': dia_actual,
            'total': count
        })
        dia_actual += timedelta(days=1)
    
    # Errores más comunes
    errores_comunes = LogTransmision.objects.filter(
        timestamp__date__range=[fecha_desde, fecha_hasta],
        nivel__in=['error', 'critical']
    ).values('descripcion').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    context = {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'stats': stats,
        'cuñas_populares': cuñas_populares,
        'transmisiones_por_dia': transmisiones_por_dia,
        'errores_comunes': errores_comunes,
    }
    
    return render(request, 'transmission_control/reporte.html', context)


# ==================== CONFIGURACIÓN ====================

class ConfiguracionUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar configuración del sistema
    """
    model = ConfiguracionTransmision
    form_class = ConfiguracionTransmisionForm
    template_name = 'transmission_control/configuracion_form.html'
    success_url = reverse_lazy('transmission_control:dashboard')
    
    def get_object(self):
        # Obtener la configuración activa o crear una nueva
        configuracion = ConfiguracionTransmision.get_configuracion_activa()
        if not configuracion:
            configuracion = ConfiguracionTransmision.objects.create(
                nombre_configuracion='Configuración Principal',
                created_by=self.request.user
            )
        return configuracion
    
    def form_valid(self, form):
        # Crear evento del sistema
        EventoSistema.objects.create(
            tipo_evento='cambio_configuracion',
            descripcion='Configuración del sistema actualizada',
            usuario=self.request.user,
            configuracion_despues=form.cleaned_data
        )
        
        messages.success(self.request, 'Configuración actualizada correctamente.')
        return super().form_valid(form)


# ==================== API ENDPOINTS ====================

@login_required
def api_transmisiones_hoy(request):
    """
    API que retorna las transmisiones de hoy en formato JSON
    """
    hoy = timezone.now().date()
    transmisiones = TransmisionActual.objects.filter(
        inicio_programado__date=hoy
    ).select_related('cuña', 'programacion')
    
    data = []
    for t in transmisiones:
        data.append({
            'id': t.id,
            'session_id': str(t.session_id),
            'cuña_titulo': t.cuña.titulo,
            'cuña_codigo': t.cuña.codigo,
            'estado': t.estado,
            'inicio_programado': t.inicio_programado.isoformat(),
            'inicio_real': t.inicio_real.isoformat() if t.inicio_real else None,
            'duracion_segundos': t.duracion_segundos,
            'progreso_porcentaje': t.progreso_porcentaje,
        })
    
    return JsonResponse({
        'transmisiones': data,
        'total': len(data),
        'timestamp': timezone.now().isoformat()
    })


@login_required
def api_estadisticas_tiempo_real(request):
    """
    API para estadísticas en tiempo real
    """
    ahora = timezone.now()
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    
    stats = {
        'transmisiones_hoy': TransmisionActual.objects.filter(
            inicio_programado__gte=inicio_dia
        ).count(),
        'completadas_hoy': TransmisionActual.objects.filter(
            inicio_programado__gte=inicio_dia,
            estado='completada'
        ).count(),
        'errores_hoy': TransmisionActual.objects.filter(
            inicio_programado__gte=inicio_dia,
            estado='error'
        ).count(),
        'tiempo_total_hoy': TransmisionActual.objects.filter(
            inicio_programado__gte=inicio_dia,
            duracion_segundos__isnull=False
        ).aggregate(total=Sum('duracion_segundos'))['total'] or 0,
        'sistema_activo': ConfiguracionTransmision.get_configuracion_activa() is not None,
        'timestamp': ahora.isoformat(),
    }
    
    return JsonResponse(stats)


# ==================== VISTAS DE UTILIDAD ====================

@login_required
def exportar_logs(request):
    """
    Exporta logs a CSV
    """
    import csv
    from django.http import HttpResponse
    
    # Obtener parámetros de filtro
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    queryset = LogTransmision.objects.all()
    
    if fecha_desde:
        try:
            fecha = datetime.strptime(fecha_desde, '%Y-%m-%d')
            queryset = queryset.filter(timestamp__gte=fecha)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            queryset = queryset.filter(timestamp__lte=fecha + timedelta(days=1))
        except ValueError:
            pass
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="logs_transmision_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Fecha/Hora',
        'Acción',
        'Nivel',
        'Descripción',
        'Usuario',
        'Cuña',
        'Session ID'
    ])
    
    for log in queryset.order_by('-timestamp')[:1000]:  # Límite de 1000 registros
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.get_accion_display(),
            log.get_nivel_display(),
            log.descripcion,
            log.usuario.username if log.usuario else '',
            log.cuña.codigo if log.cuña else '',
            str(log.transmision.session_id)[:8] if log.transmision else ''
        ])
    
    return response


@login_required
def limpiar_logs_antiguos(request):
    """
    Limpia logs antiguos (más de 90 días)
    """
    if not request.user.is_superuser:
        messages.error(request, 'Solo los administradores pueden realizar esta acción.')
        return redirect('transmission_control:logs_list')
    
    if request.method == 'POST':
        dias = int(request.POST.get('dias', 90))
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        count = LogTransmision.objects.filter(timestamp__lt=fecha_limite).count()
        LogTransmision.objects.filter(timestamp__lt=fecha_limite).delete()
        
        # Crear evento del sistema
        EventoSistema.objects.create(
            tipo_evento='mantenimiento_inicio',
            descripcion=f'Logs antiguos limpiados: {count} registros eliminados (más de {dias} días)',
            usuario=request.user,
            datos_sistema={'logs_eliminados': count, 'dias': dias}
        )
        
        messages.success(request, f'{count} logs antiguos eliminados correctamente.')
        return redirect('transmission_control:logs_list')
    
    return render(request, 'transmission_control/limpiar_logs.html')