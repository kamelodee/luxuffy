from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 'price',
            'discount', 'tax', 'total_price', 'is_available',
            'is_wishlist_item', 'created_at', 'updated_at'
        ]
        read_only_fields = ['price', 'discount', 'tax', 'is_available']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'items', 'total_amount', 'total_discount',
            'total_tax', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'total_amount', 'total_discount', 'total_tax']
