from django_filters import rest_framework as filters
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Product, Brand, Tag

class ProductFilter(filters.FilterSet):
    # Price range filters
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')
    discount_available = filters.BooleanFilter(method='filter_discount')
    discount_percentage = filters.NumberFilter(method='filter_discount_percentage')
    
    # Stock filters
    in_stock = filters.BooleanFilter(method='filter_in_stock')
    min_stock = filters.NumberFilter(field_name="stock_quantity", lookup_expr='gte')
    max_stock = filters.NumberFilter(field_name="stock_quantity", lookup_expr='lte')
    
    # Date filters
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name="updated_at", lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name="updated_at", lookup_expr='lte')
    available_now = filters.BooleanFilter(method='filter_available_now')
    
    # Text search filters
    search = filters.CharFilter(method='filter_search')
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    sku = filters.CharFilter(lookup_expr='iexact')
    barcode = filters.CharFilter(lookup_expr='iexact')
    
    # Category filters
    category = filters.NumberFilter(field_name='category__id')
    category_slug = filters.CharFilter(field_name='category__slug')
    root_category = filters.NumberFilter(field_name='category__parent__id', lookup_expr='isnull')
    
    # Brand filters
    brand = filters.NumberFilter(field_name='brand__id')
    brand_slug = filters.CharFilter(field_name='brand__slug')
    brand_name = filters.CharFilter(field_name='brand__name', lookup_expr='icontains')
    
    # Tag filters
    tag = filters.CharFilter(field_name='tags__name')
    tags = filters.CharFilter(method='filter_multiple_tags')
    
    # Vendor filters
    vendor = filters.NumberFilter(field_name='vendor__id')
    vendor_slug = filters.CharFilter(field_name='vendor__slug')
    vendor_name = filters.CharFilter(field_name='vendor__business_name', lookup_expr='icontains')
    
    # Status and type filters
    status = filters.ChoiceFilter(choices=Product.PRODUCT_STATUS)
    product_type = filters.ChoiceFilter(choices=Product.PRODUCT_TYPE_CHOICES)
    
    # Feature filters
    is_featured = filters.BooleanFilter()
    is_active = filters.BooleanFilter()
    
    # Physical product filters
    min_weight = filters.NumberFilter(field_name="weight", lookup_expr='gte')
    max_weight = filters.NumberFilter(field_name="weight", lookup_expr='lte')
    has_dimensions = filters.BooleanFilter(field_name="dimensions", lookup_expr='isnull', exclude=True)
    
    # Digital product filters
    is_digital = filters.BooleanFilter(method='filter_digital')
    has_download_limit = filters.BooleanFilter(field_name="download_limit", lookup_expr='isnull', exclude=True)
    
    # Variant filters
    has_variants = filters.BooleanFilter(method='filter_has_variants')
    variant_count = filters.NumberFilter(method='filter_variant_count')
    
    # Sorting
    sort_by = filters.CharFilter(method='filter_sort_by')

    class Meta:
        model = Product
        fields = [
            'min_price', 'max_price', 'discount_available', 'discount_percentage',
            'in_stock', 'min_stock', 'max_stock', 'created_after', 'created_before',
            'updated_after', 'updated_before', 'available_now', 'search', 'name',
            'description', 'sku', 'barcode', 'category', 'category_slug',
            'root_category', 'brand', 'brand_slug', 'brand_name', 'tag', 'tags',
            'vendor', 'vendor_slug', 'vendor_name', 'status', 'product_type',
            'is_featured', 'is_active', 'min_weight', 'max_weight', 'has_dimensions',
            'is_digital', 'has_download_limit', 'has_variants', 'variant_count',
            'sort_by'
        ]

    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields"""
        if not value:
            return queryset
            
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(sku__icontains=value) |
            Q(barcode__icontains=value) |
            Q(meta_keywords__icontains=value) |
            Q(brand__name__icontains=value) |
            Q(category__name__icontains=value) |
            Q(tags__name__icontains=value) |
            Q(specifications__specification_value__icontains=value)
        ).distinct()

    def filter_discount(self, queryset, name, value):
        """Filter products with active discounts"""
        if value:
            return queryset.filter(discount_price__isnull=False, discount_price__lt=models.F('price'))
        return queryset.filter(Q(discount_price__isnull=True) | Q(discount_price__gte=models.F('price')))

    def filter_discount_percentage(self, queryset, name, value):
        """Filter products by minimum discount percentage"""
        if value:
            return queryset.annotate(
                discount_pct=100 * (1 - models.F('discount_price') / models.F('price'))
            ).filter(discount_pct__gte=value)
        return queryset

    def filter_in_stock(self, queryset, name, value):
        """Filter products by stock availability"""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)

    def filter_available_now(self, queryset, name, value):
        """Filter products available for purchase right now"""
        now = timezone.now()
        if value:
            return queryset.filter(
                Q(available_from__lte=now) | Q(available_from__isnull=True),
                Q(available_to__gte=now) | Q(available_to__isnull=True),
                is_active=True,
                stock_quantity__gt=0
            )
        return queryset

    def filter_multiple_tags(self, queryset, name, value):
        """Filter products that have all specified tags"""
        if not value:
            return queryset
            
        tags = [tag.strip() for tag in value.split(',')]
        for tag in tags:
            queryset = queryset.filter(tags__name__iexact=tag)
        return queryset.distinct()

    def filter_digital(self, queryset, name, value):
        """Filter digital products"""
        if value:
            return queryset.filter(product_type='digital')
        return queryset.exclude(product_type='digital')

    def filter_has_variants(self, queryset, name, value):
        """Filter products with/without variants"""
        if value:
            return queryset.annotate(variant_count=Count('variants')).filter(variant_count__gt=0)
        return queryset.annotate(variant_count=Count('variants')).filter(variant_count=0)

    def filter_variant_count(self, queryset, name, value):
        """Filter products by number of variants"""
        return queryset.annotate(variant_count=Count('variants')).filter(variant_count=value)

    def filter_sort_by(self, queryset, name, value):
        """Custom sorting options"""
        valid_sorts = {
            'price_low': 'price',
            'price_high': '-price',
            'name_asc': 'name',
            'name_desc': '-name',
            'newest': '-created_at',
            'oldest': 'created_at',
            'most_variants': '-variant_count',
            'updated': '-updated_at',
            'stock_low': 'stock_quantity',
            'stock_high': '-stock_quantity'
        }
        
        if value not in valid_sorts:
            return queryset
            
        if value in ['most_variants']:
            queryset = queryset.annotate(variant_count=Count('variants'))
            
        return queryset.order_by(valid_sorts[value])
