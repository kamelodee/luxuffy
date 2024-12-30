from django.urls import path
from . import api_views

urlpatterns = [
    # Brand URLs
    path('brands/', api_views.brand_list, name='brand-list'),
    path('brands/create/', api_views.brand_create, name='brand-create'),
    path('brands/<slug:slug>/', api_views.brand_detail, name='brand-detail'),
    path('brands/<slug:slug>/update/', api_views.brand_update, name='brand-update'),
    path('brands/<slug:slug>/partial/', api_views.brand_partial_update, name='brand-partial-update'),
    path('brands/<slug:slug>/delete/', api_views.brand_delete, name='brand-delete'),
    
    # Product URLs
    path('', api_views.product_list, name='product-list'),
    path('<slug:slug>/', api_views.product_detail, name='product-detail'),
    
    # Product Images
    path('<slug:slug>/images/', api_views.add_product_image, name='product-add-image'),
    
    # Product Related
    path('<slug:slug>/related/', api_views.related_products, name='product-related'),
    
    # Product Reviews
    path('<slug:slug>/reviews/', api_views.product_reviews, name='product-reviews'),
    path('<slug:slug>/review/', api_views.add_product_review, name='product-add-review'),
    
    # Product Variants
    path('<slug:slug>/variants/', api_views.product_variants, name='product-variants'),
    path('<slug:slug>/variant/', api_views.product_add_variant, name='product-add-variant'),
    
    # Product Specifications
    path('<slug:slug>/specifications/', api_views.product_specifications, name='product-specifications'),
    path('<slug:slug>/specification/', api_views.product_add_specification, name='product-add-specification'),
    
    # Product Orders
    path('<slug:slug>/order/', api_views.product_order, name='product-order'),
    
    # Product Features
    path('featured/', api_views.product_featured, name='product-featured'),
    path('trending/', api_views.product_trending, name='product-trending'),
    path('search/', api_views.product_search, name='product-search'),
    
    # Product User Actions
    path('<slug:slug>/availability/', api_views.product_availability, name='product-availability'),
    path('<slug:slug>/favorite/', api_views.product_favorite, name='product-favorite'),
    path('<slug:slug>/notify/', api_views.product_notify_when_available, name='product-notify'),
    path('favorites/', api_views.product_favorites, name='product-favorites'),
    
    # Category URLs
    path('categories/all/', api_views.category_list, name='api_category_list'),
    path('categories/<slug:slug>/', api_views.category_detail, name='api_category_detail'),
    
    # Tag URLs
    path('tags/all/', api_views.tag_list, name='tag-list'),
    path('tags/<int:pk>/', api_views.tag_detail, name='tag-detail'),
]
