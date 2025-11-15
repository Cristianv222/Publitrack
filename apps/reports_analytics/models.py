# apps/reports_analytics/models.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.content_management.models import ContratoGenerado, CuñaPublicitaria
from apps.authentication.models import CustomUser

User = get_user_model()

class ReporteContratos(models.Model):
    """Modelo para almacenar reportes de contratos generados"""
    
    TIPO_REPORTE_CHOICES = [
        ('estado_contratos', 'Reporte por Estado de Contratos'),
        ('contratos_vencimiento', 'Reporte por Vencimiento'),
        ('ingresos_contratos', 'Reporte de Ingresos por Contratos'),
        ('contratos_cliente', 'Reporte por Cliente'),
    ]
    
    nombre = models.CharField('Nombre del Reporte', max_length=200)
    tipo_reporte = models.CharField('Tipo de Reporte', max_length=50, choices=TIPO_REPORTE_CHOICES)
    parametros = models.JSONField('Parámetros del Reporte', default=dict, blank=True)
    archivo_generado = models.FileField('Archivo Generado', upload_to='reportes/contratos/', null=True, blank=True)
    fecha_generacion = models.DateTimeField('Fecha de Generación', auto_now_add=True)
    generado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Reporte de Contratos'
        verbose_name_plural = 'Reportes de Contratos'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_reporte_display()}"

class DashboardContratos(models.Model):
    """Modelo para almacenar datos del dashboard de contratos"""
    
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    total_contratos = models.IntegerField('Total Contratos', default=0)
    contratos_activos = models.IntegerField('Contratos Activos', default=0)
    contratos_pendientes = models.IntegerField('Contratos Pendientes', default=0)
    contratos_por_vencer = models.IntegerField('Contratos por Vencer', default=0)
    contratos_vencidos = models.IntegerField('Contratos Vencidos', default=0)
    contratos_cancelados = models.IntegerField('Contratos Cancelados', default=0)
    ingresos_totales = models.DecimalField('Ingresos Totales', max_digits=15, decimal_places=2, default=0)
    ingresos_activos = models.DecimalField('Ingresos Activos', max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Dashboard Contratos'
        verbose_name_plural = 'Dashboards Contratos'
    
    def __str__(self):
        return f"Dashboard Contratos - {self.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}"

class ReporteVendedores(models.Model):
    """Modelo para almacenar reportes de vendedores"""
    
    nombre = models.CharField('Nombre del Reporte', max_length=200)
    fecha_inicio = models.DateField('Fecha Inicio')
    fecha_fin = models.DateField('Fecha Fin')
    parametros = models.JSONField('Parámetros del Reporte', default=dict, blank=True)
    archivo_generado = models.FileField('Archivo Generado', upload_to='reportes/vendedores/', null=True, blank=True)
    fecha_generacion = models.DateTimeField('Fecha de Generación', auto_now_add=True)
    generado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Reporte de Vendedores'
        verbose_name_plural = 'Reportes de Vendedores'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.fecha_generacion.strftime('%d/%m/%Y')}"
# Agrega estos modelos al final del archivo

class ReportePartesMortuorios(models.Model):
    """Modelo para almacenar reportes de partes mortuorios generados"""
    
    TIPO_REPORTE_CHOICES = [
        ('estado_partes', 'Reporte por Estado de Partes'),
        ('urgencia_partes', 'Reporte por Urgencia'),
        ('ingresos_partes', 'Reporte de Ingresos por Partes'),
        ('partes_cliente', 'Reporte por Cliente'),
    ]
    
    nombre = models.CharField('Nombre del Reporte', max_length=200)
    tipo_reporte = models.CharField('Tipo de Reporte', max_length=50, choices=TIPO_REPORTE_CHOICES)
    parametros = models.JSONField('Parámetros del Reporte', default=dict, blank=True)
    archivo_generado = models.FileField('Archivo Generado', upload_to='reportes/partes_mortuorios/', null=True, blank=True)
    fecha_generacion = models.DateTimeField('Fecha de Generación', auto_now_add=True)
    generado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Reporte de Partes Mortuorios'
        verbose_name_plural = 'Reportes de Partes Mortuorios'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_reporte_display()}"

class DashboardPartesMortuorios(models.Model):
    """Modelo para almacenar datos del dashboard de partes mortuorios"""
    
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    total_partes = models.IntegerField('Total Partes', default=0)
    partes_programados = models.IntegerField('Partes Programados', default=0)
    partes_transmitidos = models.IntegerField('Partes Transmitidos', default=0)
    partes_urgentes = models.IntegerField('Partes Urgentes', default=0)
    partes_pendientes = models.IntegerField('Partes Pendientes', default=0)
    partes_cancelados = models.IntegerField('Partes Cancelados', default=0)
    ingresos_totales = models.DecimalField('Ingresos Totales', max_digits=15, decimal_places=2, default=0)
    ingresos_mensuales = models.DecimalField('Ingresos Mensuales', max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Dashboard Partes Mortuorios'
        verbose_name_plural = 'Dashboards Partes Mortuorios'
    
    def __str__(self):
        return f"Dashboard Partes Mortuorios - {self.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}"