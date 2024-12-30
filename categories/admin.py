from django.contrib import admin
from .models import Category

class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for Category model"""
    
    list_display = ('name', 'parent', 'is_active', 'display_order', 'created_at','image', 'updated_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    
    # Exclude non-editable fields from the admin form
    exclude = ('created_at',)

    # Automatically populate slug field
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category, CategoryAdmin)