from .general import env

# PAYMENT PROVIDER
# ------------------------------------------------------------------------------
# Set PAYMENT_PROVIDER=stripe in production environment variables.
# Use the default "mock" provider for local development and tests.
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="mock")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_CURRENCY = env("STRIPE_CURRENCY", default="usd")
