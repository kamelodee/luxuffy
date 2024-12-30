from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Vendor Management URLs
    path('', views.dashboard, name='dashboard'),
    path('create/', views.vendor_create, name='vendor_create'),
    path('settings/', views.vendor_settings, name='vendor_settings'),
    path('store/<str:store_name>/', views.vendor_store, name='vendor_store'),
    path('<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('<int:pk>/update/', views.vendor_update, name='vendor_update'),
    path('<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),

    # Product Management URLs
    path('products/', views.ProductListView.as_view(), name='vendor_products'),
    path('products/create/', views.InitiateProductCreation.as_view(), name='vendor_product_create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='vendor_product_detail'),
    path('products/<slug:slug>/edit/', views.ProductCreateView.as_view(), name='vendor_product_edit'),
    path('products/<slug:slug>/update/', views.ProductUpdateView.as_view(), name='vendor_product_update'),
    path('products/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='vendor_product_delete'),
    path('products/<slug:slug>/cancel/', views.CancelProductCreation.as_view(), name='cancel_product_creation'),

    # Product Images URLs
    path('products/<slug:product_slug>/images/create/', views.ProductImageCreateView.as_view(), name='product_image_create'),
    path('products/<slug:product_slug>/images/<int:pk>/delete/', views.ProductImageDeleteView.as_view(), name='product_image_delete'),
    path('products/<slug:slug>/images/upload/', views.ProductImageUploadView.as_view(), name='product_image_upload'),
    path('products/<slug:slug>/images/', views.ProductImagesView.as_view(), name='product_images'),
    path('products/images/<int:image_id>/set-primary/', views.SetPrimaryImageView.as_view(), name='set_primary_image'),
    path('products/images/<int:image_id>/delete/', views.DeleteProductImageView.as_view(), name='delete_product_image'),

    # Product Variants URLs
    path('products/<slug:product_slug>/variants/create/', views.ProductVariantCreateView.as_view(), name='product_variant_create'),
    path('products/<slug:product_slug>/variants/<int:pk>/edit/', views.ProductVariantEditView.as_view(), name='product_variant_edit'),
    path('products/<slug:product_slug>/variants/<int:pk>/delete/', views.ProductVariantDeleteView.as_view(), name='product_variant_delete'),

    # Product Specifications URLs
    path('products/<slug:product_slug>/specifications/create/', views.ProductSpecificationCreateView.as_view(), name='product_specification_create'),
    path('products/<slug:product_slug>/specifications/<int:pk>/edit/', views.ProductSpecificationEditView.as_view(), name='product_specification_edit'),
    path('products/<slug:product_slug>/specifications/<int:pk>/delete/', views.ProductSpecificationDeleteView.as_view(), name='product_specification_delete'),

    # Ajax URLs
    path('products/load-variants/', views.LoadVariantsView.as_view(), name='load_variants'),
    path('products/add-variant/', views.AddVariantView.as_view(), name='add_variant'),
    path('products/delete-variant/', views.DeleteVariantView.as_view(), name='delete_variant'),
    path('products/toggle-variants/', views.ToggleVariantSectionView.as_view(), name='toggle_variants'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
