from django.conf import settings

from .base import PaymentProvider


def get_provider() -> PaymentProvider:
    """Return the configured payment provider instance."""
    provider_name = getattr(settings, "PAYMENT_PROVIDER", "mock")
    if provider_name == "stripe":
        from .stripe_provider import StripeProvider

        return StripeProvider()
    from .mock import MockProvider

    return MockProvider()
