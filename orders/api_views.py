from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from products.models import Product
from products.utils import create_response
from cart.models import Cart


# Swagger schemas
order_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Order item ID'),
        'product': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Product name'),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Product price'),
            }
        ),
        'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity ordered'),
        'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Price at time of order'),
        'total_price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total price for this item'),
        'discount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Discount amount'),
        'tax': openapi.Schema(type=openapi.TYPE_NUMBER, description='Tax amount')
    }
)

order_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Order ID'),
        'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'items': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=order_item_schema,
            description='List of items in the order'
        ),
        'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total order amount'),
        'subtotal_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Subtotal before tax and discounts'),
        'tax_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total tax amount'),
        'discount_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total discount amount'),
        'shipping_address': openapi.Schema(type=openapi.TYPE_STRING, description='Shipping address'),
        'shipping_method': openapi.Schema(type=openapi.TYPE_STRING, description='Shipping method'),
        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Order status'),
        'payment_method': openapi.Schema(type=openapi.TYPE_STRING, description='Payment method'),
        'payment_status': openapi.Schema(type=openapi.TYPE_STRING, description='Payment status')
    }
)

order_create_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['items', 'shipping_address', 'payment_method'],
    properties={
        'items': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['product_id', 'quantity'],
                properties={
                    'product_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                    'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity to order')
                }
            )
        ),
        'shipping_address': openapi.Schema(type=openapi.TYPE_STRING, description='Shipping address'),
        'billing_address': openapi.Schema(type=openapi.TYPE_STRING, description='Billing address'),
        'shipping_method': openapi.Schema(type=openapi.TYPE_STRING, description='Shipping method'),
        'payment_method': openapi.Schema(type=openapi.TYPE_STRING, description='Payment method')
    }
)


@swagger_auto_schema(
    methods=['GET'],
    operation_description="""
    Retrieve a list of all orders for the current user.
    
    Returns all orders with their items, status, and payment information.
    Orders are sorted by creation date (newest first).
    """,
    responses={
        200: openapi.Response(
            description="Orders retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=order_schema
                    )
                }
            )
        ),
        401: "Authentication required"
    },
    tags=['Orders']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """Get list of orders for the current user"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return create_response(
        data=serializer.data,
        message="Orders retrieved successfully",
        status_code=status.HTTP_200_OK
    )


@swagger_auto_schema(
    methods=['POST'],
    operation_description="""
    Create a new order.
    
    Required fields:
    - items: List of items with product_id and quantity
    - shipping_address: Delivery address
    - payment_method: Payment method to use
    
    Optional fields:
    - billing_address: Billing address (defaults to shipping address)
    - shipping_method: Shipping method (defaults to 'standard')
    """,
    request_body=order_create_schema,
    responses={
        201: openapi.Response(
            description="Order created successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': order_schema
                }
            )
        ),
        400: "Invalid order data",
        401: "Authentication required"
    },
    tags=['Orders']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Create a new order"""
    serializer = OrderCreateSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                user=request.user,
                shipping_address=serializer.validated_data['shipping_address'],
                billing_address=serializer.validated_data.get(
                    'billing_address',
                    serializer.validated_data['shipping_address']
                ),
                shipping_method=serializer.validated_data.get(
                    'shipping_method', 'standard'
                ),
                payment_method=serializer.validated_data['payment_method'],
                total_amount=0,
                subtotal_amount=0
            )
            
            # Add order items
            total_amount = 0
            for item_data in serializer.validated_data['items']:
                product = get_object_or_404(
                    Product, id=item_data['product_id']
                )
                quantity = item_data['quantity']
                price = product.price
                total_price = price * quantity
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price,
                    total_price=total_price
                )
                total_amount += total_price
            
            # Update order totals
            order.subtotal_amount = total_amount
            order.total_amount = total_amount
            order.save()
            
            # Clear cart if order was successful
            Cart.objects.filter(user=request.user).delete()
            
            serializer = OrderSerializer(order)
            return create_response(
                data=serializer.data,
                message="Order created successfully",
                status_code=status.HTTP_201_CREATED
            )
    
    return create_response(
        message="Invalid order data",
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=serializer.errors
    )


@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get details of a specific order",
    responses={
        200: openapi.Response(
            description="Order details retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': order_schema
                }
            )
        ),
        401: "Authentication required",
        404: "Order not found"
    },
    tags=['Orders']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    """Get details of a specific order"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return create_response(
            message="Order not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    serializer = OrderSerializer(order)
    return create_response(
        data=serializer.data,
        message="Order details retrieved successfully",
        status_code=status.HTTP_200_OK
    )


@swagger_auto_schema(
    methods=['POST'],
    operation_description="""
    Cancel an order.
    
    Only orders in 'pending' or 'processing' status can be cancelled.
    """,
    responses={
        200: openapi.Response(
            description="Order cancelled successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': order_schema
                }
            )
        ),
        400: "Order cannot be cancelled",
        401: "Authentication required",
        404: "Order not found"
    },
    tags=['Orders']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request, order_id):
    """Cancel an order"""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return create_response(
            message="Order not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if order.status not in ['pending', 'processing']:
        return create_response(
            message="Order cannot be cancelled",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    order.status = 'cancelled'
    order.save()
    
    serializer = OrderSerializer(order)
    return create_response(
        data=serializer.data,
        message="Order cancelled successfully",
        status_code=status.HTTP_200_OK
    )
