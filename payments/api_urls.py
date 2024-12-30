from django.urls import path
from . import api_views

app_name = 'payments'

urlpatterns = [
    path('initialize/', api_views.initialize_payment, name='initialize-payment'),
    path('verify/', api_views.verify_payment, name='verify-payment'),
    path('refund/', api_views.request_refund, name='request-refund'),
]
