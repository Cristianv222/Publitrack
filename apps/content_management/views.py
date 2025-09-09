"""
Vistas para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Gestión de cuñas publicitarias y archivos de audio
"""

import json
from decimal import Decimal
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.base import TemplateView

from .models import (
    CategoriaPublicitaria, 
    TipoContrato, 
    ArchivoAudio, 
    CuñaPublicitaria, 
    HistorialCuña
)
from .forms import (
    CategoriaPublicitariaForm,
    TipoContratoForm,
    ArchivoAudioForm,
    CuñaPublicitariaForm,
    CuñaAprobacionForm,
    CuñaFiltroForm
)

User = get_user_model()

# Funciones auxiliares para tests de usuario
def es_vendedor(user):
    """Verifica si el usuario es vendedor"""
    return user.groups.filter(name='Vendedores').exists()

def es_cliente(user):
    """Verifica si el usuario es cliente"""
    return user.groups.filter(name='Clientes').exists()

def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return user.groups.filter(name='Administradores').exists()

def es_supervisor(user):
    """Verifica si el usuario es supervisor"""
    return user.groups.filter(name='Supervisores').exists()

def puede_gestionar_cuñas(user):
    """Verifica si el usuario puede gestionar cuñas"""
    return user.groups.filter(name__in=['Administradores', 'Supervisores', 'Vendedores']).exists()

def puede_aprobar_cuñas(user):
    """Verifica si el usuario puede aprobar cuñas"""
    return user.groups.filter(name__in=['Administradores', 'Supervisores']).exists()

# ==================== DASHBOARD ====================

@login_required
def dashboard_content(request):
    """Dashboard principal del módulo de contenido"""
    context = {
        'total_cuñas': CuñaPublicitaria.objects.count(),
        'cuñas_activas': CuñaPublicitaria.objects.filter(estado='activa').count(),
        'cuñas_pendientes': CuñaPublicitaria.objects.filter(estado='pendiente_revision').count(),
        'cuñas_por_vencer': CuñaPublicitaria.objects.filter(
            fecha_fin__lte=timezone.now().date() + timedelta(days=7),
            estado='activa'
        ).count(),
    }
    
    # Filtrar por rol de usuario
    if es_cliente(request.user):
        context.update({
            'mis_cuñas': CuñaPublicitaria.objects.filter(cliente=request.user).count(),
            'mis_cuñas_activas': CuñaPublicitaria.objects.filter(
                cliente=request.user, estado='activa'
            ).count(),
        })
    elif es_vendedor(request.user):
        context.update({
            'mis_ventas': CuñaPublicitaria.objects.filter(vendedor_asignado=request.user).count(),
            'ventas_mes': CuñaPublicitaria.objects.filter(
                vendedor_asignado=request.user,
                created_at__month=timezone.now().month
            ).count(),
        })
    
    return render(request, 'content/dashboard.html', context)

# ==================== CATEGORIAS PUBLICITARIAS ====================

@method_decorator([login_required, permission_required('content_management.view_categoriapublicitaria')], name='dispatch')
class CategoriaListView(ListView):
    """Lista de categorías publicitarias"""
    model = CategoriaPublicitaria
    template_name = 'content/categoria_list.html'
    context_object_name = 'categorias'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CategoriaPublicitaria.objects.all()
        
        # Filtro por búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(descripcion__icontains=search)
            )
        
        # Filtro por estado
        activa = self.request.GET.get('activa')
        if activa:
            queryset = queryset.filter(is_active=activa == 'true')
        
        return queryset.order_by('nombre')

@method_decorator([login_required, permission_required('content_management.view_categoriapublicitaria')], name='dispatch')
class CategoriaDetailView(DetailView):
    """Detalle de categoría publicitaria"""
    model = CategoriaPublicitaria
    template_name = 'content/categoria_detail.html'
    context_object_name = 'categoria'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cuñas_categoria'] = self.object.cuñas.all()[:10]
        context['total_cuñas'] = self.object.cuñas.count()
        return context

@method_decorator([login_required, permission_required('content_management.add_categoriapublicitaria')], name='dispatch')
class CategoriaCreateView(CreateView):
    """Crear categoría publicitaria"""
    model = CategoriaPublicitaria
    form_class = CategoriaPublicitariaForm
    template_name = 'content/categoria_form.html'
    success_url = reverse_lazy('content:categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada exitosamente.')
        return super().form_valid(form)

