from django.contrib import admin
from .models import Brand, Tag, Product, ProductVariant, ProductImage, ProductSpecification



@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)

# Registering the Tag model to the Django admin
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)

# Registering the Product model to the Django admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'category', 'brand', 'price', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'description', 'vendor__business_name', 'category__name')
    list_filter = ('is_active', 'is_featured', 'created_at', 'category')
    ordering = ('-created_at',)
    filter_horizontal = ('tags',)  # Allows for selecting multiple tags in a list view

# Registering the ProductImage model to the Django admin
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')
    search_fields = ('product__name',)
    list_filter = ('product',)
    ordering = ('product',)

# Registering the ProductVariant model to the Django admin
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'color', 'price', 'stock_quantity')
    search_fields = ('product__name', 'size', 'color')
    list_filter = ('product', 'size', 'color', 'stock_quantity')
    ordering = ('product', 'size', 'color')

# Registering the ProductSpecification model to the Django admin
@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'specification_name', 'specification_value')
    search_fields = ('product__name', 'specification_name')
    list_filter = ('product',)
    ordering = ('product', 'specification_name')


