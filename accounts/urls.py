from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Basic auth URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.request_password_reset, name='password_reset'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # Account management URLs
    path('my-account/', views.profile_settings_api, name='my_account'),
    path('my-account/profile/', views.profile_settings_api, name='profile'),
    path('my-account/orders/', views.order_history_api, name='order_history'),
    path('my-account/addresses/', views.manage_addresses_api, name='address_book'),
    path('my-account/change-password/', views.change_password_api, name='change_password'),
    path('my-account/notifications/', views.notifications_api, name='notifications'),
    
    # Shopping URLs
    path('wishlist/', views.wishlist_api, name='wishlist'),
    path('order/', views.order_detail_api, name='order'),
    
    # Utility URLs
    path('send_mail/', views.send_maila, name='send_mail'),
    
    # API URLs
    path('api/auth/', include([
        path('register', views.api_register, name='api_register'),
        path('login', views.api_login, name='api_login'),
        path('logout', views.api_logout, name='api_logout'),
        path('google', views.google_login_api, name='google_login_api'),
        path('password-reset', views.api_request_password_reset, name='api_password_reset'),
    ])),
    
    # Profile API URLs
    path('api/profile/', include([
        # Profile management
        path('', views.profile_settings_api, name='api_profile_settings'),
        path('change-password', views.change_password_api, name='api_change_password'),
        
        # Address management
        path('addresses', views.manage_addresses_api, name='api_addresses'),
        path('addresses/<int:address_id>', views.manage_address_api, name='api_address_detail'),
        path('addresses/<int:address_id>/delete', views.manage_address_api, name='api_address_delete'),
        
        # Order management
        path('orders', views.order_history_api, name='api_orders'),
        path('orders/<int:order_id>', views.order_detail_api, name='api_order_detail'),
        
        # Wishlist management
        path('wishlist', views.wishlist_api, name='api_wishlist'),
        path('wishlist/<str:product_id>', views.wishlist_item_api, name='api_wishlist_item'),
        
        # Notification management
        path('/notifications', views.notifications_api, name='api_notifications'),
        path('/notifications/settings', views.notification_settings_api, name='api_notification_settings'),
        
        # Email verification
        path('/verify-email', views.verify_email, name='api_email_verification'),
    ])),
    
    # OAuth URLs
    path('auth/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)