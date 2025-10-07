"""
Vistas para el módulo de Gestión de Contenido Publicitario
Sistema PubliTrack - Gestión de cuñas publicitarias, archivos de audio y CONTRATOS
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
from django.http import JsonResponse, HttpResponseForbidden, Http404, FileResponse, HttpResponse
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
    HistorialCuña,
    PlantillaContrato,
    ContratoGenerado
)
from .forms import (
    CategoriaPublicitariaForm,
    TipoContratoForm,
    ArchivoAudioForm,
    CuñaPublicitariaForm,
    CuñaAprobacionForm,
    CuñaFiltroForm,
    PlantillaContratoForm,
    ContratoGeneradoForm
)

User = get_user_model()

# ==================== FUNCIONES AUXILIARES ====================

def es_vendedor(user):
    """Verifica si el usuario es vendedor"""
    return user.rol == 'vendedor' if hasattr(user, 'rol') else user.groups.filter(name='Vendedores').exists()

def es_cliente(user):
    """Verifica si el usuario es cliente"""
    return user.rol == 'cliente' if hasattr(user, 'rol') else user.groups.filter(name='Clientes').exists()

def es_administrador(user):
    """Verifica si el usuario es administrador"""
    return user.rol == 'admin' if hasattr(user, 'rol') else user.groups.filter(name='Administradores').exists()

def es_supervisor(user):
    """Verifica si el usuario es supervisor"""
    return user.groups.filter(name='Supervisores').exists()

def puede_gestionar_cuñas(user):
    """Verifica si el usuario puede gestionar cuñas"""
    if hasattr(user, 'rol'):
        return user.rol in ['admin', 'vendedor']
    return user.groups.filter(name__in=['Administradores', 'Supervisores', 'Vendedores']).exists()

def puede_aprobar_cuñas(user):
    """Verifica si el usuario puede aprobar cuñas"""
    if hasattr(user, 'rol'):
        return user.rol == 'admin'
    return user.groups.filter(name__in=['Administradores', 'Supervisores']).exists()

def puede_gestionar_contratos(user):
    """Verifica si el usuario puede gestionar contratos"""
    if hasattr(user, 'rol'):
        return user.rol in ['admin', 'vendedor']
    return user.groups.filter(name__in=['Administradores', 'Vendedores']).exists()

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
        'total_contratos': ContratoGenerado.objects.count(),
        'contratos_activos': ContratoGenerado.objects.filter(estado='activo').count(),
    }
    
    # Filtrar por rol de usuario
    if es_cliente(request.user):
        context.update({
            'mis_cuñas': CuñaPublicitaria.objects.filter(cliente=request.user).count(),
            'mis_cuñas_activas': CuñaPublicitaria.objects.filter(
                cliente=request.user, estado='activa'
            ).count(),
            'mis_contratos': ContratoGenerado.objects.filter(cliente=request.user).count(),
        })
    elif es_vendedor(request.user):
        context.update({
            'mis_ventas': CuñaPublicitaria.objects.filter(vendedor_asignado=request.user).count(),
            'ventas_mes': CuñaPublicitaria.objects.filter(
                vendedor_asignado=request.user,
                created_at__month=timezone.now().month
            ).count(),
            'contratos_generados_mes': ContratoGenerado.objects.filter(
                generado_por=request.user,
                fecha_generacion__month=timezone.now().month
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
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) | 
                Q(descripcion__icontains=search)
            )
        
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
        
        if es_cliente(self.request.user):
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
    
    if es_cliente(request.user) and not audio.cuñas.filter(cliente=request.user).exists():
        return HttpResponseForbidden("No tiene permisos para eliminar este archivo")
    
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
        
        if es_cliente(self.request.user):
            queryset = queryset.filter(cliente=self.request.user)
        elif es_vendedor(self.request.user):
            queryset = queryset.filter(vendedor_asignado=self.request.user)
        
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
        
        if es_cliente(self.request.user) and obj.cliente != self.request.user:
            raise Http404("Cuña no encontrada")
        
        if es_vendedor(self.request.user) and obj.vendedor_asignado != self.request.user:
            raise Http404("Cuña no encontrada")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historial'] = self.object.historial.all()[:10]
        context['contratos'] = self.object.contratos.all()
        context['puede_aprobar'] = puede_aprobar_cuñas(self.request.user)
        context['puede_generar_contrato'] = puede_gestionar_contratos(self.request.user)
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
    
    if es_vendedor(request.user) and cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos para finalizar esta cuña")
    
    if cuña.estado not in ['activa', 'pausada']:
        messages.error(request, 'Solo se pueden finalizar cuñas activas o pausadas.')
        return redirect('content:cuña_detail', pk=pk)
    
    cuña.finalizar()
    messages.success(request, f'Cuña "{cuña.titulo}" finalizada exitosamente.')
    
    return redirect('content:cuña_detail', pk=pk)

# ==================== PLANTILLAS DE CONTRATO ====================

@method_decorator([login_required, user_passes_test(es_administrador)], name='dispatch')
class PlantillaContratoListView(ListView):
    """Lista de plantillas de contrato"""
    model = PlantillaContrato
    template_name = 'content/plantilla_contrato_list.html'
    context_object_name = 'plantillas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = PlantillaContrato.objects.all()
        
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_contrato=tipo)
        
        activa = self.request.GET.get('activa')
        if activa:
            queryset = queryset.filter(is_active=activa == 'true')
        
        return queryset.order_by('-is_default', '-created_at')

@method_decorator([login_required, user_passes_test(es_administrador)], name='dispatch')
class PlantillaContratoDetailView(DetailView):
    """Detalle de plantilla de contrato"""
    model = PlantillaContrato
    template_name = 'content/plantilla_contrato_detail.html'
    context_object_name = 'plantilla'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contratos_generados'] = self.object.contratos_generados.all()[:10]
        context['total_contratos'] = self.object.contratos_generados.count()
        return context

@method_decorator([login_required, user_passes_test(es_administrador)], name='dispatch')
class PlantillaContratoCreateView(CreateView):
    """Crear plantilla de contrato"""
    model = PlantillaContrato
    form_class = PlantillaContratoForm
    template_name = 'content/plantilla_contrato_form.html'
    success_url = reverse_lazy('content:plantilla_contrato_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Plantilla de contrato creada exitosamente.')
        return super().form_valid(form)

@method_decorator([login_required, user_passes_test(es_administrador)], name='dispatch')
class PlantillaContratoUpdateView(UpdateView):
    """Actualizar plantilla de contrato"""
    model = PlantillaContrato
    form_class = PlantillaContratoForm
    template_name = 'content/plantilla_contrato_form.html'
    success_url = reverse_lazy('content:plantilla_contrato_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Plantilla actualizada exitosamente.')
        return super().form_valid(form)

@login_required
@user_passes_test(es_administrador)
@require_POST
def plantilla_contrato_delete(request, pk):
    """Eliminar plantilla de contrato"""
    plantilla = get_object_or_404(PlantillaContrato, pk=pk)
    
    if plantilla.contratos_generados.exists():
        messages.error(request, 'No se puede eliminar la plantilla porque tiene contratos generados.')
        return redirect('content:plantilla_contrato_detail', pk=pk)
    
    plantilla.delete()
    messages.success(request, 'Plantilla eliminada exitosamente.')
    return redirect('content:plantilla_contrato_list')

# ==================== CONTRATOS GENERADOS ====================

@method_decorator([login_required], name='dispatch')
class ContratoGeneradoListView(ListView):
    """Lista de contratos generados"""
    model = ContratoGenerado
    template_name = 'content/contrato_list.html'
    context_object_name = 'contratos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ContratoGenerado.objects.select_related(
            'cuña', 'cliente', 'plantilla_usada', 'generado_por'
        )
        
        # Filtrar por rol
        if es_cliente(self.request.user):
            queryset = queryset.filter(cliente=self.request.user)
        elif es_vendedor(self.request.user):
            queryset = queryset.filter(cuña__vendedor_asignado=self.request.user)
        
        # Filtros
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero_contrato__icontains=search) |
                Q(nombre_cliente__icontains=search) |
                Q(ruc_dni_cliente__icontains=search)
            )
        
        return queryset.order_by('-fecha_generacion')

@method_decorator([login_required], name='dispatch')
class ContratoGeneradoDetailView(DetailView):
    """Detalle de contrato generado"""
    model = ContratoGenerado
    template_name = 'content/contrato_detail.html'
    context_object_name = 'contrato'
    
    def get_object(self):
        obj = super().get_object()
        
        # Verificar permisos
        if es_cliente(self.request.user) and obj.cliente != self.request.user:
            raise Http404("Contrato no encontrado")
        
        if es_vendedor(self.request.user) and obj.cuña.vendedor_asignado != self.request.user:
            raise Http404("Contrato no encontrado")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_regenerar'] = self.object.puede_regenerar and puede_gestionar_contratos(self.request.user)
        context['puede_modificar_estado'] = puede_gestionar_contratos(self.request.user)
        return context

@login_required
@user_passes_test(puede_gestionar_contratos)
def generar_contrato(request, cuña_id):
    """Generar contrato desde una cuña"""
    cuña = get_object_or_404(CuñaPublicitaria, pk=cuña_id)
    
    # Verificar permisos
    if es_vendedor(request.user) and cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos para generar contrato para esta cuña")
    
    # Verificar si ya tiene contrato
    if cuña.contratos.filter(estado__in=['generado', 'enviado', 'firmado', 'activo']).exists():
        messages.warning(request, 'Esta cuña ya tiene un contrato activo.')
        return redirect('content:cuña_detail', pk=cuña_id)
    
    # Obtener plantilla predeterminada
    plantilla = PlantillaContrato.objects.filter(
        is_default=True,
        is_active=True
    ).first()
    
    if not plantilla:
        plantilla = PlantillaContrato.objects.filter(is_active=True).first()
    
    if not plantilla:
        messages.error(request, 'No hay plantillas de contrato disponibles. Contacte al administrador.')
        return redirect('content:cuña_detail', pk=cuña_id)
    
    # Crear contrato
    contrato = ContratoGenerado.objects.create(
        cuña=cuña,
        plantilla_usada=plantilla,
        cliente=cuña.cliente,
        nombre_cliente=cuña.cliente.empresa or cuña.cliente.razon_social or cuña.cliente.get_full_name(),
        ruc_dni_cliente=cuña.cliente.ruc_dni or 'N/A',
        valor_sin_iva=cuña.precio_total,
        generado_por=request.user
    )
    
    # Generar el archivo
    if contrato.generar_contrato():
        messages.success(
            request,
            f'Contrato {contrato.numero_contrato} generado exitosamente. Ya puede descargarlo.'
        )
        return redirect('content:contrato_detail', pk=contrato.pk)
    else:
        messages.error(request, 'Error al generar el contrato. Intente nuevamente.')
        contrato.delete()
        return redirect('content:cuña_detail', pk=cuña_id)

@login_required
@user_passes_test(puede_gestionar_contratos)
def regenerar_contrato(request, pk):
    """Regenerar contrato"""
    contrato = get_object_or_404(ContratoGenerado, pk=pk)
    
    # Verificar permisos
    if es_vendedor(request.user) and contrato.cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos para regenerar este contrato")
    
    if not contrato.puede_regenerar:
        messages.error(request, 'No se puede regenerar este contrato en su estado actual.')
        return redirect('content:contrato_detail', pk=pk)
    
    # Regenerar
    if contrato.generar_contrato():
        messages.success(request, f'Contrato {contrato.numero_contrato} regenerado exitosamente.')
    else:
        messages.error(request, 'Error al regenerar el contrato.')
    
    return redirect('content:contrato_detail', pk=pk)

@login_required
def descargar_contrato(request, pk):
    """Descargar archivo de contrato"""
    contrato = get_object_or_404(ContratoGenerado, pk=pk)
    
    # Verificar permisos
    if es_cliente(request.user) and contrato.cliente != request.user:
        return HttpResponseForbidden("No tiene permisos para descargar este contrato")
    
    if es_vendedor(request.user) and contrato.cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos para descargar este contrato")
    
    if not contrato.archivo_contrato:
        messages.error(request, 'El contrato no ha sido generado aún.')
        return redirect('content:contrato_detail', pk=pk)
    
    # Servir archivo
    response = FileResponse(
        contrato.archivo_contrato.open('rb'),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    response['Content-Disposition'] = f'attachment; filename="Contrato_{contrato.numero_contrato}.docx"'
    
    return response

@login_required
@user_passes_test(puede_gestionar_contratos)
@require_POST
def contrato_marcar_enviado(request, pk):
    """Marcar contrato como enviado"""
    contrato = get_object_or_404(ContratoGenerado, pk=pk)
    
    if es_vendedor(request.user) and contrato.cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos")
    
    contrato.marcar_como_enviado()
    messages.success(request, f'Contrato {contrato.numero_contrato} marcado como enviado.')
    
    return redirect('content:contrato_detail', pk=pk)

@login_required
@user_passes_test(puede_gestionar_contratos)
@require_POST
def contrato_marcar_firmado(request, pk):
    """Marcar contrato como firmado"""
    contrato = get_object_or_404(ContratoGenerado, pk=pk)
    
    if es_vendedor(request.user) and contrato.cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos")
    
    contrato.marcar_como_firmado()
    messages.success(request, f'Contrato {contrato.numero_contrato} marcado como firmado.')
    
    return redirect('content:contrato_detail', pk=pk)

@login_required
@user_passes_test(puede_gestionar_contratos)
@require_POST
def contrato_activar(request, pk):
    """Activar contrato"""
    contrato = get_object_or_404(ContratoGenerado, pk=pk)
    
    if es_vendedor(request.user) and contrato.cuña.vendedor_asignado != request.user:
        return HttpResponseForbidden("No tiene permisos")
    
    contrato.activar_contrato()
    messages.success(request, f'Contrato {contrato.numero_contrato} activado.')
    
    return redirect('content:contrato_detail', pk=pk)

# ==================== VISTAS AJAX ====================

@login_required
@require_http_methods(["GET"])
def cuña_estado_ajax(request, pk):
    """Obtener estado actual de cuña vía AJAX"""
    try:
        cuña = CuñaPublicitaria.objects.get(pk=pk)
        
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
    
    stats = {
        'total_cuñas': CuñaPublicitaria.objects.count(),
        'cuñas_activas': CuñaPublicitaria.objects.filter(estado='activa').count(),
        'cuñas_pendientes': CuñaPublicitaria.objects.filter(estado='pendiente_revision').count(),
        'cuñas_por_vencer': CuñaPublicitaria.objects.filter(
            fecha_fin__lte=timezone.now().date() + timedelta(days=7),
            estado='activa'
        ).count(),
        'total_contratos': ContratoGenerado.objects.count(),
        'contratos_activos': ContratoGenerado.objects.filter(estado='activo').count(),
    }
    
    if es_cliente(request.user):
        stats.update({
            'mis_cuñas': CuñaPublicitaria.objects.filter(cliente=request.user).count(),
            'mis_cuñas_activas': CuñaPublicitaria.objects.filter(
                cliente=request.user, estado='activa'
            ).count(),
            'mis_contratos': ContratoGenerado.objects.filter(cliente=request.user).count(),
        })
    elif es_vendedor(request.user):
        stats.update({
            'mis_ventas': CuñaPublicitaria.objects.filter(vendedor_asignado=request.user).count(),
            'ventas_mes': CuñaPublicitaria.objects.filter(
                vendedor_asignado=request.user,
                created_at__month=timezone.now().month
            ).count(),
            'contratos_mes': ContratoGenerado.objects.filter(
                generado_por=request.user,
                fecha_generacion__month=timezone.now().month
            ).count(),
        })
    
    return JsonResponse(stats)

# ==================== REPORTES ====================

@login_required
@user_passes_test(lambda u: es_administrador(u) or es_supervisor(u))
def reporte_cuñas(request):
    """Reporte de cuñas publicitarias"""
    
    stats_estado = CuñaPublicitaria.objects.values('estado').annotate(
        count=Count('id')
    ).order_by('estado')
    
    stats_categoria = CuñaPublicitaria.objects.values(
        'categoria__nombre'
    ).annotate(
        count=Count('id'),
        total_ingresos=Sum('precio_total')
    ).order_by('-count')
    
    stats_vendedor = CuñaPublicitaria.objects.values(
        'vendedor_asignado__first_name',
        'vendedor_asignado__last_name'
    ).annotate(
        count=Count('id'),
        total_ingresos=Sum('precio_total')
    ).order_by('-count')
    
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

@login_required
@user_passes_test(lambda u: es_administrador(u) or es_supervisor(u))
def reporte_contratos(request):
    """Reporte de contratos generados"""
    
    stats_estado = ContratoGenerado.objects.values('estado').annotate(
        count=Count('id'),
        total=Sum('valor_total')
    ).order_by('estado')
    
    stats_mes = ContratoGenerado.objects.filter(
        fecha_generacion__year=timezone.now().year
    ).values(
        'fecha_generacion__month'
    ).annotate(
        count=Count('id'),
        total=Sum('valor_total')
    ).order_by('fecha_generacion__month')
    
    contratos_recientes = ContratoGenerado.objects.select_related(
        'cuña', 'cliente'
    ).order_by('-fecha_generacion')[:20]
    
    context = {
        'stats_estado': stats_estado,
        'stats_mes': stats_mes,
        'contratos_recientes': contratos_recientes,
    }
    
    return render(request, 'content/reporte_contratos.html', context)

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
        
        cuña_id = self.request.GET.get('cuña')
        if cuña_id:
            queryset = queryset.filter(cuña_id=cuña_id)
        
        if es_cliente(self.request.user):
            queryset = queryset.filter(cuña__cliente=self.request.user)
        elif es_vendedor(self.request.user):
            queryset = queryset.filter(cuña__vendedor_asignado=self.request.user)
        
        return queryset.order_by('-fecha')