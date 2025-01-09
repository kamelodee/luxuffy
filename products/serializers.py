from rest_framework import serializers
from django.conf import settings

from .models import Product, Brand, ProductImage, ProductVariant, ProductSpecification, Tag
from categories.models import Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'is_active']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'description', 'logo', 'website', 'created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'product_id', 'image', 'image_url', 'alt_text', 'is_primary', 'created_at', 'updated_at']
        read_only_fields = ['created_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return f"{settings.MEDIA_URL}{obj.image}"
        return None

class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'product_id', 'specification_name', 'specification_value', 'created_at']

class ProductVariantSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='variant_image', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'product_id', 'name', 'sku', 'price', 'stock_quantity', 'discount_price',
            'weight', 'dimensions', 'size', 'color', 'material', 'style',
            'image', 'image_url', 'is_active', 'created_at', 'updated_at'
        ]
    
    def get_image_url(self, obj):
        if obj.variant_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.variant_image.url)
            return f"{settings.MEDIA_URL}{obj.variant_image}"
        return None

class ProductListSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'category', 'product_type', 'status',
            'price', 'discount_price', 'is_active', 'is_featured',
            'primary_image', 'primary_image_url', 'images', 'variants', 'created_at'
        ]

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None

    def get_primary_image_url(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    primary_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'category', 'brand', 'product_type', 'status',
            'name', 'description', 'slug', 'tags', 'primary_image', 'primary_image_url', 'images',
            'price', 'compare_at_price', 'discount_price', 'sku', 'barcode',
            'video', 'stock_quantity', 'is_active', 'is_featured',
            'available_from', 'available_to', 'weight', 'dimensions',
            'digital_file', 'download_limit', 'download_expiry',
            'meta_title', 'meta_description', 'meta_keywords',
            'variants', 'specifications', 'created_at', 'updated_at'
        ]

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None

    def get_primary_image_url(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image_url
        return None

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'vendor', 'category', 'brand', 'product_type', 'status',
            'name', 'description', 'tags', 'image', 'price',
            'compare_at_price', 'discount_price', 'sku', 'barcode',
            'video', 'stock_quantity', 'is_active', 'is_featured',
            'available_from', 'available_to', 'weight', 'dimensions',
            'digital_file', 'download_limit', 'download_expiry',
            'meta_title', 'meta_description', 'meta_keywords'
        ]

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        product = Product.objects.create(**validated_data)
        product.tags.set(tags_data)
        return product

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if tags_data is not None:
            instance.tags.set(tags_data)
        
        return instance
