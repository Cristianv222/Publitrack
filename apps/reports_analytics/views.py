# apps/reports_analytics/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.contrib import messages
import json
from datetime import datetime, timedelta
from decimal import Decimal
import csv
import xlwt

from apps.content_management.models import ContratoGenerado, CuñaPublicitaria
from .models import ReporteContratos, DashboardContratos

def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_superuser or user.is_staff or getattr(user, 'rol', None) == 'admin'

@login_required
@user_passes_test(is_admin)
def dashboard_contratos(request):
    """Dashboard principal de contratos"""
    
    # Obtener estadísticas en tiempo real
    hoy = timezone.now().date()
    
    # Contratos por estado
    total_contratos = ContratoGenerado.objects.count()
    
    contratos_activos = ContratoGenerado.objects.filter(estado='activo').count()
    contratos_pendientes = ContratoGenerado.objects.filter(
        estado__in=['borrador', 'generado', 'enviado']
    ).count()
    
    # Contratos por vencer (firmados que están activos pero cerca de vencer)
    fecha_limite_vencimiento = hoy + timedelta(days=30)
    contratos_por_vencer = ContratoGenerado.objects.filter(
        estado='activo',
        cuña__fecha_fin__lte=fecha_limite_vencimiento,
        cuña__fecha_fin__gte=hoy
    ).count()
    
    contratos_vencidos = ContratoGenerado.objects.filter(
        estado='activo',
        cuña__fecha_fin__lt=hoy
    ).count()
    
    contratos_cancelados = ContratoGenerado.objects.filter(estado='cancelado').count()
    
    # Ingresos
    ingresos_totales = ContratoGenerado.objects.aggregate(
        total=Sum('valor_total')
    )['total'] or Decimal('0.00')
    
    ingresos_activos = ContratoGenerado.objects.filter(estado='activo').aggregate(
        total=Sum('valor_total')
    )['total'] or Decimal('0.00')
    
    # Contratos recientes
    contratos_recientes = ContratoGenerado.objects.select_related(
        'cliente', 'cuña', 'plantilla_usada'
    ).order_by('-fecha_generacion')[:10]
    
    # Evolución mensual de contratos (últimos 6 meses)
    meses_data = []
    for i in range(5, -1, -1):
        mes_fecha = hoy - timedelta(days=30*i)
        mes_str = mes_fecha.strftime('%Y-%m')
        mes_nombre = mes_fecha.strftime('%b %Y')
        
        contrato_mes = ContratoGenerado.objects.filter(
            fecha_generacion__year=mes_fecha.year,
            fecha_generacion__month=mes_fecha.month
        ).count()
        
        meses_data.append({
            'mes': mes_nombre,
            'total': contrato_mes
        })
    
    context = {
        'total_contratos': total_contratos,
        'contratos_activos': contratos_activos,
        'contratos_pendientes': contratos_pendientes,
        'contratos_por_vencer': contratos_por_vencer,
        'contratos_vencidos': contratos_vencidos,
        'contratos_cancelados': contratos_cancelados,
        'ingresos_totales': ingresos_totales,
        'ingresos_activos': ingresos_activos,
        'contratos_recientes': contratos_recientes,
        'meses_data': meses_data,
    }
    
    return render(request, 'reports_analytics/dashboard_contratos.html', context)