@method_decorator([login_required, permission_required('content_management.change_categoriapublicitaria')], name='dispatch')
class CategoriaUpdateView(UpdateView):
    """Actualizar categoría publicitaria"""
    model = CategoriaPublicitaria
    form_class = CategoriaPublicitariaForm
    template_name = 'content/categoria_form.html'
    success_url = reverse_lazy('content:categoria_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada exitosamente.')
        return super().form_valid(form)

@login_required
@permission_required('content_management.delete_categoriapublicitaria')
@require_POST
def categoria_delete(request, pk):
    """Eliminar categoría publicitaria"""
    categoria = get_object_or_404(CategoriaPublicitaria, pk=pk)
    
    # Verificar que no tenga cuñas asociadas
    if categoria.cuñas.exists():
        messages.error(request, 'No se puede eliminar la categoría porque tiene cuñas asociadas.')
        return redirect('content:categoria_detail', pk=pk)
    
    categoria.delete()
    messages.success(request, 'Categoría eliminada exitosamente.')
    return redirect('content:categoria_list')

# ==================== TIPOS DE CONTRATO ====================

@method_decorator([login_required, permission_required('content_management.view_tipocontrato')], name='dispatch')
class TipoContratoListView(ListView):
    """Lista de tipos de contrato"""
    model = TipoContrato
    template_name = 'content/tipo_contrato_list.html'
    context_object_name = 'tipos_contrato'
    paginate_by = 20

@method_decorator([login_required, permission_required('content_management.add_tipocontrato')], name='dispatch')
class TipoContratoCreateView(CreateView):
    """Crear tipo de contrato"""
    model = TipoContrato
    form_class = TipoContratoForm
    template_name = 'content/tipo_contrato_form.html'
    success_url = reverse_lazy('content:tipo_contrato_list')

@method_decorator([login_required, permission_required('content_management.change_tipocontrato')], name='dispatch')
class TipoContratoUpdateView(UpdateView):
    """Actualizar tipo de contrato"""
    model = TipoContrato
    form_class = TipoContratoForm
    template_name = 'content/tipo_contrato_form.html'
    success_url = reverse_lazy('content:tipo_contrato_list')

# ==================== ARCHIVOS DE AUDIO ====================

@method_decorator([login_required, permission_required('content_management.view_archivoaudio')], name='dispatch')
class ArchivoAudioListView(ListView):
    """Lista de archivos de audio"""
    model = ArchivoAudio
    template_name = 'content/audio_list.html'
    context_object_name = 'audios'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ArchivoAudio.objects.select_related('subido_por')
        
        # Filtrar por usuario si es cliente
        if es_cliente(self.request.user):
            # Solo ver archivos de cuñas propias
            queryset = queryset.filter(cuñas__cliente=self.request.user).distinct()
        
        return queryset.order_by('-fecha_subida')

@method_decorator([login_required, permission_required('content_management.view_archivoaudio')], name='dispatch')
class ArchivoAudioDetailView(DetailView):
    """Detalle de archivo de audio"""
    model = ArchivoAudio
    template_name = 'content/audio_detail.html'
    context_object_name = 'audio'
    
    def get_object(self):
        obj = super().get_object()
        
        # Verificar permisos para clientes
        if es_cliente(self.request.user):
            if not obj.cuñas.filter(cliente=self.request.user).exists():
                raise Http404("Audio no encontrado")
        
        return obj

@method_decorator([login_required, permission_required('content_management.add_archivoaudio')], name='dispatch')
class ArchivoAudioCreateView(CreateView):
    """Subir archivo de audio"""
    model = ArchivoAudio
    form_class = ArchivoAudioForm
    template_name = 'content/audio_form.html'
    success_url = reverse_lazy('content:audio_list')
    
    def form_valid(self, form):
        form.instance.subido_por = self.request.user
        messages.success(self.request, 'Archivo de audio subido exitosamente.')
        return super().form_valid(form)

@login_required
@permission_required('content_management.delete_archivoaudio')
@require_POST
def audio_delete(request, pk):
    """Eliminar archivo de audio"""
    audio = get_object_or_404(ArchivoAudio, pk=pk)
    
    # Verificar permisos
    if es_cliente(request.user) and not audio.cuñas.filter(cliente=request.user).exists():
        return HttpResponseForbidden("No tiene permisos para eliminar este archivo")
    
    # Verificar que no esté siendo usado
    if audio.cuñas.exists():
        messages.error(request, 'No se puede eliminar el archivo porque está siendo usado en cuñas.')
        return redirect('content:audio_detail', pk=pk)
    
    audio.delete()
    messages.success(request, 'Archivo de audio eliminado exitosamente.')
    return redirect('content:audio_list')

