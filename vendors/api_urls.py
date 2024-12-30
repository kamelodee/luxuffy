from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import VendorViewSet

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')

urlpatterns = [
    path('', include(router.urls)),
]
