"""
JWT WebSocket authentication middleware.

Reads a ``token`` query-string parameter, validates it with SimpleJWT,
and populates ``scope["user"]`` so that consumers can rely on a real
Django user object instead of ``AnonymousUser``.

Usage in asgi.py::

    from config.ws_auth import JWTAuthMiddlewareStack
    _ws_app = JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user(token_key: str):
    """Return the User for *token_key*, or AnonymousUser on any failure."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        token = AccessToken(token_key)
        return User.objects.get(pk=token["user_id"])
    except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Populate ``scope["user"]`` from a ``?token=<access_token>`` query param."""

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            query_string = scope.get("query_string", b"").decode()
            params = parse_qs(query_string)
            token_list = params.get("token", [])
            if token_list:
                scope["user"] = await _get_user(token_list[0])
            else:
                scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """Convenience wrapper — drop-in replacement for AuthMiddlewareStack."""
    return JWTAuthMiddleware(inner)
