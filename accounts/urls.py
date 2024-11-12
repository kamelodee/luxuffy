from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Product URLs
    path('wishlist', views.wishlist, name='wishlist'),
    path('my-account', views.my_acount, name='my_account'),
    path('login', views.login, name='login'),
    path('order', views.order, name='order'),
    path('cart', views.cart, name='cart'),
    path('checkout', views.checkout, name='checkout'),
    
   
  
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)