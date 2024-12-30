from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .api_views import CategoryViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
