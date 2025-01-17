from rest_framework import serializers
from .models import Category

class CategoryListSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent_name', 'is_active', 'display_order', 'product_count', 'image']

    def get_product_count(self, obj):
        return obj.products.count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class CategoryDetailSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    parent_details = serializers.SerializerMethodField()
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_details',
            'image', 'is_active', 'display_order', 'children', 'full_path',
            'meta_title', 'meta_description', 'meta_keywords', 'seo_url',
            'product_count', 'created_at', 'updated_at'
        ]

    def get_children(self, obj):
        children = obj.children.all()
        return CategoryListSerializer(children, many=True).data

    def get_parent_details(self, obj):
        if obj.parent:
            return {
                'id': obj.parent.id,
                'name': obj.parent.name,
                'slug': obj.parent.slug
            }
        return None

    def get_product_count(self, obj):
        return obj.products.count()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request:
            representation['image'] = request.build_absolute_uri(instance.image.url)
        return representation

class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'name', 'description', 'parent', 'image', 'is_active',
            'display_order', 'meta_title', 'meta_description',
            'meta_keywords', 'seo_url'
        ]

    def validate_parent(self, value):
        if value and value == self.instance:
            raise serializers.ValidationError("A category cannot be its own parent.")
        return value

    def validate(self, data):
        # Check for circular dependencies
        parent = data.get('parent')
        instance = self.instance
        
        if parent and instance:
            current_parent = parent
            while current_parent:
                if current_parent == instance:
                    raise serializers.ValidationError({
                        'parent': 'Circular dependency detected in category hierarchy.'
                    })
                current_parent = current_parent.parent
                
        return data
