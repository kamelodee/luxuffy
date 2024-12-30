from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Address, Order, OrderItem, WishlistItem, Notification, NotificationSettings, UserProfile

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    phone_number = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)
    avatar_url = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'birth_date', 'avatar_url']
        read_only_fields = ['id', 'username', 'email']

    def update(self, instance, validated_data):
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
        
        # Update User fields
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return data

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'name', 'type', 'label', 'address_line1', 'address_line2', 
                 'city', 'state', 'postal_code', 'country', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_id', 'name', 'quantity', 'price', 'image_url']

class OrderSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    shipping_address = AddressSerializer()

    class Meta:
        model = Order
        fields = ['id', 'date', 'status', 'total_amount', 'items_count', 'shipping_address']

    def get_items_count(self, obj):
        return obj.items.count()

class OrderDetailSerializer(OrderSerializer):
    items = OrderItemSerializer(many=True)
    tracking_info = serializers.SerializerMethodField()

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ['items', 'tracking_info']

    def get_tracking_info(self, obj):
        return {
            'carrier': obj.shipping_carrier,
            'tracking_number': obj.tracking_number,
            'estimated_delivery': obj.estimated_delivery_date
        }

class WishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['id', 'product_id', 'name', 'price', 'image_url', 'added_date', 'in_stock']
        read_only_fields = ['id', 'name', 'price', 'image_url', 'added_date', 'in_stock']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'message', 'read', 'created_at']
        read_only_fields = ['id', 'created_at']

class NotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSettings
        fields = ['email_notifications', 'push_notifications']