# ==================== CUÑAS PUBLICITARIAS ====================

@method_decorator([login_required, permission_required('content_management.view_cuñapublicitaria')], name='dispatch')
class CuñaListView(ListView):
    """Lista de cuñas publicitarias"""
    model = CuñaPublicitaria
    template_name = 'content/cuña_list.html'
    context_object_name = 'cuñas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = CuñaPublicitaria.objects.select_related(
            'cliente', 'vendedor_asignado', 'categoria', 'tipo_contrato'
        )
        
        # Filtrar por rol de usuario
        if es_cliente(self.request.user):
            queryset = queryset.filter(cliente=self.request.user)
        elif es_vendedor(self.request.user):
            queryset = queryset.filter(vendedor_asignado=self.request.user)
        
        # Aplicar filtros del formulario
        form = CuñaFiltroForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('estado'):
                queryset = queryset.filter(estado=form.cleaned_data['estado'])
            
            if form.cleaned_data.get('categoria'):
                queryset = queryset.filter(categoria=form.cleaned_data['categoria'])
            
            if form.cleaned_data.get('vendedor'):
                queryset = queryset.filter(vendedor_asignado=form.cleaned_data['vendedor'])
            
            if form.cleaned_data.get('fecha_inicio'):
                queryset = queryset.filter(fecha_inicio__gte=form.cleaned_data['fecha_inicio'])
            
            if form.cleaned_data.get('fecha_fin'):
                queryset = queryset.filter(fecha_fin__lte=form.cleaned_data['fecha_fin'])
        
        # Búsqueda por texto
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(titulo__icontains=search) |
                Q(cliente__first_name__icontains=search) |
                Q(cliente__last_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filtro_form'] = CuñaFiltroForm(self.request.GET)
        context['search'] = self.request.GET.get('search', '')
        return context

@method_decorator([login_required, permission_required('content_management.view_cuñapublicitaria')], name='dispatch')
class CuñaDetailView(DetailView):
    """Detalle de cuña publicitaria"""
    model = CuñaPublicitaria
    template_name = 'content/cuña_detail.html'
    context_object_name = 'cuña'
    
    def get_object(self):
        obj = super().get_object()
        
        # Verificar permisos para clientes
        if es_cliente(self.request.user) and obj.cliente != self.request.user:
            raise Http404("Cuña no encontrada")
        
        # Verificar permisos para vendedores
        if es_vendedor(self.request.user) and obj.vendedor_asignado != self.request.user:
            raise Http404("Cuña no encontrada")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historial'] = self.object.historial.all()[:10]
        context['puede_aprobar'] = puede_aprobar_cuñas(self.request.user)
        context['puede_editar'] = (
            self.object.permite_edicion and 
            (es_administrador(self.request.user) or 
             self.object.vendedor_asignado == self.request.user)
        )
        return context

@method_decorator([login_required, permission_required('content_management.add_cuñapublicitaria')], name='dispatch')
class CuñaCreateView(UserPassesTestMixin, CreateView):
    """Crear cuña publicitaria"""
    model = CuñaPublicitaria
    form_class = CuñaPublicitariaForm
    template_name = 'content/cuña_form.html'
    
    def test_func(self):
        return puede_gestionar_cuñas(self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Si es vendedor, asignarse automáticamente
        if es_vendedor(self.request.user):
            form.instance.vendedor_asignado = self.request.user
        
        messages.success(self.request, f'Cuña "{form.instance.titulo}" creada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('content:cuña_detail', kwargs={'pk': self.object.pk})

@method_decorator([login_required, permission_required('content_management.change_cuñapublicitaria')], name='dispatch')
class CuñaUpdateView(UserPassesTestMixin, UpdateView):
    """Actualizar cuña publicitaria"""
    model = CuñaPublicitaria
    form_class = CuñaPublicitariaForm
    template_name = 'content/cuña_form.html'
    
    def test_func(self):
        obj = self.get_object()
        if not obj.permite_edicion:
            return False
        
        return (
            es_administrador(self.request.user) or
            obj.vendedor_asignado == self.request.user or
            obj.cliente == self.request.user
        )
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Marcar usuario que modifica para el historial
        form.instance._user_modificador = self.request.user
        messages.success(self.request, f'Cuña "{form.instance.titulo}" actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('content:cuña_detail', kwargs={'pk': self.object.pk})

@login_required
@user_passes_test(puede_aprobar_cuñas)
@require_POST
def cuña_aprobar(request, pk):
    """Aprobar cuña publicitaria"""
    cuña = get_object_or_404(CuñaPublicitaria, pk=pk)
    
    if cuña.estado != 'pendiente_revision':
        messages.error(request, 'La cuña no está en estado pendiente de revisión.')
        return redirect('content:cuña_detail', pk=pk)
    
    cuña.aprobar(request.user)
    messages.success(request, f'Cuña "{cuña.titulo}" aprobada exitosamente.')
    
    return redirect('content:cuña_detail', pk=pk)

@login_required
@user_passes_test(puede_gestionar_cuñas)
@require_POST
def cuña_activar(request, pk):
    """Activar cuña publicitaria"""
    cuña = get_object_or_404(CuñaPublicitaria, pk=pk)
    
    # Verificar permisos específicos
    if es_vendedor(request.user) and cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos para activar esta cuña")
    
    if cuña.estado != 'aprobada':
        messages.error(request, 'La cuña debe estar aprobada para poder activarla.')
        return redirect('content:cuña_detail', pk=pk)
    
    cuña.activar()
    messages.success(request, f'Cuña "{cuña.titulo}" activada exitosamente.')
    
    return redirect('content:cuña_detail', pk=pk)

@login_required
@user_passes_test(puede_gestionar_cuñas)
@require_POST
def cuña_pausar(request, pk):
    """Pausar cuña publicitaria"""
    cuña = get_object_or_404(CuñaPublicitaria, pk=pk)
    
    # Verificar permisos específicos
    if es_vendedor(request.user) and cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos para pausar esta cuña")
    
    if cuña.estado != 'activa':
        messages.error(request, 'Solo se pueden pausar cuñas activas.')
        return redirect('content:cuña_detail', pk=pk)
    
    cuña.pausar()
    messages.success(request, f'Cuña "{cuña.titulo}" pausada exitosamente.')
    
    return redirect('content:cuña_detail', pk=pk)

@login_required
@user_passes_test(puede_gestionar_cuñas)
@require_POST
def cuña_finalizar(request, pk):
    """Finalizar cuña publicitaria"""
    cuña = get_object_or_404(CuñaPublicitaria, pk=pk)
    
    # Verificar permisos específicos
    if es_vendedor(request.user) and cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos para finalizar esta cuña")
    
    if cuña.estado not in ['activa', 'pausada']:
        messages.error(request, 'Solo se pueden finalizar cuñas activas o pausadas.')
        return redirect('content:cuña_detail', pk=pk)
    
    cuña.finalizar()
    messages.success(request, f'Cuña "{cuña.titulo}" finalizada exitosamente.')
    
    return redirect('content:cuña_detail', pk=pk)

# ==================== VISTAS AJAX ====================

@login_required
@require_http_methods(["GET"])
def cuña_estado_ajax(request, pk):
    """Obtener estado actual de cuña vía AJAX"""
    try:
        cuña = CuñaPublicitaria.objects.get(pk=pk)
        
        # Verificar permisos
        if es_cliente(request.user) and cuña.cliente != request.user:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        if es_vendedor(request.user) and cuña.vendedor_asignado != request.user:
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = {
            'estado': cuña.estado,
            'estado_display': cuña.get_estado_display(),
            'semaforo': cuña.semaforo_estado,
            'dias_restantes': cuña.dias_restantes,
            'esta_activa': cuña.esta_activa,
            'esta_vencida': cuña.esta_vencida,
        }
        
        return JsonResponse(data)
        
    except CuñaPublicitaria.DoesNotExist:
        return JsonResponse({'error': 'Cuña no encontrada'}, status=404)

@login_required
@require_http_methods(["GET"])
def audio_metadatos_ajax(request, pk):
    """Obtener metadatos de audio vía AJAX"""
    try:
        audio = ArchivoAudio.objects.get(pk=pk)
        
        # Verificar permisos básicos
        if es_cliente(request.user):
            if not audio.cuñas.filter(cliente=request.user).exists():
                return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        data = {
            'duracion_segundos': audio.duracion_segundos,
            'duracion_formateada': audio.duracion_formateada,
            'tamaño_formateado': audio.tamaño_formateado,
            'formato': audio.formato,
            'calidad': audio.calidad,
            'bitrate': audio.bitrate,
            'sample_rate': audio.sample_rate,
            'canales': audio.canales,
        }
        
        return JsonResponse(data)
        
    except ArchivoAudio.DoesNotExist:
        return JsonResponse({'error': 'Audio no encontrado'}, status=404)

@login_required
@require_http_methods(["GET"])
def estadisticas_dashboard_ajax(request):
    """Obtener estadísticas para dashboard vía AJAX"""
    
    # Estadísticas generales
    stats = {
        'total_cuñas': CuñaPublicitaria.objects.count(),
        'cuñas_activas': CuñaPublicitaria.objects.filter(estado='activa').count(),
        'cuñas_pendientes': CuñaPublicitaria.objects.filter(estado='pendiente_revision').count(),
        'cuñas_por_vencer': CuñaPublicitaria.objects.filter(
            fecha_fin__lte=timezone.now().date() + timedelta(days=7),
            estado='activa'
        ).count(),
    }
    
    # Estadísticas por rol
    if es_cliente(request.user):
        stats.update({
            'mis_cuñas': CuñaPublicitaria.objects.filter(cliente=request.user).count(),
            'mis_cuñas_activas': CuñaPublicitaria.objects.filter(
                cliente=request.user, estado='activa'
            ).count(),
        })
    elif es_vendedor(request.user):
        stats.update({
            'mis_ventas': CuñaPublicitaria.objects.filter(vendedor_asignado=request.user).count(),
            'ventas_mes': CuñaPublicitaria.objects.filter(
                vendedor_asignado=request.user,
                created_at__month=timezone.now().month
            ).count(),
        })
    
    return JsonResponse(stats)

# ==================== REPORTES ====================

@login_required
@user_passes_test(lambda u: u.groups.filter(name__in=['Administradores', 'Supervisores']).exists())
def reporte_cuñas(request):
    """Reporte de cuñas publicitarias"""
    
    # Estadísticas por estado
    stats_estado = CuñaPublicitaria.objects.values('estado').annotate(
        count=Count('id')
    ).order_by('estado')
    
    # Estadísticas por categoría
    stats_categoria = CuñaPublicitaria.objects.values(
        'categoria__nombre'
    ).annotate(
        count=Count('id'),
        total_ingresos=Sum('precio_total')
    ).order_by('-count')
    
    # Estadísticas por vendedor
    stats_vendedor = CuñaPublicitaria.objects.values(
        'vendedor_asignado__first_name',
        'vendedor_asignado__last_name'
    ).annotate(
        count=Count('id'),
        total_ingresos=Sum('precio_total')
    ).order_by('-count')
    
    # Cuñas próximas a vencer
    cuñas_vencimiento = CuñaPublicitaria.objects.filter(
        fecha_fin__lte=timezone.now().date() + timedelta(days=30),
        estado__in=['activa', 'aprobada']
    ).order_by('fecha_fin')
    
    context = {
        'stats_estado': stats_estado,
        'stats_categoria': stats_categoria,
        'stats_vendedor': stats_vendedor,
        'cuñas_vencimiento': cuñas_vencimiento,
    }
    
    return render(request, 'content/reporte_cuñas.html', context)

# ==================== HISTORIAL ====================

@method_decorator([login_required, permission_required('content_management.view_historialcuña')], name='dispatch')
class HistorialCuñaListView(ListView):
    """Lista de historial de cuñas"""
    model = HistorialCuña
    template_name = 'content/historial_list.html'
    context_object_name = 'historiales'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = HistorialCuña.objects.select_related('cuña', 'usuario')
        
        # Filtrar por cuña específica si se proporciona
        cuña_id = self.request.GET.get('cuña')
        if cuña_id:
            queryset = queryset.filter(cuña_id=cuña_id)
        
        # Filtrar por rol de usuario
        if es_cliente(self.request.user):
            queryset = queryset.filter(cuña__cliente=self.request.user)
        elif es_vendedor(self.request.user):
            queryset = queryset.filter(cuña__vendedor_asignado=self.request.user)
        
        return queryset.order_by('-fecha')