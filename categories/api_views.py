from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Category
from .serializers import (
    CategoryListSerializer,
    CategoryDetailSerializer,
    CategoryCreateUpdateSerializer
)
from django.db.models import Q

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def list_categories(request):
    if request.method == 'GET':
        queryset = Category.objects.all()
        filterset_fields = ['is_active', 'parent']
        search_fields = ['name', 'description', 'meta_keywords']
        ordering_fields = ['name', 'display_order', 'created_at']
        
        # Filter root categories (no parent)
        root_only = request.query_params.get('root_only', None)
        if root_only and root_only.lower() == 'true':
            queryset = queryset.filter(parent=None)
            
        # Filter by parent slug
        parent_slug = request.query_params.get('parent_slug', None)
        if parent_slug:
            queryset = queryset.filter(parent__slug=parent_slug)
        
        # Search functionality
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(meta_keywords__icontains=search_query)
            )
        
        serializer = CategoryListSerializer(queryset, many=True, context={'request': request})
        return Response({'status': 'success', 'message': 'Categories retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = CategoryCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Category created successfully', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    if request.method == 'GET':
        serializer = CategoryDetailSerializer(category, context={'request': request})
        return Response({'status': 'success', 'message': 'Category retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    elif request.method == 'PUT':
        serializer = CategoryCreateUpdateSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Category updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        category.delete()
        return Response({'status': 'success', 'message': 'Category deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_subcategories(request, slug):
    category = get_object_or_404(Category, slug=slug)
    subcategories = category.children.all()
    serializer = CategoryListSerializer(subcategories, many=True, context={'request': request})
    return Response({'status': 'success', 'message': 'Subcategories retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()
    from products.serializers import ProductListSerializer
    serializer = ProductListSerializer(products, many=True, context={'request': request})
    return Response({'status': 'success', 'message': 'Products retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_hierarchy(request, slug):
    category = get_object_or_404(Category, slug=slug)
    hierarchy = []
    current = category
    while current.parent:
        hierarchy.insert(0, {
            'id': current.parent.id,
            'name': current.parent.name,
            'slug': current.parent.slug
        })
        current = current.parent
    hierarchy.append({
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'is_current': True
    })
    return Response({'status': 'success', 'message': 'Hierarchy retrieved successfully', 'data': hierarchy}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_category_tree(request):
    root_categories = Category.objects.filter(parent=None)
    serializer = CategoryDetailSerializer(root_categories, many=True, context={'request': request})
    return Response({'status': 'success', 'message': 'Category tree retrieved successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
