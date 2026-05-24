from django.urls import path

from .views import PaymentMethodViewSet, PaymentViewSet, PromoCodeViewSet

_pm = PaymentMethodViewSet.as_view
_pay = PaymentViewSet.as_view
_promo = PromoCodeViewSet.as_view

urlpatterns = [
    # Payment methods
    path(
        "methods/",
        _pm({"get": "list", "post": "create"}),
        name="payment-method-list",
    ),
    path(
        "methods/<uuid:pk>/",
        _pm({"delete": "destroy"}),
        name="payment-method-detail",
    ),
    path(
        "methods/<uuid:pk>/set-default/",
        _pm({"post": "set_default"}),
        name="payment-method-set-default",
    ),
    # Payments
    path(
        "",
        _pay({"get": "list"}),
        name="payment-list",
    ),
    path(
        "charge/",
        _pay({"post": "charge"}),
        name="payment-charge",
    ),
    path(
        "<uuid:pk>/retry/",
        _pay({"post": "retry"}),
        name="payment-retry",
    ),
    path(
        "webhook/stripe/",
        _pay({"post": "webhook_stripe"}),
        name="payment-webhook-stripe",
    ),
    # Promo codes
    path(
        "promo/validate/",
        _promo({"post": "validate"}),
        name="promo-validate",
    ),
]
