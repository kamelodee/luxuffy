from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'products'

urlpatterns = [
    # API URLs - note: no leading slash here
   
    
    # Product URLs
    path('', views.detail, name='product_list'),  # List all products
    path('create/', views.product_create, name='product_create'),
    path('update/<slug:slug>/', views.product_update, name='product_update'),
    path('upload-product-image/<int:product_id>/', views.upload_product_image, name='upload_product_image'),
    path('<slug:slug>/', views.detail, name='product_detail'),  # View single product
    path('delete/<slug:slug>/', views.delete, name='product_delete'),
    path('compare/', views.compare, name='product_compare'),
    path('wishlist/', views.wishlist, name='product_wishlist'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)