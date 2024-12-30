from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 'price',
            'total_price', 'discount', 'tax', 'created_at', 'updated_at'
        ]
        read_only_fields = ['price', 'total_price', 'discount', 'tax']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    shipping_method_display = serializers.CharField(source='get_shipping_method_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'items', 'total_amount', 'subtotal_amount',
            'tax_amount', 'discount_amount', 'shipping_address',
            'billing_address', 'shipping_method', 'shipping_method_display',
            'shipping_cost', 'estimated_delivery_date', 'shipping_latitude',
            'shipping_longitude', 'billing_latitude', 'billing_longitude',
            'status', 'status_display', 'tracking_number', 'tracking_url',
            'payment_method', 'payment_method_display', 'payment_status',
            'payment_status_display', 'payment_reference', 'created_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'user', 'total_amount', 'subtotal_amount', 'tax_amount',
            'discount_amount', 'shipping_cost', 'status_display',
            'payment_method_display', 'payment_status_display',
            'shipping_method_display', 'created_at', 'updated_at',
            'completed_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            allow_empty=False
        ),
        write_only=True
    )
    
    class Meta:
        model = Order
        fields = [
            'items', 'shipping_address', 'billing_address',
            'shipping_method', 'payment_method'
        ]
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required")
        for item in value:
            if 'product_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'product_id' and 'quantity'"
                )
            if item['quantity'] < 1:
                raise serializers.ValidationError(
                    "Quantity must be greater than 0"
                )
        return value
