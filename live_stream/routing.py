from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/stream/(?P<stream_id>\w+)/$', consumers.StreamConsumer.as_asgi()),
    re_path(r'ws/stream/chat/(?P<stream_id>\w+)/$', consumers.StreamChatConsumer.as_asgi()),
]
