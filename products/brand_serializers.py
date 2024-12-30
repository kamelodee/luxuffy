from rest_framework import serializers
from .models import Brand
from .serializers import ProductListSerializer

class BrandListSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug', 'logo', 'product_count']

    def get_product_count(self, obj):
        return obj.products.count()

class BrandDetailSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'description', 'logo',
            'website', 'created_at', 'updated_at',
            'product_count', 'products'
        ]

    def get_product_count(self, obj):
        return obj.products.count()

class BrandCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'logo', 'website']

    def validate_name(self, value):
        """
        Check that the brand name is unique (case-insensitive)
        """
        instance = self.instance
        if Brand.objects.filter(name__iexact=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("A brand with this name already exists.")
        return value
