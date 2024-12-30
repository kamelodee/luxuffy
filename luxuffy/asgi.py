"""
ASGI config for luxuffy project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luxuffy.settings')

django_asgi_app = get_asgi_application()

from chat_to_shop.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from live_stream.routing import websocket_urlpatterns as stream_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                chat_websocket_urlpatterns +
                stream_websocket_urlpatterns
            )
        )
    ),
})
