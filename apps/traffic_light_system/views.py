"""
Vistas para el Sistema de Semáforos
Sistema PubliTrack - Dashboard y gestión de estados
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView
)
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied
from datetime import datetime, timedelta
import json

from .models import (
    ConfiguracionSemaforo, EstadoSemaforo, HistorialEstadoSemaforo,
    AlertaSemaforo, ResumenEstadosSemaforo
)
from .utils.status_calculator import StatusCalculator, AlertasManager
from .forms import ConfiguracionSemaforoForm, FiltroEstadosForm
from apps.content_management.models import CuñaPublicitaria
from apps.authentication.decorators import permission_required


class TrafficLightPermissionMixin(UserPassesTestMixin):
    """Mixin para verificar permisos del sistema de semáforos"""
    
    def test_func(self):
        return (
            self.request.user.is_authenticated and
            self.request.user.can_view_traffic_light_system()
        )
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('authentication:login')
        raise PermissionDenied("No tienes permisos para acceder al sistema de semáforos")


class DashboardSemaforoView(LoginRequiredMixin, TrafficLightPermissionMixin, TemplateView):
    """Dashboard principal del sistema de semáforos"""
    template_name = 'traffic_light_system/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener estadísticas generales
        calculator = StatusCalculator()
        estadisticas = calculator.obtener_estadisticas_resumen()
        
        # Cuñas que requieren atención inmediata
        cuñas_criticas = EstadoSemaforo.objects.filter(
            color_actual='rojo'
        ).select_related('cuña', 'cuña__cliente', 'cuña__vendedor_asignado')[:10]
        
        # Cuñas próximas a vencer
        cuñas_amarillas = EstadoSemaforo.objects.filter(
            color_actual='amarillo'
        ).select_related('cuña', 'cuña__cliente', 'cuña__vendedor_asignado')[:10]
        
        # Alertas pendientes
        alertas_pendientes = AlertaSemaforo.objects.filter(
            estado='pendiente'
        ).select_related('cuña')[:5]
        
        # Cambios recientes de estado
        cambios_recientes = HistorialEstadoSemaforo.objects.select_related(
            'cuña', 'cuña__cliente'
        )[:10]
        
        # Gráfico de evolución semanal
        datos_grafico = self._obtener_datos_grafico_semanal()
        
        context.update({
            'estadisticas': estadisticas,
            'cuñas_criticas': cuñas_criticas,
            'cuñas_amarillas': cuñas_amarillas,
            'alertas_pendientes': alertas_pendientes,
            'cambios_recientes': cambios_recientes,
            'datos_grafico': datos_grafico,
            'configuracion_activa': ConfiguracionSemaforo.get_active(),
        })
        
        return context
    
    def _obtener_datos_grafico_semanal(self):
        """Obtiene datos para gráfico de evolución semanal"""
        hoy = timezone.now().date()
        hace_7_dias = hoy - timedelta(days=7)
        
        resumen = ResumenEstadosSemaforo.objects.filter(
            periodo='dia',
            fecha__gte=hace_7_dias,
            fecha__lte=hoy
        ).order_by('fecha')
        
        datos = []
        for dia in resumen:
            datos.append({
                'fecha': dia.fecha.strftime('%d/%m'),
                'verde': dia.cuñas_verde,
                'amarillo': dia.cuñas_amarillo,
                'rojo': dia.cuñas_rojo,
                'total': dia.total_cuñas
            })
        
        return datos


class ListaEstadosView(LoginRequiredMixin, TrafficLightPermissionMixin, ListView):
    """Lista de estados de semáforos con filtros"""
    model = EstadoSemaforo
    template_name = 'traffic_light_system/lista_estados.html'
    context_object_name = 'estados'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = EstadoSemaforo.objects.select_related(
            'cuña', 'cuña__cliente', 'cuña__vendedor_asignado', 'cuña__categoria'
        ).order_by('-ultimo_calculo')
        
        # Aplicar filtros
        form = FiltroEstadosForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('color'):
                queryset = queryset.filter(color_actual=form.cleaned_data['color'])
            
            if form.cleaned_data.get('prioridad'):
                queryset = queryset.filter(prioridad=form.cleaned_data['prioridad'])
            
            if form.cleaned_data.get('cliente'):
                queryset = queryset.filter(cuña__cliente=form.cleaned_data['cliente'])
            
            if form.cleaned_data.get('vendedor'):
                queryset = queryset.filter(cuña__vendedor_asignado=form.cleaned_data['vendedor'])
            
            if form.cleaned_data.get('categoria'):
                queryset = queryset.filter(cuña__categoria=form.cleaned_data['categoria'])
            
            if form.cleaned_data.get('requiere_alerta'):
                queryset = queryset.filter(requiere_alerta=True)
            
            if form.cleaned_data.get('buscar'):
                buscar = form.cleaned_data['buscar']
                queryset = queryset.filter(
                    Q(cuña__codigo__icontains=buscar) |
                    Q(cuña__titulo__icontains=buscar) |
                    Q(cuña__cliente__first_name__icontains=buscar) |
                    Q(cuña__cliente__last_name__icontains=buscar) |
                    Q(cuña__cliente__empresa__icontains=buscar)
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_filtros'] = FiltroEstadosForm(self.request.GET)
        
        # Estadísticas del filtro aplicado
        queryset = self.get_queryset()
        context['estadisticas_filtro'] = {
            'total': queryset.count(),
            'verde': queryset.filter(color_actual='verde').count(),
            'amarillo': queryset.filter(color_actual='amarillo').count(),
            'rojo': queryset.filter(color_actual='rojo').count(),
            'gris': queryset.filter(color_actual='gris').count(),
        }
        
        return context


class DetalleEstadoView(LoginRequiredMixin, TrafficLightPermissionMixin, DetailView):
    """Detalle de un estado de semáforo específico"""
    model = EstadoSemaforo
    template_name = 'traffic_light_system/detalle_estado.html'
    context_object_name = 'estado'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Historial de cambios
        historial = HistorialEstadoSemaforo.objects.filter(
            cuña=self.object.cuña
        ).order_by('-fecha_cambio')[:20]
        
        # Alertas relacionadas
        alertas = AlertaSemaforo.objects.filter(
            cuña=self.object.cuña
        ).order_by('-created_at')[:10]
        
        # Recalcular estado actual
        calculator = StatusCalculator()
        estado_calculado = calculator.calcular_estado_cuña(self.object.cuña)
        
        context.update({
            'historial': historial,
            'alertas': alertas,
            'estado_calculado': estado_calculado,
            'cuña': self.object.cuña,
        })
        
        return context


class ConfiguracionSemaforoListView(LoginRequiredMixin, TrafficLightPermissionMixin, ListView):
    """Lista de configuraciones de semáforo"""
    model = ConfiguracionSemaforo
    template_name = 'traffic_light_system/configuraciones.html'
    context_object_name = 'configuraciones'
    
    def test_func(self):
        """Solo administradores pueden ver configuraciones"""
        return (
            super().test_func() and
            self.request.user.es_admin
        )


class ConfiguracionSemaforoCreateView(LoginRequiredMixin, TrafficLightPermissionMixin, CreateView):
    """Crear nueva configuración de semáforo"""
    model = ConfiguracionSemaforo
    form_class = ConfiguracionSemaforoForm
    template_name = 'traffic_light_system/configuracion_form.html'
    success_url = reverse_lazy('traffic_light:configuraciones')
    
    def test_func(self):
        """Solo administradores pueden crear configuraciones"""
        return (
            super().test_func() and
            self.request.user.es_admin
        )
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Configuración creada exitosamente.')
        return super().form_valid(form)


class ConfiguracionSemaforoUpdateView(LoginRequiredMixin, TrafficLightPermissionMixin, UpdateView):
    """Editar configuración de semáforo"""
    model = ConfiguracionSemaforo
    form_class = ConfiguracionSemaforoForm
    template_name = 'traffic_light_system/configuracion_form.html'
    success_url = reverse_lazy('traffic_light:configuraciones')
    
    def test_func(self):
        """Solo administradores pueden editar configuraciones"""
        return (
            super().test_func() and
            self.request.user.es_admin
        )
    
    def form_valid(self, form):
        messages.success(self.request, 'Configuración actualizada exitosamente.')
        return super().form_valid(form)


class AlertasListView(LoginRequiredMixin, TrafficLightPermissionMixin, ListView):
    """Lista de alertas del sistema"""
    model = AlertaSemaforo
    template_name = 'traffic_light_system/alertas.html'
    context_object_name = 'alertas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = AlertaSemaforo.objects.select_related(
            'cuña', 'estado_semaforo'
        ).order_by('-created_at')
        
        # Filtrar por estado si se especifica
        estado_filtro = self.request.GET.get('estado')
        if estado_filtro:
            queryset = queryset.filter(estado=estado_filtro)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas de alertas
        context['stats_alertas'] = {
            'pendientes': AlertaSemaforo.objects.filter(estado='pendiente').count(),
            'enviadas': AlertaSemaforo.objects.filter(estado='enviada').count(),
            'errores': AlertaSemaforo.objects.filter(estado='error').count(),
        }
        
        return context


class HistorialEstadosView(LoginRequiredMixin, TrafficLightPermissionMixin, ListView):
    """Historial de cambios de estados"""
    model = HistorialEstadoSemaforo
    template_name = 'traffic_light_system/historial.html'
    context_object_name = 'cambios'
    paginate_by = 30
    
    def get_queryset(self):
        queryset = HistorialEstadoSemaforo.objects.select_related(
            'cuña', 'cuña__cliente', 'usuario_trigger'
        ).order_by('-fecha_cambio')
        
        # Filtrar por cuña si se especifica
        cuña_id = self.request.GET.get('cuña')
        if cuña_id:
            queryset = queryset.filter(cuña_id=cuña_id)
        
        # Filtrar por rango de fechas
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_cambio__date__gte=fecha_desde)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_cambio__date__lte=fecha_hasta)
            except ValueError:
                pass
        
        return queryset


# VISTAS AJAX Y API

@login_required
@require_http_methods(["POST"])
def recalcular_estado_cuña(request, cuña_id):
    """Recalcula el estado de una cuña específica"""
    try:
        cuña = get_object_or_404(CuñaPublicitaria, id=cuña_id)
        
        # Verificar permisos
        if not request.user.can_manage_content():
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        calculator = StatusCalculator()
        estado = calculator.actualizar_estado_cuña(cuña)
        
        return JsonResponse({
            'success': True,
            'color': estado.color_actual,
            'prioridad': estado.prioridad,
            'razon': estado.razon_color,
            'dias_restantes': estado.dias_restantes,
            'mensaje': 'Estado recalculado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def recalcular_todos_estados(request):
    """Recalcula todos los estados del sistema"""
    try:
        # Solo administradores pueden hacer esto
        if not request.user.es_admin:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        calculator = StatusCalculator()
        stats = calculator.actualizar_todas_las_cuñas()
        
        return JsonResponse({
            'success': True,
            'estadisticas': stats,
            'mensaje': 'Todos los estados han sido recalculados'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def activar_configuracion(request, config_id):
    """Activa una configuración específica"""
    try:
        # Solo administradores
        if not request.user.es_admin:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        config = get_object_or_404(ConfiguracionSemaforo, id=config_id)
        
        # Desactivar todas las demás y activar esta
        ConfiguracionSemaforo.objects.update(is_active=False)
        config.is_active = True
        config.save()
        
        # Recalcular todos los estados con la nueva configuración
        calculator = StatusCalculator(config)
        stats = calculator.actualizar_todas_las_cuñas()
        
        return JsonResponse({
            'success': True,
            'configuracion': config.nombre,
            'estadisticas': stats,
            'mensaje': f'Configuración "{config.nombre}" activada y estados recalculados'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def generar_alertas(request):
    """Genera alertas pendientes manualmente"""
    try:
        # Solo vendedores y administradores
        if not request.user.can_view_reports():
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        manager = AlertasManager()
        stats = manager.generar_alertas_pendientes()
        
        return JsonResponse({
            'success': True,
            'estadisticas': stats,
            'mensaje': f'{stats["alertas_creadas"]} alertas generadas'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def marcar_alerta_leida(request, alerta_id):
    """Marca una alerta como leída/procesada"""
    try:
        alerta = get_object_or_404(AlertaSemaforo, id=alerta_id)
        
        # Verificar que el usuario puede ver esta alerta
        if not (request.user.es_admin or 
                request.user == alerta.cuña.vendedor_asignado or
                request.user in alerta.usuarios_destino.all()):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        alerta.estado = 'enviada'
        alerta.fecha_enviada = timezone.now()
        alerta.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Alerta marcada como procesada'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_estadisticas_dashboard(request):
    """API para obtener estadísticas actualizadas del dashboard"""
    try:
        calculator = StatusCalculator()
        estadisticas = calculator.obtener_estadisticas_resumen()
        
        return JsonResponse({
            'success': True,
            'estadisticas': estadisticas
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def actualizar_semaforo_manual(request, cuna_id):
    """API para forzar actualización manual del semáforo"""
    try:
        from apps.content_management.models import CuñaPublicitaria
        from .utils.status_calculator import StatusCalculator
        
        cuna = CuñaPublicitaria.objects.get(pk=cuna_id)
        calculator = StatusCalculator()
        estado_semaforo = calculator.actualizar_estado_cuña(cuna, crear_historial=True)
        
        return JsonResponse({
            'success': True,
            'message': f'Semáforo actualizado manualmente para {cuna.codigo}',
            'color_actual': estado_semaforo.color_actual,
            'razon': estado_semaforo.razon_color,
            'prioridad': estado_semaforo.prioridad
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@login_required
def api_cuñas_por_estado(request, color):
    """API para obtener cuñas filtradas por color de estado"""
    try:
        # Validar color
        colores_validos = ['verde', 'amarillo', 'rojo', 'gris']
        if color not in colores_validos:
            return JsonResponse({'error': 'Color inválido'}, status=400)
        
        estados = EstadoSemaforo.objects.filter(
            color_actual=color
        ).select_related('cuña', 'cuña__cliente')[:20]
        
        cuñas_data = []
        for estado in estados:
            cuñas_data.append({
                'id': estado.cuña.id,
                'codigo': estado.cuña.codigo,
                'titulo': estado.cuña.titulo,
                'cliente': estado.cuña.cliente.get_full_name(),
                'dias_restantes': estado.dias_restantes,
                'prioridad': estado.get_prioridad_display(),
                'razon': estado.razon_color,
                'url': estado.cuña.get_absolute_url()
            })
        
        return JsonResponse({
            'success': True,
            'cuñas': cuñas_data,
            'total': len(cuñas_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def exportar_reporte_estados(request):
    """Exporta un reporte de estados en CSV"""
    import csv
    from django.http import HttpResponse
    
    try:
        # Verificar permisos
        if not request.user.can_view_reports():
            raise PermissionDenied("Sin permisos para exportar reportes")
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_estados_semaforo.csv"'
        
        writer = csv.writer(response)
        
        # Escribir encabezados
        writer.writerow([
            'Código Cuña', 'Título', 'Cliente', 'Vendedor', 'Estado Semáforo',
            'Prioridad', 'Días Restantes', 'Porcentaje Tiempo', 'Razón',
            'Requiere Alerta', 'Último Cálculo'
        ])
        
        # Obtener datos
        estados = EstadoSemaforo.objects.select_related(
            'cuña', 'cuña__cliente', 'cuña__vendedor_asignado'
        ).all()
        
        # Escribir datos
        for estado in estados:
            writer.writerow([
                estado.cuña.codigo,
                estado.cuña.titulo,
                estado.cuña.cliente.get_full_name(),
                estado.cuña.vendedor_asignado.get_full_name() if estado.cuña.vendedor_asignado else '',
                estado.get_color_actual_display(),
                estado.get_prioridad_display(),
                estado.dias_restantes or '',
                estado.porcentaje_tiempo_transcurrido or '',
                estado.razon_color,
                'Sí' if estado.requiere_alerta else 'No',
                estado.ultimo_calculo.strftime('%d/%m/%Y %H:%M')
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al exportar reporte: {str(e)}')
        return redirect('traffic_light:dashboard')


# VISTAS PARA WIDGETS

class WidgetEstadosView(LoginRequiredMixin, TemplateView):
    """Widget de estados para incluir en otras páginas"""
    template_name = 'traffic_light_system/widgets/estados_widget.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener estadísticas básicas
        calculator = StatusCalculator()
        estadisticas = calculator.obtener_estadisticas_resumen()
        
        context['estadisticas'] = estadisticas
        return context


class WidgetAlertasView(LoginRequiredMixin, TemplateView):
    """Widget de alertas para incluir en otras páginas"""
    template_name = 'traffic_light_system/widgets/alertas_widget.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Alertas pendientes para el usuario actual
        alertas = AlertaSemaforo.objects.filter(
            estado='pendiente',
            mostrar_dashboard=True
        ).select_related('cuña')
        
        # Filtrar según el rol del usuario
        if self.request.user.es_vendedor:
            alertas = alertas.filter(
                Q(cuña__vendedor_asignado=self.request.user) |
                Q(usuarios_destino=self.request.user)
            )
        elif not self.request.user.es_admin:
            alertas = alertas.filter(usuarios_destino=self.request.user)
        
        context['alertas'] = alertas[:5]  # Solo las 5 más recientes
        return context