"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

Django Channels wraps the standard ASGI app so that both HTTP and WebSocket
connections are dispatched from a single entry point.

HTTP  →  Django ASGI application (normal request/response)
WS    →  JWTAuthMiddlewareStack  →  URLRouter  →  Consumers
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Must be called before any models are imported.
django_asgi_app = get_asgi_application()

from apps.notifications.routing import websocket_urlpatterns as notifications_ws  # noqa: E402
from apps.tracking.routing import websocket_urlpatterns as tracking_ws  # noqa: E402
from config.ws_auth import JWTAuthMiddlewareStack  # noqa: E402

websocket_urlpatterns = tracking_ws + notifications_ws
_ws_app = JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns))

# AllowedHostsOriginValidator rejects CLI WebSocket clients (e.g. wscat) that
# don't send an Origin header — skip it in development.
if not settings.DEBUG:
    _ws_app = AllowedHostsOriginValidator(_ws_app)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": _ws_app,
    }
)
