from rest_framework import serializers
from .models import Tag
from .serializers import ProductListSerializer

class TagListSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'product_count']

    def get_product_count(self, obj):
        return obj.products.count()

class TagDetailSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'description', 'created_at', 'product_count', 'products']

    def get_product_count(self, obj):
        return obj.products.count()

class TagCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name', 'description']

    def validate_name(self, value):
        """
        Check that the tag name is unique (case-insensitive)
        """
        instance = self.instance
        if Tag.objects.filter(name__iexact=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("A tag with this name already exists.")
        return value
