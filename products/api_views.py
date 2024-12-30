from rest_framework import status, filters
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q, Min, Max
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend

from .models import Product, ProductImage, Brand, Tag, Category
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    ProductImageSerializer, ProductVariantSerializer, ProductSpecificationSerializer,
    BrandSerializer, TagSerializer, CategorySerializer
)
from .filters import ProductFilter
from .utils import create_response
from orders.models import Order
from django.core.paginator import Paginator, EmptyPage

def get_response_schema(data_schema):
    """Helper function to generate standard API response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'data': data_schema,
            'message': openapi.Schema(type=openapi.TYPE_STRING),
            'status_code': openapi.Schema(type=openapi.TYPE_INTEGER)
        }
    )

def get_paginated_response_schema(item_schema):
    """Helper function to generate paginated response schema"""
    return get_response_schema(
        openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'results': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=item_schema
                ),
                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
            }
        )
    )

# Schema definitions for Swagger documentation
product_list_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'slug': openapi.Schema(type=openapi.TYPE_STRING),
        'description': openapi.Schema(type=openapi.TYPE_STRING),
        'price': openapi.Schema(type=openapi.TYPE_NUMBER),
        'discount_price': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
        'stock_quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'is_featured': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'brand': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'slug': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        'images': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'image': openapi.Schema(type=openapi.TYPE_STRING),
                    'alt_text': openapi.Schema(type=openapi.TYPE_STRING),
                    'is_primary': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                }
            )
        ),
        'tags': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'slug': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )
    }
)

brand_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Brand name'),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description='Brand description'),
        'logo': openapi.Schema(type=openapi.TYPE_FILE, description='Brand logo image'),
        'website': openapi.Schema(type=openapi.TYPE_STRING, description='Brand website URL')
    }
)

brand_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'slug': openapi.Schema(type=openapi.TYPE_STRING),
        'description': openapi.Schema(type=openapi.TYPE_STRING),
        'logo': openapi.Schema(type=openapi.TYPE_STRING),
        'website': openapi.Schema(type=openapi.TYPE_STRING),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

tag_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'slug': openapi.Schema(type=openapi.TYPE_STRING),
        'description': openapi.Schema(type=openapi.TYPE_STRING),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

tag_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Tag name'),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description='Tag description')
    }
)

category_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'slug': openapi.Schema(type=openapi.TYPE_STRING),
        'description': openapi.Schema(type=openapi.TYPE_STRING),
        'image': openapi.Schema(type=openapi.TYPE_STRING),
        'parent': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'slug': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
    }
)

category_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['name'],
    properties={
        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Category name'),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description='Category description'),
        'parent_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Parent category ID'),
        'image': openapi.Schema(type=openapi.TYPE_FILE, description='Category image'),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Category status')
    }
)

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get details of a specific product by its slug",
    responses={
        200: get_response_schema(product_list_schema),
        404: "Product not found"
    },
    tags=['Products']
)
@swagger_auto_schema(
    methods=['PUT'],
    operation_description="Update all fields of a specific product",
    request_body=ProductCreateUpdateSerializer,
    responses={
        200: get_response_schema(product_list_schema),
        400: "Invalid data",
        404: "Product not found"
    },
    tags=['Products']
)
@swagger_auto_schema(
    methods=['PATCH'],
    operation_description="Partially update a specific product",
    request_body=ProductCreateUpdateSerializer,
    responses={
        200: get_response_schema(product_list_schema),
        400: "Invalid data",
        404: "Product not found"
    },
    tags=['Products']
)
@swagger_auto_schema(
    methods=['DELETE'],
    operation_description="Delete a specific product",
    responses={
        204: "Product deleted successfully",
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('vendor', 'category', 'brand')
        .prefetch_related('tags', 'images', 'variants', 'specifications'),
        slug=slug
    )

    if request.method == 'GET':
        serializer = ProductDetailSerializer(product)
        return create_response(
            data=serializer.data,
            message="Product details retrieved successfully",
            status_code=status.HTTP_200_OK
        )

    elif request.method == 'PUT':
        serializer = ProductCreateUpdateSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return create_response(
                data=serializer.data,
                message="Product updated successfully",
                status_code=status.HTTP_200_OK
            )
        return create_response(
            data=serializer.errors,
            message="Invalid product data",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'PATCH':
        serializer = ProductCreateUpdateSerializer(
            product,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return create_response(
                data=serializer.data,
                message="Product updated successfully",
                status_code=status.HTTP_200_OK
            )
        return create_response(
            data=serializer.errors,
            message="Invalid product data",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        product.delete()
        return create_response(
            message="Product deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get a list of all products with pagination",
    manual_parameters=[
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=10
        )
    ],
    responses={
        200: get_paginated_response_schema(product_list_schema),
        400: "Invalid query parameters"
    },
    tags=['Products']
)
@swagger_auto_schema(
    methods=['POST'],
    operation_description="Create a new product",
    request_body=ProductCreateUpdateSerializer,
    responses={
        201: get_response_schema(product_list_schema),
        400: "Invalid product data"
    },
    tags=['Products']
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_list(request):
    if request.method == 'GET':
        products = Product.objects.select_related('brand').prefetch_related('images').all()
        
        # Apply filters
        product_filter = ProductFilter(request.GET, queryset=products)
        products = product_filter.qs

        # Apply search if provided
        search_query = request.GET.get('search', '')
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        serializer = ProductListSerializer(products, many=True)
        return create_response(
            data=serializer.data,
            message="Products retrieved successfully",
            status_code=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializer = ProductCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return create_response(
                data=serializer.data,
                message="Product created successfully",
                status_code=status.HTTP_201_CREATED
            )
        return create_response(
            data=serializer.errors,
            message="Invalid product data",
            status_code=status.HTTP_400_BAD_REQUEST
        )

@swagger_auto_schema(
    methods=['POST'],
    operation_description="Add a new image to a product",
    request_body=ProductImageSerializer,
    responses={
        201: get_response_schema(openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'image': openapi.Schema(type=openapi.TYPE_STRING),
                'alt_text': openapi.Schema(type=openapi.TYPE_STRING),
                'is_primary': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        )),
        400: "Invalid image data",
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def add_product_image(request, slug):
    product = get_object_or_404(Product, slug=slug)
    serializer = ProductImageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(product=product)
        return create_response(
            data=serializer.data,
            message="Product image added successfully",
            status_code=status.HTTP_201_CREATED
        )
    return create_response(
        data=serializer.errors,
        message="Invalid image data",
        status_code=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get related products for a specific product",
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=product_list_schema
        )),
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['GET'])
def related_products(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(
        Q(category=product.category) | 
        Q(tags__in=product.tags.all())
    ).exclude(slug=product.slug).distinct()[:5]
    
    serializer = ProductListSerializer(related_products, many=True)
    return create_response(
        data=serializer.data,
        message="Related products retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get reviews for a specific product",
    manual_parameters=[
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=10
        )
    ],
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'average_rating': openapi.Schema(type=openapi.TYPE_NUMBER),
                'total_reviews': openapi.Schema(type=openapi.TYPE_INTEGER),
                'rating_distribution': openapi.Schema(type=openapi.TYPE_OBJECT),
                'reviews': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_STRING),
                        'rating': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'comment': openapi.Schema(type=openapi.TYPE_STRING),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                ))
            }
        )),
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_reviews(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.all()
    rating = request.GET.get('rating')
    
    if rating:
        reviews = reviews.filter(rating=rating)
    
    return create_response(
        data={
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'],
            'total_reviews': reviews.count(),
            'rating_distribution': reviews.values('rating').annotate(count=Count('rating')),
            'reviews': [{
                'user': review.user.username,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at
            } for review in reviews]
        },
        message="Product reviews retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['POST'],
    operation_description="Add a review to a product",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['rating'],
        properties={
            'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description='Rating between 1 and 5'),
            'comment': openapi.Schema(type=openapi.TYPE_STRING, description='Review comment')
        }
    ),
    responses={
        201: "Review added successfully",
        400: "Invalid review data",
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_product_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    rating = request.data.get('rating')
    comment = request.data.get('comment')
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return create_response(
            message="Valid rating between 1 and 5 is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    review = product.reviews.create(
        user=request.user,
        rating=rating,
        comment=comment
    )
    
    return create_response(
        message="Review added successfully",
        status_code=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_add_variant(request, slug):
    product = get_object_or_404(Product, slug=slug)
    serializer = ProductVariantSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(product=product)
        return create_response(
            data=serializer.data,
            message="Product variant added successfully",
            status_code=status.HTTP_201_CREATED
        )
    return create_response(
        data=serializer.errors,
        message="Invalid variant data",
        status_code=status.HTTP_400_BAD_REQUEST
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_add_specification(request, slug):
    product = get_object_or_404(Product, slug=slug)
    serializer = ProductSpecificationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(product=product)
        return create_response(
            data=serializer.data,
            message="Product specification added successfully",
            status_code=status.HTTP_201_CREATED
        )
    return create_response(
        data=serializer.errors,
        message="Invalid specification data",
        status_code=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get variants for a specific product",
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'sku': openapi.Schema(type=openapi.TYPE_STRING),
                    'price': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'stock_quantity': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )
        )),
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_variants(request, slug):
    product = get_object_or_404(Product, slug=slug)
    variants = product.variants.all()
    serializer = ProductVariantSerializer(variants, many=True)
    return create_response(
        data=serializer.data,
        message="Product variants retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get specifications for a specific product",
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'value': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        )),
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_specifications(request, slug):
    product = get_object_or_404(Product, slug=slug)
    specs = product.specifications.all()
    serializer = ProductSpecificationSerializer(specs, many=True)
    return create_response(
        data=serializer.data,
        message="Product specifications retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_order(request, slug):
    product = get_object_or_404(Product, slug=slug)
    quantity = int(request.data.get('quantity', 1))
    
    if product.stock_quantity < quantity:
        return create_response(
            message="Not enough stock available",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        order = Order.objects.create(
            user=request.user,
            product=product,
            quantity=quantity
        )
        
        product.stock_quantity -= quantity
        product.save()
        
        return create_response(
            message="Order created successfully",
            status_code=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return create_response(
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_availability(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return create_response(
        data={
            'in_stock': product.stock_quantity > 0,
            'stock_quantity': product.stock_quantity,
            'available_from': product.available_from
        },
        message="Product availability retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['POST'],
    operation_description="Toggle favorite status of a product",
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_favorite': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'product': product_list_schema
            }
        )),
        401: "Authentication required",
        404: "Product not found"
    },
    tags=['Products']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_favorite(request, slug):
    """
    Toggle favorite status of a product for the authenticated user
    """
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return create_response(
            message="Product not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

    user = request.user
    is_favorite = False

    if product.favorites.filter(id=user.id).exists():
        product.favorites.remove(user)
        message = "Product removed from favorites"
    else:
        product.favorites.add(user)
        is_favorite = True
        message = "Product added to favorites"

    serializer = ProductListSerializer(product)
    
    return create_response(
        data={
            'is_favorite': is_favorite,
            'product': serializer.data
        },
        message=message,
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get user's favorite products",
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=product_list_schema
        )),
        401: "Authentication required"
    },
    tags=['Products']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_favorites(request):
    if not request.user.is_authenticated:
        return create_response(
            message="Authentication required",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
        
    products = request.user.favorite_products.all()
    serializer = ProductListSerializer(products, many=True)
    return create_response(
        data=serializer.data,
        message="Favorite products retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_notify_when_available(request, slug):
    product = get_object_or_404(Product, slug=slug)
    
    if not request.user.is_authenticated:
        return create_response(
            message="Authentication required",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
        
    if product.stock_quantity > 0:
        return create_response(
            message="Product is currently in stock",
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
    product.stock_notifications.get_or_create(user=request.user)
    return create_response(
        message="You will be notified when the product is back in stock",
        status_code=status.HTTP_200_OK
    )

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_trending(request):
    trending = Product.objects.annotate(
        order_count=Count('orderitem'),
        view_count=Count('streamanalytics')
    ).order_by('-order_count', '-view_count')[:10]
    
    serializer = ProductListSerializer(trending, many=True)
    return create_response(
        data=serializer.data,
        message="Trending products retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Search and filter products with advanced options",
    manual_parameters=[
        openapi.Parameter(
            'q', openapi.IN_QUERY,
            description="Search query for product name, description, or SKU",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'category', openapi.IN_QUERY,
            description="Filter by category slug",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'brand', openapi.IN_QUERY,
            description="Filter by brand slug",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'price_min', openapi.IN_QUERY,
            description="Minimum price filter",
            type=openapi.TYPE_NUMBER,
            required=False
        ),
        openapi.Parameter(
            'price_max', openapi.IN_QUERY,
            description="Maximum price filter",
            type=openapi.TYPE_NUMBER,
            required=False
        ),
        openapi.Parameter(
            'in_stock', openapi.IN_QUERY,
            description="Filter by stock availability (true/false)",
            type=openapi.TYPE_BOOLEAN,
            required=False
        ),
        openapi.Parameter(
            'sort_by', openapi.IN_QUERY,
            description="Sort by: -created_at (newest), price_asc, price_desc, popular, rating",
            type=openapi.TYPE_STRING,
            enum=['-created_at', 'price', '-price', 'popular', 'rating'],
            required=False
        )
    ],
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=product_list_schema),
                'filters': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'price_range': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'min': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'max': openapi.Schema(type=openapi.TYPE_NUMBER)
                            }
                        ),
                        'categories': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'brands': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'tags': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                )
            }
        )),
        400: "Invalid query parameters"
    },
    tags=['Products']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_search(request):
    # Get query parameters
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    min_price = request.GET.get('price_min')
    max_price = request.GET.get('price_max')
    tags = request.GET.get('tags', '').split(',') if request.GET.get('tags') else []
    in_stock = request.GET.get('in_stock')
    sort_by = request.GET.get('sort', 'newest')
    page = int(request.GET.get('page', 1))
    page_size = min(int(request.GET.get('page_size', 10)), 50)  # Max 50 items per page

    # Base queryset with optimized joins
    queryset = Product.objects.select_related(
        'category', 'brand', 'vendor'
    ).prefetch_related(
        'images', 'tags', 'variants'
    ).filter(is_active=True)

    # Apply search filters
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(meta_keywords__icontains=query)
        )

    # Apply category filter
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    # Apply brand filter
    if brand_slug:
        queryset = queryset.filter(brand__slug=brand_slug)

    # Apply price range filter
    if min_price:
        queryset = queryset.filter(price__gte=float(min_price))
    if max_price:
        queryset = queryset.filter(price__lte=float(max_price))

    # Apply tags filter
    if tags:
        queryset = queryset.filter(tags__slug__in=tags).distinct()

    # Apply stock filter
    if in_stock is not None:
        if in_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        elif in_stock.lower() == 'false':
            queryset = queryset.filter(stock_quantity=0)

    # Apply sorting
    if sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'popular':
        queryset = queryset.annotate(
            order_count=Count('orders')
        ).order_by('-order_count')
    elif sort_by == 'rating':
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating')
    else:  # newest
        queryset = queryset.order_by('-created_at')

    # Get aggregated data for filters
    price_range = queryset.aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    available_categories = queryset.values_list('category__slug', flat=True).distinct()
    available_brands = queryset.values_list('brand__slug', flat=True).distinct()
    available_tags = queryset.values_list('tags__slug', flat=True).distinct()

    # Pagination
    paginator = Paginator(queryset, page_size)
    
    try:
        products = paginator.page(page)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    
    serializer = ProductListSerializer(products, many=True)
    
    return create_response(
        data={
            'count': paginator.count,
            'next': products.next_page_number() if products.has_next() else None,
            'previous': products.previous_page_number() if products.has_previous() else None,
            'results': serializer.data,
            'filters': {
                'price_range': {
                    'min': price_range['min_price'],
                    'max': price_range['max_price']
                },
                'categories': list(available_categories),
                'brands': list(available_brands),
                'tags': list(available_tags)
            }
        },
        message="Products retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get featured products",
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=product_list_schema
        ))
    },
    tags=['Products']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_featured(request):
    featured_products = Product.objects.filter(is_featured=True)
    serializer = ProductListSerializer(featured_products, many=True)
    return create_response(
        data=serializer.data,
        message="Featured products retrieved successfully",
        status_code=status.HTTP_200_OK
    )

# Product Tags views
@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get tags for a specific product",
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=tag_schema
        )),
        404: "Product not found"
    },
    tags=['Product Tags']
)
@swagger_auto_schema(
    methods=['POST'],
    operation_description="Add tags to a product",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['tag_ids'],
        properties={
            'tag_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description='List of tag IDs to add to the product'
            )
        }
    ),
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=tag_schema
        )),
        400: "Invalid tag IDs",
        404: "Product not found"
    },
    tags=['Product Tags']
)
@swagger_auto_schema(
    methods=['DELETE'],
    operation_description="Remove tags from a product",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['tag_ids'],
        properties={
            'tag_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description='List of tag IDs to remove from the product'
            )
        }
    ),
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=tag_schema
        )),
        400: "Invalid tag IDs",
        404: "Product not found"
    },
    tags=['Product Tags']
)
@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_tags(request, slug):
    """
    Manage tags for a specific product.
    
    GET: Get all tags for a product
    POST: Add tags to a product
    DELETE: Remove tags from a product
    """
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return create_response(
            message="Product not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = TagSerializer(product.tags.all(), many=True)
        return create_response(
            data=serializer.data,
            message="Product tags retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    elif request.method == 'POST':
        tag_ids = request.data.get('tag_ids', [])
        if not isinstance(tag_ids, list):
            return create_response(
                message="tag_ids must be a list of integers",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tags = Tag.objects.filter(id__in=tag_ids)
            if len(tags) != len(tag_ids):
                return create_response(
                    message="Some tag IDs are invalid",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            product.tags.add(*tags)
            serializer = TagSerializer(product.tags.all(), many=True)
            return create_response(
                data=serializer.data,
                message="Tags added to product successfully",
                status_code=status.HTTP_200_OK
            )
        except (ValueError, TypeError):
            return create_response(
                message="Invalid tag IDs format",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    elif request.method == 'DELETE':
        tag_ids = request.data.get('tag_ids', [])
        if not isinstance(tag_ids, list):
            return create_response(
                message="tag_ids must be a list of integers",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tags = Tag.objects.filter(id__in=tag_ids)
            if len(tags) != len(tag_ids):
                return create_response(
                    message="Some tag IDs are invalid",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            product.tags.remove(*tags)
            serializer = TagSerializer(product.tags.all(), many=True)
            return create_response(
                data=serializer.data,
                message="Tags removed from product successfully",
                status_code=status.HTTP_200_OK
            )
        except (ValueError, TypeError):
            return create_response(
                message="Invalid tag IDs format",
                status_code=status.HTTP_400_BAD_REQUEST
            )

@swagger_auto_schema(
    methods=['PUT'],
    operation_description="Replace all tags for a product",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['tag_ids'],
        properties={
            'tag_ids': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description='List of tag IDs to set for the product'
            )
        }
    ),
    responses={
        200: get_response_schema(openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=tag_schema
        )),
        400: "Invalid tag IDs",
        404: "Product not found"
    },
    tags=['Product Tags']
)
@api_view(['PUT'])
@permission_classes([IsAuthenticatedOrReadOnly])
def product_tags_update(request, slug):
    """
    Replace all tags for a product with a new set of tags.
    """
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        return create_response(
            message="Product not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    tag_ids = request.data.get('tag_ids', [])
    if not isinstance(tag_ids, list):
        return create_response(
            message="tag_ids must be a list of integers",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tags = Tag.objects.filter(id__in=tag_ids)
        if len(tags) != len(tag_ids):
            return create_response(
                message="Some tag IDs are invalid",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        product.tags.set(tags)
        serializer = TagSerializer(product.tags.all(), many=True)
        return create_response(
            data=serializer.data,
            message="Product tags updated successfully",
            status_code=status.HTTP_200_OK
        )
    except (ValueError, TypeError):
        return create_response(
            message="Invalid tag IDs format",
            status_code=status.HTTP_400_BAD_REQUEST
        )

# Brand views
@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get a paginated list of brands with optional search filtering",
    manual_parameters=[
        openapi.Parameter(
            'search',
            openapi.IN_QUERY,
            description="Search brands by name",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Page number for pagination",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=1
        ),
        openapi.Parameter(
            'page_size',
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=10
        )
    ],
    responses={
        200: get_paginated_response_schema(brand_response_schema),
        400: "Invalid query parameters"
    },
    tags=['Brands']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def brand_list(request):
    """
    Get a paginated list of brands with optional search filtering.
    
    Query Parameters:
    - search: Filter brands by name
    - page: Page number (default: 1)
    - page_size: Number of items per page (default: 10)
    """
    queryset = Brand.objects.all()
    search = request.query_params.get('search', '')
    
    if search:
        queryset = queryset.filter(name__icontains=search)
    
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 10)
    
    try:
        page = int(page)
        page_size = int(page_size)
    except ValueError:
        return create_response(
            message="Invalid page or page_size parameter",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    paginator = Paginator(queryset, page_size)
    
    try:
        brands = paginator.page(page)
    except EmptyPage:
        brands = paginator.page(paginator.num_pages)
    
    serializer = BrandSerializer(brands, many=True)
    
    return create_response(
        data={
            'results': serializer.data,
            'count': paginator.count,
            'next': brands.has_next(),
            'previous': brands.has_previous(),
            'total_pages': paginator.num_pages,
            'current_page': page
        },
        message="Brands retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['POST'],
    operation_description="Create a new brand",
    request_body=brand_request_schema,
    responses={
        201: get_response_schema(brand_response_schema),
        400: openapi.Response(
            description="Invalid brand data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        )
    },
    tags=['Brands']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def brand_create(request):
    """
    Create a new brand.
    
    Required fields:
    - name: Brand name
    
    Optional fields:
    - description: Brand description
    - logo: Brand logo image
    - website: Brand website URL
    """
    serializer = BrandSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return create_response(
            data=serializer.data,
            message="Brand created successfully",
            status_code=status.HTTP_201_CREATED
        )
    return create_response(
        message="Invalid brand data",
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=serializer.errors
    )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get details of a specific brand by its slug",
    responses={
        200: get_response_schema(brand_response_schema),
        404: "Brand not found"
    },
    tags=['Brands']
)
@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def brand_detail(request, slug):
    """
    Get details of a specific brand by its slug.
    """
    try:
        brand = Brand.objects.get(slug=slug)
    except Brand.DoesNotExist:
        return create_response(
            message="Brand not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    serializer = BrandSerializer(brand)
    return create_response(
        data=serializer.data,
        message="Brand details retrieved successfully",
        status_code=status.HTTP_200_OK
    )

@swagger_auto_schema(
    methods=['PUT'],
    operation_description="Update all fields of a specific brand",
    request_body=brand_request_schema,
    responses={
        200: get_response_schema(brand_response_schema),
        400: "Invalid brand data",
        404: "Brand not found"
    },
    tags=['Brands']
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def brand_update(request, slug):
    """
    Update all fields of a specific brand.
    
    All fields are required:
    - name: Brand name
    - description: Brand description
    - logo: Brand logo image
    - website: Brand website URL
    """
    try:
        brand = Brand.objects.get(slug=slug)
    except Brand.DoesNotExist:
        return create_response(
            message="Brand not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    serializer = BrandSerializer(brand, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return create_response(
            data=serializer.data,
            message="Brand updated successfully",
            status_code=status.HTTP_200_OK
        )
    return create_response(
        message="Invalid brand data",
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=serializer.errors
    )

@swagger_auto_schema(
    methods=['PATCH'],
    operation_description="Partially update a specific brand",
    request_body=brand_request_schema,
    responses={
        200: get_response_schema(brand_response_schema),
        400: "Invalid brand data",
        404: "Brand not found"
    },
    tags=['Brands']
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def brand_partial_update(request, slug):
    """
    Partially update a specific brand.
    
    Optional fields (include only fields to update):
    - name: Brand name
    - description: Brand description
    - logo: Brand logo image
    - website: Brand website URL
    """
    try:
        brand = Brand.objects.get(slug=slug)
    except Brand.DoesNotExist:
        return create_response(
            message="Brand not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    serializer = BrandSerializer(brand, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return create_response(
            data=serializer.data,
            message="Brand updated successfully",
            status_code=status.HTTP_200_OK
        )
    return create_response(
        message="Invalid brand data",
        status_code=status.HTTP_400_BAD_REQUEST,
        errors=serializer.errors
    )

@swagger_auto_schema(
    methods=['DELETE'],
    operation_description="Delete a specific brand",
    responses={
        204: "Brand deleted successfully",
        404: "Brand not found"
    },
    tags=['Brands']
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def brand_delete(request, slug):
    """
    Delete a specific brand.
    """
    try:
        brand = Brand.objects.get(slug=slug)
    except Brand.DoesNotExist:
        return create_response(
            message="Brand not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    brand.delete()
    return create_response(
        message="Brand deleted successfully",
        status_code=status.HTTP_204_NO_CONTENT
    )

# Category views
@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get a paginated list of categories with optional search filtering",
    manual_parameters=[
        openapi.Parameter(
            'search',
            openapi.IN_QUERY,
            description="Search categories by name or description",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'parent_id',
            openapi.IN_QUERY,
            description="Filter by parent category ID",
            type=openapi.TYPE_INTEGER,
            required=False
        ),
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Page number for pagination",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=1
        ),
        openapi.Parameter(
            'page_size',
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=10
        )
    ],
    responses={
        200: get_paginated_response_schema(category_schema),
        400: "Invalid query parameters"
    },
    tags=['Categories']
)
@swagger_auto_schema(
    methods=['POST'],
    operation_description="Create a new category",
    request_body=category_request_schema,
    responses={
        201: get_response_schema(category_schema),
        400: "Invalid category data"
    },
    tags=['Categories']
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
@parser_classes([MultiPartParser, FormParser])
def category_list(request):
    """
    GET: Get a paginated list of categories with optional search filtering
    POST: Create a new category
    """
    if request.method == 'GET':
        search_query = request.GET.get('search', '').strip()
        parent_id = request.GET.get('parent_id')
        
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
        except ValueError:
            return create_response(
                message="Invalid page or page_size parameter",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Category.objects.all().order_by('name')
        
        if parent_id:
            try:
                parent_id = int(parent_id)
                queryset = queryset.filter(parent_id=parent_id)
            except ValueError:
                return create_response(
                    message="Invalid parent_id parameter",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        paginator = Paginator(queryset, page_size)
        try:
            categories = paginator.page(page)
        except EmptyPage:
            categories = paginator.page(paginator.num_pages)
        
        serializer = CategorySerializer(categories, many=True)
        return create_response(
            data={
                'results': serializer.data,
                'count': paginator.count,
                'next': categories.has_next(),
                'previous': categories.has_previous(),
                'total_pages': paginator.num_pages,
                'current_page': page
            },
            message="Categories retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return create_response(
                data=serializer.data,
                message=f"Category '{category.name}' created successfully",
                status_code=status.HTTP_201_CREATED
            )
        return create_response(
            message="Invalid category data",
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors
        )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get details of a specific category",
    responses={
        200: get_response_schema(category_schema),
        404: "Category not found"
    },
    tags=['Categories']
)
@swagger_auto_schema(
    methods=['PUT'],
    operation_description="Update all fields of a specific category",
    request_body=category_request_schema,
    responses={
        200: get_response_schema(category_schema),
        400: "Invalid category data",
        404: "Category not found"
    },
    tags=['Categories']
)
@swagger_auto_schema(
    methods=['PATCH'],
    operation_description="Partially update a specific category",
    request_body=category_request_schema,
    responses={
        200: get_response_schema(category_schema),
        400: "Invalid category data",
        404: "Category not found"
    },
    tags=['Categories']
)
@swagger_auto_schema(
    methods=['DELETE'],
    operation_description="Delete a specific category",
    responses={
        204: "Category deleted successfully",
        404: "Category not found"
    },
    tags=['Categories']
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
@parser_classes([MultiPartParser, FormParser])
def category_detail(request, slug):
    """
    GET: Get details of a specific category
    PUT: Update all fields of a specific category
    PATCH: Partially update a specific category
    DELETE: Delete a specific category
    """
    try:
        category = Category.objects.get(slug=slug)
    except Category.DoesNotExist:
        return create_response(
            message="Category not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = CategorySerializer(category)
        return create_response(
            data=serializer.data,
            message="Category details retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        if serializer.is_valid():
            category = serializer.save()
            return create_response(
                data=serializer.data,
                message=f"Category '{category.name}' updated successfully",
                status_code=status.HTTP_200_OK
            )
        return create_response(
            message="Invalid category data",
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors
        )
    
    elif request.method == 'DELETE':
        category.delete()
        return create_response(
            message=f"Category '{category.name}' deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )

# Tag views
@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get a paginated list of tags with optional search filtering",
    manual_parameters=[
        openapi.Parameter(
            'search', openapi.IN_QUERY,
            description="Search tags by name or description",
            type=openapi.TYPE_STRING,
            required=False
        ),
        openapi.Parameter(
            'page', openapi.IN_QUERY,
            description="Page number for pagination",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=1
        ),
        openapi.Parameter(
            'page_size', openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=10
        )
    ],
    responses={
        200: get_paginated_response_schema(tag_schema),
        400: "Invalid query parameters"
    },
    tags=['Tags']
)
@swagger_auto_schema(
    methods=['POST'],
    operation_description="Create a new tag",
    request_body=tag_request_schema,
    responses={
        201: get_response_schema(tag_schema),
        400: openapi.Response(
            description="Invalid tag data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'errors': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        )
    },
    tags=['Tags']
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def tag_list(request):
    print("hello")

    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        
        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            return create_response(
                message="Invalid page or page_size parameter",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Tag.objects.all().order_by('name')
        print(queryset)
        
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        paginator = Paginator(queryset, page_size)
        
        try:
            tags = paginator.page(page)
        except EmptyPage:
            tags = paginator.page(paginator.num_pages)
        
        serializer = TagSerializer(tags, many=True)
        return create_response(
            data={
                'results': serializer.data,
                'count': paginator.count,
                'next': tags.has_next(),
                'previous': tags.has_previous(),
                'total_pages': paginator.num_pages,
                'current_page': page
            },
            message="Tags retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    elif request.method == 'POST':
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            tag = serializer.save()
            return create_response(
                data=serializer.data,
                message=f"Tag '{tag.name}' created successfully",
                status_code=status.HTTP_201_CREATED
            )
        return create_response(
            message="Invalid tag data",
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors
        )

@swagger_auto_schema(
    methods=['GET'],
    operation_description="Get details of a specific tag",
    responses={
        200: get_response_schema(tag_schema),
        404: "Tag not found"
    },
    tags=['Tags']
)
@swagger_auto_schema(
    methods=['PUT'],
    operation_description="Update all fields of a specific tag",
    request_body=tag_request_schema,
    responses={
        200: get_response_schema(tag_schema),
        400: "Invalid tag data",
        404: "Tag not found"
    },
    tags=['Tags']
)
@swagger_auto_schema(
    methods=['PATCH'],
    operation_description="Partially update a specific tag",
    request_body=tag_request_schema,
    responses={
        200: get_response_schema(tag_schema),
        400: "Invalid tag data",
        404: "Tag not found"
    },
    tags=['Tags']
)
@swagger_auto_schema(
    methods=['DELETE'],
    operation_description="Delete a specific tag",
    responses={
        204: "Tag deleted successfully",
        404: "Tag not found"
    },
    tags=['Tags']
)
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def tag_detail(request, pk):
    """
    GET: Get details of a specific tag
    PUT: Update all fields of a specific tag
    PATCH: Partially update a specific tag
    DELETE: Delete a specific tag
    """
    try:
        tag = Tag.objects.get(pk=pk)
    except Tag.DoesNotExist:
        return create_response(
            message="Tag not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = TagSerializer(tag)
        return create_response(
            data=serializer.data,
            message="Tag details retrieved successfully",
            status_code=status.HTTP_200_OK
        )
    
    elif request.method in ['PUT', 'PATCH']:
        serializer = TagSerializer(tag, data=request.data, partial=request.method == 'PATCH')
        if serializer.is_valid():
            serializer.save()
            return create_response(
                data=serializer.data,
                message="Tag updated successfully",
                status_code=status.HTTP_200_OK
            )
        return create_response(
            message="Invalid tag data",
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors
        )
    
    elif request.method == 'DELETE':
        tag.delete()
        return create_response(
            message="Tag deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
