from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Product URLs
    path('', views.home, name='home'),
    path('about-us', views.about, name='about'),
    path('contact-us', views.contact, name='contact'),
    path('compare', views.compare, name='compare'),
    path('coming-soon', views.coming_soon, name='coming_soon'),
    path('faq', views.faq, name='faq'),
    path('store-detail', views.store, name='store_detail'),
    path('store-list', views.stores, name='store_list'),
    path('shop', views.shop, name='shop'),
    path('blogs', views.blog, name='blogs'),
    path('become-vendor', views.become_vendor, name='become_vendor'),
    path('404', views.error, name='404'),
   
  
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)