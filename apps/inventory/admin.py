# apps/inventory/admin.py - VERSIÓN SIMPLIFICADA
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from .models import Category, Status, InventoryItem

User = get_user_model()

# ========== ADMIN CLASSES ==========
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['order', 'is_active']
    
    def color_display(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border-radius: 3px;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_default', 'can_use', 'requires_attention']
    list_filter = ['is_default', 'can_use', 'requires_attention']
    search_fields = ['name']
    list_editable = ['is_default', 'can_use', 'requires_attention']
    
    def color_display(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border-radius: 3px;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'status', 'quantity', 'location', 'is_active']
    list_filter = ['category', 'status', 'is_active']
    search_fields = ['code', 'name', 'description', 'serial_number', 'location']
    list_editable = ['quantity', 'is_active']
    readonly_fields = ['code', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('code', 'name', 'description', 'category', 'status', 'location')
        }),
        ('Cantidad', {
            'fields': ('quantity', 'min_quantity', 'unit_of_measure')
        }),
        ('Información Técnica', {
            'fields': ('serial_number', 'brand', 'model', 'supplier'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('is_active', 'notes', 'created_by', 'created_at', 'updated_by', 'updated_at')
        }),
    )