from django.conf import settings

from .base import PushProvider


def get_push_provider() -> PushProvider:
    """Return the configured push provider instance."""
    provider_name = getattr(settings, "PUSH_PROVIDER", "mock")
    if provider_name == "fcm":
        from .fcm import FCMProvider

        return FCMProvider()
    from .mock import MockPushProvider

    return MockPushProvider()
