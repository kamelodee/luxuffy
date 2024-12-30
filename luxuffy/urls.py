"""
URL configuration for luxuffy project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Luxuffy E-commerce API",
        default_version='v1',
        description="""
        Welcome to the Luxuffy E-commerce API documentation. This API provides endpoints for managing an e-commerce platform.

        ## Authentication
        Most endpoints require authentication. Use the following methods:
        * Bearer Token Authentication
        * Session Authentication for browser access

        ## Features
        1. **Products Management**
           * Browse and search products
           * Manage product variants
           * Handle product images
           * Product tags and categories

        2. **Shopping Cart**
           * Add/remove items
           * Update quantities
           * Save items for later
           * Calculate totals

        3. **Orders**
           * Create orders
           * Track order status
           * Order history
           * Cancel orders

        4. **Categories**
           * Browse categories
           * Nested category structure
           * Category filtering

        5. **User Management**
           * User registration
           * Profile management
           * Address management

        ## Rate Limiting
        API requests are rate-limited to:
        * 100 requests per minute for authenticated users
        * 20 requests per minute for anonymous users

        ## Response Format
        All responses follow this structure:
        ```json
        {
            "status": "success|error",
            "message": "Response message",
            "data": {
                // Response data here
            },
            "errors": {
                // Error details if any
            }
        }
        ```

        ## Status Codes
        * 200: Success
        * 201: Created
        * 400: Bad Request
        * 401: Unauthorized
        * 403: Forbidden
        * 404: Not Found
        * 429: Too Many Requests
        * 500: Server Error

        ## Support
        For API support, please contact:
        * Email: support@luxuffy.com
        * Documentation: https://docs.luxuffy.com
        """,
        terms_of_service="https://www.luxuffy.com/terms/",
        contact=openapi.Contact(
            name="API Support",
            url="https://www.luxuffy.com/support/",
            email="support@luxuffy.com"
        ),
        license=openapi.License(
            name="MIT License",
            url="https://opensource.org/licenses/MIT"
        ),
        x_logo={
            "url": "https://www.luxuffy.com/static/images/logo.png",
            "backgroundColor": "#FFFFFF",
            "altText": "Luxuffy Logo"
        },
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/products/', include('products.api_urls')),
    path('api/categories/', include('categories.api_urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/cart/', include('cart.api_urls')),
    path('api/orders/', include('orders.api_urls')),
    path('api/payments/', include('payments.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
