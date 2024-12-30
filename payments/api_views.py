import uuid
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Payment, PaymentRefund
from .serializers import PaymentSerializer, PaymentRefundSerializer
from .paystack import PaystackAPI
from orders.models import Order
from products.utils import create_response


# Initialize Paystack
paystack = PaystackAPI()


# Swagger schemas
payment_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Payment ID'),
        'order': openapi.Schema(type=openapi.TYPE_INTEGER, description='Order ID'),
        'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Payment amount'),
        'reference': openapi.Schema(type=openapi.TYPE_STRING, description='Payment reference'),
        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Payment status'),
        'payment_method': openapi.Schema(type=openapi.TYPE_STRING, description='Payment method'),
        'currency': openapi.Schema(type=openapi.TYPE_STRING, description='Payment currency'),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'paid_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)


# Request Serializers for Swagger
class InitializePaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(help_text="ID of the order to pay for")


class RequestRefundSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(help_text="ID of the payment to refund")
    reason = serializers.CharField(help_text="Reason for the refund")
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        help_text="Amount to refund (optional)"
    )


@swagger_auto_schema(
    methods=['POST'],
    operation_description="""
    Initialize a payment transaction with Paystack.
    
    Required fields:
    - order_id: ID of the order to pay for
    
    Returns:
    - authorization_url: URL to redirect user for payment
    - access_code: Payment access code
    - reference: Payment reference
    """,
    request_body=InitializePaymentSerializer,
    responses={
        200: openapi.Response(
            description="Payment initialized successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'authorization_url': openapi.Schema(type=openapi.TYPE_STRING),
                            'access_code': openapi.Schema(type=openapi.TYPE_STRING),
                            'reference': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                }
            )
        ),
        400: "Invalid order ID or order already paid",
        401: "Authentication required",
        404: "Order not found"
    },
    tags=['Payments']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initialize_payment(request):
    """Initialize a payment transaction"""
    serializer = InitializePaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return create_response(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    order_id = serializer.validated_data['order_id']
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return create_response(
            message="Order not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if hasattr(order, 'payment'):
        return create_response(
            message="Payment already exists for this order",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate unique reference
    reference = str(uuid.uuid4())
    
    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        order=order,
        amount=order.total_amount,
        reference=reference,
        payment_method='card',
        currency='NGN'
    )
    
    # Initialize transaction with Paystack
    response = paystack.initialize_transaction(
        email=request.user.email,
        amount=float(order.total_amount),
        reference=reference,
        metadata={
            'order_id': order.id,
            'payment_id': payment.id
        }
    )
    
    if response.get('status'):
        data = response.get('data', {})
        return create_response(
            data={
                'authorization_url': data.get('authorization_url'),
                'access_code': data.get('access_code'),
                'reference': reference
            },
            message="Payment initialized successfully",
            status_code=status.HTTP_200_OK
        )
    
    payment.delete()  # Clean up if initialization failed
    return create_response(
        message="Failed to initialize payment",
        status_code=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    methods=['GET'],
    operation_description="""
    Verify a payment transaction.
    
    Required query parameters:
    - reference: Payment reference to verify
    """,
    manual_parameters=[
        openapi.Parameter(
            'reference',
            openapi.IN_QUERY,
            description="Payment reference to verify",
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="Payment verified successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': payment_schema
                }
            )
        ),
        400: "Invalid reference",
        401: "Authentication required",
        404: "Payment not found"
    },
    tags=['Payments']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """Verify a payment transaction"""
    reference = request.GET.get('reference')
    if not reference:
        return create_response(
            message="Payment reference is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        payment = Payment.objects.get(reference=reference, user=request.user)
    except Payment.DoesNotExist:
        return create_response(
            message="Payment not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Verify with Paystack
    response = paystack.verify_transaction(reference)
    
    if response.get('status'):
        data = response.get('data', {})
        if data.get('status') == 'success':
            # Update payment record
            payment.status = 'success'
            payment.paystack_reference = data.get('reference')
            payment.gateway_response = data.get('gateway_response')
            payment.paid_at = timezone.now()
            payment.save()
            
            # Update order
            order = payment.order
            order.payment_status = 'paid'
            order.save()
            
            serializer = PaymentSerializer(payment)
            return create_response(
                data=serializer.data,
                message="Payment verified successfully",
                status_code=status.HTTP_200_OK
            )
    
    return create_response(
        message="Payment verification failed",
        status_code=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    methods=['POST'],
    operation_description="""
    Request a refund for a payment.
    
    Required fields:
    - payment_id: ID of the payment to refund
    - reason: Reason for the refund
    
    Optional fields:
    - amount: Amount to refund (defaults to full payment amount)
    """,
    request_body=RequestRefundSerializer,
    responses={
        200: openapi.Response(
            description="Refund initiated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'reference': openapi.Schema(type=openapi.TYPE_STRING),
                            'status': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                }
            )
        ),
        400: "Invalid payment ID or payment not eligible for refund",
        401: "Authentication required",
        404: "Payment not found"
    },
    tags=['Payments']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_refund(request):
    """Request a refund for a payment"""
    serializer = RequestRefundSerializer(data=request.data)
    if not serializer.is_valid():
        return create_response(
            message="Invalid data",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    payment_id = serializer.validated_data['payment_id']
    reason = serializer.validated_data['reason']
    amount = serializer.validated_data.get('amount')
    
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
    except Payment.DoesNotExist:
        return create_response(
            message="Payment not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if payment.status != 'success':
        return create_response(
            message="Only successful payments can be refunded",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate refund reference
    refund_reference = str(uuid.uuid4())
    
    # Create refund record
    refund = PaymentRefund.objects.create(
        payment=payment,
        amount=amount or payment.amount,
        reference=refund_reference,
        reason=reason
    )
    
    # Request refund from Paystack
    response = paystack.create_refund(
        transaction_reference=payment.paystack_reference,
        amount=float(refund.amount) if amount else None
    )
    
    if response.get('status'):
        data = response.get('data', {})
        refund.status = 'success'
        refund.paystack_reference = data.get('reference')
        refund.gateway_response = data.get('gateway_response')
        refund.processed_at = timezone.now()
        refund.save()
        
        return create_response(
            data={
                'reference': refund_reference,
                'status': 'success'
            },
            message="Refund initiated successfully",
            status_code=status.HTTP_200_OK
        )
    
    refund.delete()  # Clean up if refund failed
    return create_response(
        message="Failed to initiate refund",
        status_code=status.HTTP_400_BAD_REQUEST
    )
