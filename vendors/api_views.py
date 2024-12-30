from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Vendor
from .serializers import (
    VendorRegistrationSerializer,
    VendorProfileSerializer,
    VendorShippingSerializer,
    VendorPaymentSerializer,
    VendorVerificationSerializer,
    VendorSEOSerializer,
    VendorListSerializer
)

class IsVendorOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a vendor to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class VendorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'list':
            return Vendor.objects.filter(account_status='active')
        return Vendor.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return VendorRegistrationSerializer
        elif self.action == 'list':
            return VendorListSerializer
        elif self.action == 'shipping':
            return VendorShippingSerializer
        elif self.action == 'payment':
            return VendorPaymentSerializer
        elif self.action == 'verification':
            return VendorVerificationSerializer
        elif self.action == 'seo':
            return VendorSEOSerializer
        return VendorProfileSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy', 'shipping', 
                           'payment', 'verification', 'seo']:
            return [IsAuthenticated(), IsVendorOwner()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get', 'put', 'patch'])
    def shipping(self, request, pk=None):
        vendor = self.get_object()
        if request.method == 'GET':
            serializer = self.get_serializer(vendor)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(vendor, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'put', 'patch'])
    def payment(self, request, pk=None):
        vendor = self.get_object()
        if request.method == 'GET':
            serializer = self.get_serializer(vendor)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(vendor, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'put', 'patch'])
    def verification(self, request, pk=None):
        vendor = self.get_object()
        if request.method == 'GET':
            serializer = self.get_serializer(vendor)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(vendor, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'put', 'patch'])
    def seo(self, request, pk=None):
        vendor = self.get_object()
        if request.method == 'GET':
            serializer = self.get_serializer(vendor)
            return Response(serializer.data)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(vendor, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def use_business_address(self, request, pk=None):
        vendor = self.get_object()
        address_type = request.data.get('type', 'shipping')
        
        if address_type == 'shipping':
            vendor.use_business_address_for_shipping()
        elif address_type == 'return':
            vendor.use_business_address_for_returns()
        else:
            return Response(
                {'error': 'Invalid address type. Use "shipping" or "return".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vendor.save()
        return Response({'status': 'Address updated successfully'})

    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        vendor = self.get_object()
        from products.models import Product
        from orders.models import Order
        
        # Get basic stats
        total_products = Product.objects.filter(vendor=vendor).count()
        active_products = Product.objects.filter(vendor=vendor, status='active').count()
        recent_orders = Order.objects.filter(items__product__vendor=vendor).distinct().order_by('-created_at')[:5]
        
        data = {
            'total_products': total_products,
            'active_products': active_products,
            'verification_status': vendor.verification_status,
            'account_status': vendor.account_status,
            'recent_orders': [
                {
                    'order_number': order.order_number,
                    'date': order.created_at,
                    'status': order.status,
                    'total': str(order.total_amount)
                }
                for order in recent_orders
            ]
        }
        return Response(data)
