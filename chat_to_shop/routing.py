from django.urls import re_path
from .consumers.chat import ChatConsumer
from .consumers.video_shop import VideoShopConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/room/(?P<room_name>\w+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/video_shop/$', VideoShopConsumer.as_asgi()),
]
