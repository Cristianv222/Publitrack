# apps/inventory/models.py - VERSIÓN SIMPLIFICADA
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date

# ========== MODELOS SIMPLIFICADOS ==========
class Category(models.Model):
    """Categoría principal simplificada"""
    name = models.CharField(_('Nombre'), max_length=100, unique=True)
    color = models.CharField(
        _('Color'), 
        max_length=20, 
        default='#3498db',
        help_text=_('Color en hexadecimal')
    )
    order = models.IntegerField(_('Orden'), default=0)
    is_active = models.BooleanField(_('Activa'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Categoría')
        verbose_name_plural = _('Categorías')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Status(models.Model):
    """Estados personalizables simplificados"""
    name = models.CharField(_('Nombre'), max_length=50, unique=True)
    color = models.CharField(
        _('Color'), 
        max_length=20, 
        default='#95a5a6',
        help_text=_('Color para visualización')
    )
    is_default = models.BooleanField(
        _('Estado por defecto'), 
        default=False
    )
    can_use = models.BooleanField(
        _('Puede usarse'), 
        default=True,
        help_text=_('Los ítems con este estado pueden ser utilizados')
    )
    requires_attention = models.BooleanField(
        _('Requiere atención'), 
        default=False,
        help_text=_('Alerta para mantenimiento/revisión')
    )
    
    class Meta:
        verbose_name = _('Estado')
        verbose_name_plural = _('Estados')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.is_default:
            # Solo puede haber un estado por defecto
            Status.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ========== MODELO PRINCIPAL DE INVENTARIO SIMPLIFICADO ==========
class InventoryItem(models.Model):
    """Ítem principal del inventario simplificado"""
    # Información básica
    code = models.CharField(
        _('Código Único'), 
        max_length=50, 
        unique=True,
        editable=False,
        help_text=_('Código generado automáticamente')
    )
    name = models.CharField(
        _('Nombre del Producto'), 
        max_length=200
    )
    description = models.TextField(
        _('Descripción detallada'), 
        blank=True
    )
    
    # Categorización simplificada
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT,
        verbose_name=_('Categoría')
    )
    
    # Estado simplificado
    status = models.ForeignKey(
        Status, 
        on_delete=models.PROTECT,
        verbose_name=_('Estado actual')
    )
    
    # Ubicación simplificada (campo de texto libre)
    location = models.CharField(
        _('Ubicación'), 
        max_length=200,
        blank=True,
        help_text=_('Ej: Estudio 1, Bodega Central, Oficina')
    )
    
    # Cantidad y medición
    quantity = models.IntegerField(_('Cantidad'), default=1)
    min_quantity = models.IntegerField(
        _('Cantidad mínima'), 
        default=0,
        help_text=_('Alerta cuando el stock baja de este nivel')
    )
    unit_of_measure = models.CharField(
        _('Unidad de medida'), 
        max_length=20,
        default='Unidad',
        help_text=_('Piezas, metros, litros, etc.')
    )
    
    # Información de adquisición (opcional)
    serial_number = models.CharField(
        _('Número de serie'), 
        max_length=100, 
        blank=True,
        unique=True,
        null=True
    )
    brand = models.CharField(_('Marca'), max_length=100, blank=True)
    model = models.CharField(_('Modelo'), max_length=100, blank=True)
    supplier = models.CharField(_('Proveedor'), max_length=200, blank=True)
    
    # Metadatos
    is_active = models.BooleanField(_('Activo'), default=True)
    notes = models.TextField(_('Notas adicionales'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_inventory_items',
        verbose_name=_('Creado por')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_inventory_items',
        verbose_name=_('Actualizado por')
    )
    
    class Meta:
        verbose_name = _('Ítem de Inventario')
        verbose_name_plural = _('Ítems de Inventario')
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]
    
    def clean(self):
        """Validaciones personalizadas"""
        if self.quantity < 0:
            raise ValidationError(_('La cantidad no puede ser negativa'))
        
        if self.min_quantity > self.quantity:
            raise ValidationError(
                _('La cantidad mínima no puede ser mayor que la cantidad actual')
            )
    
    def save(self, *args, **kwargs):
        # Generar código automático si es nuevo
        if not self.code:
            prefix = 'INV'
            last_item = InventoryItem.objects.filter(
                code__startswith=prefix
            ).order_by('code').last()
            
            if last_item:
                try:
                    last_num = int(last_item.code.replace(prefix, ''))
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            
            self.code = f"{prefix}{new_num:04d}"
        
        # Asegurar que haya un estado por defecto
        if not self.status_id:
            default_status = Status.objects.filter(is_default=True).first()
            if default_status:
                self.status = default_status
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def needs_restock(self):
        """Verifica si necesita reabastecimiento"""
        return self.quantity <= self.min_quantity