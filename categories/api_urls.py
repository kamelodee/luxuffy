from django.urls import path, include
from .api_views import (
    list_categories,
    category_detail,
    get_subcategories,
    get_products,
    get_hierarchy,
    get_category_tree
)

urlpatterns = [
    path('categories/', list_categories, name='list_categories'),
    path('categories/<slug:slug>/', category_detail, name='category_detail'),
    path('categories/<slug:slug>/subcategories/', get_subcategories, name='get_subcategories'),
    path('categories/<slug:slug>/products/', get_products, name='get_products'),
    path('categories/<slug:slug>/hierarchy/', get_hierarchy, name='get_hierarchy'),
    path('categories/tree/', get_category_tree, name='get_category_tree'),
]
