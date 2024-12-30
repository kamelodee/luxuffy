from rest_framework import serializers
from .models import Payment, PaymentRefund


class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'order', 'amount', 'reference',
            'paystack_reference', 'status', 'status_display',
            'payment_method', 'currency', 'gateway_response',
            'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = [
            'user', 'reference', 'paystack_reference', 'status',
            'gateway_response', 'created_at', 'updated_at', 'paid_at'
        ]


class PaymentRefundSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentRefund
        fields = [
            'id', 'payment', 'amount', 'reference',
            'paystack_reference', 'status', 'status_display',
            'reason', 'gateway_response', 'created_at',
            'updated_at', 'processed_at'
        ]
        read_only_fields = [
            'reference', 'paystack_reference', 'status',
            'gateway_response', 'created_at', 'updated_at',
            'processed_at'
        ]
