from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category
from .serializers import (
    CategoryListSerializer,
    CategoryDetailSerializer,
    CategoryCreateUpdateSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description', 'meta_keywords']
    ordering_fields = ['name', 'display_order', 'created_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return CategoryDetailSerializer

    def get_queryset(self):
        queryset = Category.objects.all()
        
        # Filter root categories (no parent)
        root_only = self.request.query_params.get('root_only', None)
        if root_only and root_only.lower() == 'true':
            queryset = queryset.filter(parent=None)
            
        # Filter by parent slug
        parent_slug = self.request.query_params.get('parent_slug', None)
        if parent_slug:
            queryset = queryset.filter(parent__slug=parent_slug)
            
        return queryset

    @action(detail=True)
    def subcategories(self, request, slug=None):
        """Get all subcategories of a category"""
        category = self.get_object()
        subcategories = category.children.all()
        serializer = CategoryListSerializer(subcategories, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def products(self, request, slug=None):
        """Get all products in a category"""
        category = self.get_object()
        products = category.products.all()
        from products.serializers import ProductListSerializer
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def hierarchy(self, request, slug=None):
        """Get the complete hierarchy of a category"""
        category = self.get_object()
        hierarchy = []
        current = category
        
        # Get ancestors
        while current.parent:
            hierarchy.insert(0, {
                'id': current.parent.id,
                'name': current.parent.name,
                'slug': current.parent.slug
            })
            current = current.parent
            
        # Add current category
        hierarchy.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'is_current': True
        })
        
        return Response(hierarchy)

    @action(detail=False)
    def tree(self, request):
        """Get the complete category tree"""
        root_categories = Category.objects.filter(parent=None)
        serializer = CategoryDetailSerializer(root_categories, many=True)
        return Response(serializer.data)
