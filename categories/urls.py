from django.urls import path
from . import views, api_views

urlpatterns = [
    # HTML Views
    path('', views.category_list, name='category_list'),
    path('<int:pk>/', views.category_detail, name='category_detail'),
    path('create/', views.category_create, name='category_create'),
    path('<int:pk>/update/', views.category_update, name='category_update'),
    path('<int:pk>/delete/', views.category_delete, name='category_delete'),

    # API Views
    path('api/categories/', api_views.category_list_api, name='category_list_api'),
    path('api/categories/<int:pk>/', api_views.category_detail_api, name='category_detail_api'),
]
