from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Brand
from .brand_serializers import (
    BrandListSerializer,
    BrandDetailSerializer,
    BrandCreateUpdateSerializer
)

class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return BrandListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BrandCreateUpdateSerializer
        return BrandDetailSerializer
