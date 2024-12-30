from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from products.models import Product
from products.utils import create_response


# Swagger schemas
cart_item_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Cart item ID'),
        'product': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Product ID'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Product name'),
                'slug': openapi.Schema(type=openapi.TYPE_STRING, description='Product slug'),
                'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Product price'),
                'image': openapi.Schema(type=openapi.TYPE_STRING, description='Product image URL'),
            }
        ),
        'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity of the item'),
        'price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Unit price at time of adding'),
        'discount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Discount amount'),
        'tax': openapi.Schema(type=openapi.TYPE_NUMBER, description='Tax amount'),
        'total_price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total price including tax and discount'),
        'is_available': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether the item is in stock'),
        'is_wishlist_item': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Whether item is saved for later'),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

cart_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Cart ID'),
        'user': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
        'items': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=cart_item_schema,
            description='List of items in the cart'
        ),
        'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total cart amount'),
        'total_discount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total discount amount'),
        'total_tax': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total tax amount'),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

cart_item_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['product_id', 'quantity'],
    properties={
        'product_id': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='ID of the product to add to cart'
        ),
        'quantity': openapi.Schema(
            type=openapi.TYPE_INTEGER,
            description='Quantity of the product (must be greater than 0)'
        ),
        'is_wishlist_item': openapi.Schema(
            type=openapi.TYPE_BOOLEAN,
            description='Whether to save item for later (default: false)'
        )
    }
)

cart_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Response status'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Response message'),
        'data': cart_schema
    }
)

error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Error status'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description='Detailed error information')
    }
)


@swagger_auto_schema(
    methods=['GET'],
    operation_description="""
    Retrieve the current user's shopping cart.
    
    Returns the cart with all its items, including:
    - List of cart items with product details
    - Total amount
    - Total discount
    - Total tax
    
    Authentication is required.
    """,
    responses={
        200: openapi.Response(
            description="Cart retrieved successfully",
            schema=cart_response_schema
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided",
            schema=error_response_schema
        )
    },
    tags=['Cart']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    """Get the current user's cart"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return create_response(
        data=serializer.data,
        message="Cart retrieved successfully",
        status_code=status.HTTP_200_OK
    )


@swagger_auto_schema(
    methods=['POST'],
    operation_description="""
    Add a product to the shopping cart.
    
    Required fields:
    - product_id: ID of the product to add
    - quantity: Number of items (must be greater than 0)
    
    Optional fields:
    - is_wishlist_item: Save for later (default: false)
    
    If the product is already in the cart, its quantity will be updated.
    Authentication is required.
    """,
    request_body=cart_item_request_schema,
    responses={
        201: openapi.Response(
            description="Item added to cart successfully",
            schema=cart_response_schema
        ),
        400: openapi.Response(
            description="Invalid request data",
            schema=error_response_schema
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided",
            schema=error_response_schema
        ),
        404: openapi.Response(
            description="Product not found",
            schema=error_response_schema
        )
    },
    tags=['Cart']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Add an item to the cart"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    serializer = CartItemSerializer(data=request.data)
    if serializer.is_valid():
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        is_wishlist = serializer.validated_data.get('is_wishlist_item', False)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return create_response(
                message="Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'quantity': quantity,
                'price': product.price,
                'is_wishlist_item': is_wishlist
            }
        )
        
        if not created:
            cart_item.quantity = quantity
            cart_item.is_wishlist_item = is_wishlist
            cart_item.save()
        
        cart_serializer = CartSerializer(cart)
        return create_response(
            data=cart_serializer.data,
            message="Item added to cart successfully",
            status_code=status.HTTP_201_CREATED
        )
    
    return create_response(
        message="Invalid request data",
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=serializer.errors
    )


@swagger_auto_schema(
    methods=['PUT'],
    operation_description="""
    Update the quantity or wishlist status of a cart item.
    
    Required fields:
    - quantity: New quantity (must be greater than 0)
    
    Optional fields:
    - is_wishlist_item: Save for later status
    
    Authentication is required.
    The user can only update items in their own cart.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['quantity'],
        properties={
            'quantity': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description='New quantity for the item (must be greater than 0)'
            ),
            'is_wishlist_item': openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description='Whether to save item for later'
            )
        }
    ),
    responses={
        200: openapi.Response(
            description="Cart item updated successfully",
            schema=cart_response_schema
        ),
        400: openapi.Response(
            description="Invalid quantity",
            schema=error_response_schema
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided",
            schema=error_response_schema
        ),
        404: openapi.Response(
            description="Cart item not found",
            schema=error_response_schema
        )
    },
    tags=['Cart']
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )
    except CartItem.DoesNotExist:
        return create_response(
            message="Cart item not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    quantity = request.data.get('quantity')
    is_wishlist = request.data.get('is_wishlist_item', cart_item.is_wishlist_item)
    
    if not quantity or quantity < 1:
        return create_response(
            message="Invalid quantity",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    cart_item.quantity = quantity
    cart_item.is_wishlist_item = is_wishlist
    cart_item.save()
    
    cart_serializer = CartSerializer(cart_item.cart)
    return create_response(
        data=cart_serializer.data,
        message="Cart item updated successfully",
        status_code=status.HTTP_200_OK
    )


@swagger_auto_schema(
    methods=['DELETE'],
    operation_description="""
    Remove an item from the shopping cart.
    
    Authentication is required.
    The user can only remove items from their own cart.
    """,
    responses={
        204: openapi.Response(
            description="Item removed successfully"
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided",
            schema=error_response_schema
        ),
        404: openapi.Response(
            description="Cart item not found",
            schema=error_response_schema
        )
    },
    tags=['Cart']
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    """Remove an item from the cart"""
    try:
        cart_item = CartItem.objects.get(
            id=item_id,
            cart__user=request.user
        )
    except CartItem.DoesNotExist:
        return create_response(
            message="Cart item not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    cart_item.delete()
    return create_response(
        message="Item removed from cart successfully",
        status_code=status.HTTP_204_NO_CONTENT
    )


@swagger_auto_schema(
    methods=['POST'],
    operation_description="""
    Remove all items from the shopping cart.
    
    Authentication is required.
    This will permanently delete all items from the user's cart.
    """,
    responses={
        204: openapi.Response(
            description="Cart cleared successfully"
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided",
            schema=error_response_schema
        ),
        404: openapi.Response(
            description="Cart not found",
            schema=error_response_schema
        )
    },
    tags=['Cart']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from the cart"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    return create_response(
        message="Cart cleared successfully",
        status_code=status.HTTP_204_NO_CONTENT
    )


@swagger_auto_schema(
    methods=['POST'],
    operation_description="""
    Move all items in the cart to the wishlist.
    
    Authentication is required.
    This will update all items in the cart to be wishlist items.
    """,
    responses={
        200: openapi.Response(
            description="All items moved to wishlist successfully",
            schema=cart_response_schema
        ),
        401: openapi.Response(
            description="Authentication credentials were not provided",
            schema=error_response_schema
        ),
        404: openapi.Response(
            description="Cart not found",
            schema=error_response_schema
        )
    },
    tags=['Cart']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def move_all_to_wishlist(request):
    """Move all cart items to wishlist"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().update(is_wishlist_item=True)
    
    cart_serializer = CartSerializer(cart)
    return create_response(
        data=cart_serializer.data,
        message="All items moved to wishlist successfully",
        status_code=status.HTTP_200_OK
    )
