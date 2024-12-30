from django.urls import path
from . import api_views

app_name = 'orders'

urlpatterns = [
    path('', api_views.order_list, name='order-list'),
    path('create/', api_views.create_order, name='create-order'),
    path('<int:order_id>/', api_views.order_detail, name='order-detail'),
    path('<int:order_id>/cancel/', api_views.cancel_order, name='cancel-order'),
]
