from django.urls import path
from .views import chat_room, video_shop_view, vendor_dashboard

app_name = 'chat_to_shop'

urlpatterns = [
    path('room/', chat_room, name='chat'),
    # path('room/<str:room_name>/', chat_room, name='chat_room'),
    path('video/', video_shop_view, name='video_shop'),
    path('vendor/dashboard/', vendor_dashboard, name='vendor_dashboard'),
]