@login_required
@user_passes_test(is_admin)
def api_estadisticas_contratos(request):
    """API para obtener estadísticas de contratos (AJAX)"""
    
    hoy = timezone.now().date()
    
    # Datos para gráficos
    contratos_por_estado = ContratoGenerado.objects.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')
    
    # Ingresos por mes (últimos 6 meses)
    ingresos_mensuales = []
    for i in range(5, -1, -1):
        mes_fecha = hoy - timedelta(days=30*i)
        mes_nombre = mes_fecha.strftime('%b %Y')
        
        ingreso_mes = ContratoGenerado.objects.filter(
            fecha_generacion__year=mes_fecha.year,
            fecha_generacion__month=mes_fecha.month
        ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        
        ingresos_mensuales.append({
            'mes': mes_nombre,
            'ingresos': float(ingreso_mes)
        })
    
    return JsonResponse({
        'contratos_por_estado': list(contratos_por_estado),
        'ingresos_mensuales': ingresos_mensuales,
    })

@login_required
@user_passes_test(is_admin)
def reporte_estado_contratos(request):
    """Genera reporte de contratos por estado"""
    
    # Parámetros del reporte
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Filtrar contratos
    contratos = ContratoGenerado.objects.select_related(
        'cliente', 'cuña', 'plantilla_usada'
    ).all()
    
    if fecha_inicio:
        contratos = contratos.filter(fecha_generacion__date__gte=fecha_inicio)
    if fecha_fin:
        contratos = contratos.filter(fecha_generacion__date__lte=fecha_fin)
    
    # Agrupar por estado
    contratos_por_estado = contratos.values('estado').annotate(
        total=Count('id'),
        valor_total=Sum('valor_total')
    ).order_by('estado')
    
    # Detalle por estado
    detalle_estados = {}
    for estado in ['borrador', 'generado', 'enviado', 'firmado', 'activo', 'vencido', 'cancelado']:
        detalle_estados[estado] = contratos.filter(estado=estado)
    
    formato = request.GET.get('formato', 'html')
    
    if formato == 'csv':
        return generar_reporte_csv_estado(contratos_por_estado, detalle_estados)
    elif formato == 'excel':
        return generar_reporte_excel_estado(contratos_por_estado, detalle_estados)
    
    context = {
        'contratos_por_estado': contratos_por_estado,
        'detalle_estados': detalle_estados,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_contratos': contratos.count(),
        'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    
    return render(request, 'reports_analytics/reportes/estado_contratos.html', context)

@login_required
@user_passes_test(is_admin)
def reporte_vencimiento_contratos(request):
    """Genera reporte de contratos por vencimiento"""
    
    hoy = timezone.now().date()
    dias_aviso = int(request.GET.get('dias_aviso', 30))
    
    fecha_limite = hoy + timedelta(days=dias_aviso)
    
    # Contratos por vencer
    contratos_por_vencer = ContratoGenerado.objects.filter(
        estado='activo',
        cuña__fecha_fin__lte=fecha_limite,
        cuña__fecha_fin__gte=hoy
    ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
    
    # Contratos vencidos
    contratos_vencidos = ContratoGenerado.objects.filter(
        estado='activo',
        cuña__fecha_fin__lt=hoy
    ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
    
    # Contratos con buena vigencia
    contratos_vigentes = ContratoGenerado.objects.filter(
        estado='activo',
        cuña__fecha_fin__gt=fecha_limite
    ).select_related('cliente', 'cuña').order_by('cuña__fecha_fin')
    
    formato = request.GET.get('formato', 'html')
    
    if formato == 'csv':
        return generar_reporte_csv_vencimiento(contratos_por_vencer, contratos_vencidos, contratos_vigentes)
    elif formato == 'excel':
        return generar_reporte_excel_vencimiento(contratos_por_vencer, contratos_vencidos, contratos_vigentes)
    
    context = {
        'contratos_por_vencer': contratos_por_vencer,
        'contratos_vencidos': contratos_vencidos,
        'contratos_vigentes': contratos_vigentes,
        'dias_aviso': dias_aviso,
        'fecha_limite': fecha_limite,
        'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    
    return render(request, 'reports_analytics/reportes/vencimiento_contratos.html', context)

@login_required
@user_passes_test(is_admin)
def reporte_ingresos_contratos(request):
    """Genera reporte de ingresos por contratos"""
    
    # Parámetros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    agrupar_por = request.GET.get('agrupar_por', 'mes')
    
    # Base query
    contratos = ContratoGenerado.objects.select_related('cliente', 'cuña').all()
    
    if fecha_inicio:
        contratos = contratos.filter(fecha_generacion__date__gte=fecha_inicio)
    if fecha_fin:
        contratos = contratos.filter(fecha_generacion__date__lte=fecha_fin)
    
    # Agrupar datos
    if agrupar_por == 'mes':
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
    
    formato = request.GET.get('formato', 'html')
    
    if formato == 'csv':
        return generar_reporte_csv_ingresos(ingresos_data, agrupar_por)
    elif formato == 'excel':
        return generar_reporte_excel_ingresos(ingresos_data, agrupar_por)
    
    context = {
        'ingresos_data': ingresos_data,
        'agrupar_por': agrupar_por,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_ingresos': contratos.aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00'),
        'fecha_reporte': timezone.now().strftime('%d/%m/%Y %H:%M'),
    }
    
    return render(request, 'reports_analytics/reportes/ingresos_contratos.html', context)

# Funciones auxiliares para generar reportes en CSV
def generar_reporte_csv_estado(contratos_por_estado, detalle_estados):
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

def generar_reporte_csv_vencimiento(por_vencer, vencidos, vigentes):
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

# Funciones para Excel (similar a CSV pero con xlwt)

def generar_reporte_excel_estado(contratos_por_estado, detalle_estados):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="reporte_estado_contratos.xls"'
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Contratos por Estado')
    
    # Estilos
    style_heading = xlwt.easyxf('font: bold on')
    style_bold = xlwt.easyxf('font: bold on')
    
    # Encabezados
    ws.write(0, 0, 'Reporte de Contratos por Estado', style_heading)
    ws.write(1, 0, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    row = 3
    ws.write(row, 0, 'Estado', style_bold)
    ws.write(row, 1, 'Cantidad', style_bold)
    ws.write(row, 2, 'Valor Total', style_bold)
    
    for item in contratos_por_estado:
        row += 1
        ws.write(row, 0, dict(ContratoGenerado.ESTADO_CHOICES).get(item['estado'], item['estado']))
        ws.write(row, 1, item['total'])
        ws.write(row, 2, float(item['valor_total']))
    
    wb.save(response)
    return response