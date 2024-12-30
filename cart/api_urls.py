from django.urls import path
from . import api_views

app_name = 'cart'

urlpatterns = [
    # Cart operations
    path('', api_views.cart_detail, name='cart-detail'),
    path('add/', api_views.add_to_cart, name='add-to-cart'),
    path('items/<int:item_id>/', api_views.update_cart_item, name='update-cart-item'),
    path('items/<int:item_id>/remove/', api_views.remove_from_cart, name='remove-from-cart'),
    path('clear/', api_views.clear_cart, name='clear-cart'),
    path('move-to-wishlist/', api_views.move_all_to_wishlist, name='move-to-wishlist'),
]
