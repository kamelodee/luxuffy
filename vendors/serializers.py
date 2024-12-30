from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vendor

User = get_user_model()

class VendorRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'email', 'username', 'business_name', 'business_type', 
            'store_name', 'full_name', 'phone_number', 'phone_number2'
        ]
        read_only_fields = ['id', 'email', 'username']

class VendorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'email', 'username', 'business_name', 'business_type', 
            'store_name', 'logo_url', 'banner_url', 'verification_status',
            'account_status', 'full_name', 'email', 'phone_number', 'phone_number2',
            'address_line1', 'address_line2', 'city', 'locality', 'region',
            'country', 'postal_code', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'username', 'verification_status', 
                           'account_status', 'created_at', 'updated_at']

class VendorShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'ship_from_address1', 'ship_from_address2', 'ship_from_city',
            'ship_from_locality', 'ship_from_region', 'ship_from_country',
            'return_address1', 'return_address2', 'return_city',
            'return_locality', 'return_region', 'return_country',
            'latitude', 'longitude'
        ]

class VendorPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'payment_type', 'account_number', 'mobile_money_number'
        ]

    def validate(self, data):
        payment_type = data.get('payment_type')
        account_number = data.get('account_number')
        mobile_money_number = data.get('mobile_money_number')

        if payment_type in ['bank_transfer', 'both'] and not account_number:
            raise serializers.ValidationError(
                {'account_number': 'Bank account number is required for bank transfers.'}
            )

        if payment_type in ['mobile_money', 'both'] and not mobile_money_number:
            raise serializers.ValidationError(
                {'mobile_money_number': 'Mobile money number is required for mobile money payments.'}
            )

        return data

class VendorVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'id_type', 'id_number', 'tin_number', 
            'id_front_url', 'id_back_url',
            'verification_status', 'verification_date', 'verification_notes'
        ]
        read_only_fields = ['verification_status', 'verification_date', 'verification_notes']

class VendorSEOSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'meta_title', 'meta_description', 'meta_keywords', 'canonical_url'
        ]

class VendorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = [
            'id', 'store_name', 'business_name', 'logo_url', 
            'verification_status', 'account_status', 'city', 'region'
        ]
        read_only_fields = fields
