from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Vendor
from .serializers import VendorSerializer

class VendorViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for managing Vendor data.
    """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only allow vendors related to the logged-in user
        if self.request.user.is_superuser:
            return Vendor.objects.all()
        return Vendor.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Retrieve the current vendor profile."""
        vendor = self.get_object()
        if vendor.user != request.user:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(vendor)
        return Response(serializer.data)
