from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from .serializers import (
    ChargeRideSerializer,
    CreatePaymentMethodSerializer,
    FareBreakdownSerializer,
    PaymentMethodSerializer,
    PaymentSerializer,
    RetryPaymentSerializer,
    ValidatePromoSerializer,
)

# ── Payment Methods ────────────────────────────────────────────────────────────

payment_method_list_schema = extend_schema(
    summary="List payment methods",
    description="Returns all active payment methods for the authenticated driver.",
    responses={200: PaymentMethodSerializer(many=True)},
    tags=["Payments"],
)

payment_method_create_schema = extend_schema(
    summary="Add a payment method",
    description=(
        "Tokenises a new payment method via the configured provider "
        "(Stripe or Mock) and stores it. No raw card data is ever handled — "
        "pass the provider-issued token (e.g. `pm_xxx` from Stripe.js). "
        "The first method added is automatically set as the default."
    ),
    request=CreatePaymentMethodSerializer,
    responses={
        201: PaymentMethodSerializer,
        400: OpenApiResponse(description="Validation error"),
    },
    tags=["Payments"],
)

payment_method_delete_schema = extend_schema(
    summary="Remove a payment method",
    description="Soft-deletes the specified payment method.",
    responses={
        204: OpenApiResponse(description="Deleted"),
        404: OpenApiResponse(description="Payment method not found"),
    },
    tags=["Payments"],
)

payment_method_set_default_schema = extend_schema(
    summary="Set default payment method",
    description="Marks the specified method as the default for this driver.",
    responses={
        200: PaymentMethodSerializer,
        404: OpenApiResponse(description="Payment method not found"),
    },
    tags=["Payments"],
)

# ── Payments ──────────────────────────────────────────────────────────────────

payment_list_schema = extend_schema(
    summary="Payment history",
    description="Returns a paginated list of payments for the authenticated driver.",
    parameters=[
        OpenApiParameter(name="page", required=False, type=int),
        OpenApiParameter(name="page_size", required=False, type=int),
    ],
    responses={200: PaymentSerializer(many=True)},
    tags=["Payments"],
)

payment_charge_schema = extend_schema(
    summary="Charge for a ride",
    description=(
        "Creates and immediately executes a payment for the specified completed ride. "
        "Uses the driver's default payment method unless `payment_method_id` is supplied. "
        "An optional `promo_code` is validated and applied atomically. "
        "If the charge fails the payment is stored with `status=failed` so it "
        "can be retried later — the ride record is never rolled back."
    ),
    request=ChargeRideSerializer,
    responses={
        201: PaymentSerializer,
        400: OpenApiResponse(description="Validation error"),
    },
    tags=["Payments"],
)

payment_retry_schema = extend_schema(
    summary="Retry a failed payment",
    description=(
        "Retries a payment that previously failed. "
        "Optionally supply a different `payment_method_id`. "
        "Only payments with `status=failed` can be retried."
    ),
    request=RetryPaymentSerializer,
    responses={
        200: PaymentSerializer,
        400: OpenApiResponse(description="Not a failed payment"),
        404: OpenApiResponse(description="Payment not found"),
    },
    tags=["Payments"],
)

# ── Promo Codes ────────────────────────────────────────────────────────────────

promo_validate_schema = extend_schema(
    summary="Validate a promo code",
    description=(
        "Checks whether a promo code is valid for the authenticated driver. "
        "Optionally accepts `distance_km` and `duration_seconds` to return a "
        "full fare preview including the discount."
    ),
    request=ValidatePromoSerializer,
    responses={
        200: OpenApiResponse(description="Promo code valid, fare preview included"),
        400: OpenApiResponse(description="Invalid or expired promo code"),
    },
    tags=["Payments"],
)

# ── Webhook ────────────────────────────────────────────────────────────────────

webhook_stripe_schema = extend_schema(
    summary="Stripe webhook receiver",
    description=(
        "Receives Stripe webhook events and updates local payment records. "
        "The `Stripe-Signature` header is validated using the webhook secret. "
        "Returns 200 for all successfully processed events."
    ),
    responses={
        200: OpenApiResponse(description="Event processed"),
        400: OpenApiResponse(description="Invalid signature or payload"),
    },
    tags=["Payments"],
    auth=[],
)
