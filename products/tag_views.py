from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Tag
from .tag_serializers import (
    TagListSerializer,
    TagDetailSerializer,
    TagCreateUpdateSerializer
)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return TagListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TagCreateUpdateSerializer
        return TagDetailSerializer
