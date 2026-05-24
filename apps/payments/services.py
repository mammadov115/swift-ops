from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .fare import calculate_fare
from .models import Payment, PaymentMethod, PromoCode
from .providers import get_provider


# ─────────────────────────────────────────────────────────────────────────────
# Payment Methods
# ─────────────────────────────────────────────────────────────────────────────


def list_payment_methods(user):
    return PaymentMethod.objects.filter(user=user, is_active=True)


def add_payment_method(user, token: str) -> PaymentMethod:
    """
    Tokenise a new payment method via the provider and store it.
    No raw card data is ever handled here (PCI-compliant).
    """
    provider = get_provider()
    result = provider.create_payment_method(token)

    with transaction.atomic():
        is_first = not PaymentMethod.objects.filter(
            user=user, is_active=True
        ).exists()
        method = PaymentMethod.objects.create(
            user=user,
            provider=_provider_label(provider),
            provider_payment_method_id=result.provider_payment_method_id,
            type=result.type,
            last4=result.last4,
            brand=result.brand,
            is_default=is_first,
        )
    return method


def set_default_payment_method(user, payment_method_id) -> PaymentMethod:
    with transaction.atomic():
        PaymentMethod.objects.filter(user=user).update(is_default=False)
        try:
            method = PaymentMethod.objects.select_for_update().get(
                pk=payment_method_id, user=user, is_active=True
            )
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": "Payment method not found."}
            )
        method.is_default = True
        method.save(update_fields=["is_default", "updated_at"])
    return method


def remove_payment_method(user, payment_method_id) -> None:
    try:
        method = PaymentMethod.objects.get(
            pk=payment_method_id, user=user, is_active=True
        )
    except PaymentMethod.DoesNotExist:
        raise serializers.ValidationError(
            {"detail": "Payment method not found."}
        )
    method.is_active = False
    method.save(update_fields=["is_active", "updated_at"])


def _get_default_payment_method(user, payment_method_id=None):
    qs = PaymentMethod.objects.filter(user=user, is_active=True)
    if payment_method_id:
        return qs.filter(pk=payment_method_id).first()
    return qs.filter(is_default=True).first()


# ─────────────────────────────────────────────────────────────────────────────
# Promo Codes
# ─────────────────────────────────────────────────────────────────────────────


def validate_promo_code(code: str, user) -> PromoCode:
    """
    Validate a promo code for the given user without consuming it.
    Raises serializers.ValidationError on any violation.
    """
    try:
        promo = PromoCode.objects.get(code__iexact=code, is_active=True)
    except PromoCode.DoesNotExist:
        raise serializers.ValidationError(
            {"promo_code": "Invalid or inactive promo code."}
        )

    now = timezone.now()
    if promo.valid_from > now:
        raise serializers.ValidationError(
            {"promo_code": "Promo code is not yet valid."}
        )
    if promo.valid_until and promo.valid_until < now:
        raise serializers.ValidationError(
            {"promo_code": "Promo code has expired."}
        )
    if promo.max_uses is not None and promo.uses_count >= promo.max_uses:
        raise serializers.ValidationError(
            {"promo_code": "Promo code usage limit reached."}
        )
    if promo.used_by.filter(pk=user.pk).exists():
        raise serializers.ValidationError(
            {"promo_code": "You have already used this promo code."}
        )
    return promo


# ─────────────────────────────────────────────────────────────────────────────
# Payments
# ─────────────────────────────────────────────────────────────────────────────


def get_payment_history(user):
    return Payment.objects.filter(user=user).select_related(
        "ride", "payment_method", "promo_code"
    )


def charge_for_ride(
    ride,
    user,
    payment_method_id=None,
    promo_code_str: str = None,
) -> Payment:
    """
    Create a Payment for a completed ride and immediately attempt to charge.

    If the charge fails (no payment method, or provider error) the Payment is
    persisted with status=failed so the driver can retry later. The ride record
    is never rolled back — it is already completed and the vehicle released.
    """
    if hasattr(ride, "payment"):
        raise serializers.ValidationError(
            {"detail": "A payment already exists for this ride."}
        )

    promo = None
    if promo_code_str:
        promo = validate_promo_code(promo_code_str, user)

    fare = calculate_fare(ride.distance_km, ride.duration_seconds, promo)
    pm = _get_default_payment_method(user, payment_method_id)
    provider = get_provider()

    with transaction.atomic():
        payment = Payment.objects.create(
            ride=ride,
            user=user,
            payment_method=pm,
            promo_code=promo,
            status=Payment.Status.PENDING,
            amount=fare.total,
            discount_amount=fare.discount_amount,
            provider=_provider_label(provider),
        )

        if pm is None:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = "No payment method on file."
            payment.save(
                update_fields=["status", "failure_reason", "updated_at"]
            )
            return payment

        result = provider.charge(
            provider_payment_method_id=pm.provider_payment_method_id,
            amount=fare.total,
            metadata={
                "ride_id": str(ride.id),
                "user_id": str(user.id),
                "payment_id": str(payment.id),
            },
        )

        payment.status = (
            Payment.Status.COMPLETED
            if result.status == "completed"
            else Payment.Status.FAILED
        )
        payment.provider_payment_id = result.provider_payment_id
        payment.provider_metadata = result.metadata
        payment.failure_reason = result.failure_reason or ""
        payment.save(
            update_fields=[
                "status",
                "provider_payment_id",
                "provider_metadata",
                "failure_reason",
                "updated_at",
            ]
        )

        if payment.status == Payment.Status.COMPLETED and promo:
            _consume_promo(promo, user)

    return payment


def retry_payment(payment_id, user, payment_method_id=None) -> Payment:
    """
    Retry a previously failed payment, optionally with a different payment
    method. Promo code already attached to the payment record is reused.
    """
    try:
        payment = Payment.objects.select_related(
            "ride", "promo_code"
        ).get(pk=payment_id, user=user)
    except Payment.DoesNotExist:
        raise serializers.ValidationError({"detail": "Payment not found."})

    if payment.status != Payment.Status.FAILED:
        raise serializers.ValidationError(
            {"detail": "Only failed payments can be retried."}
        )

    pm = _get_default_payment_method(user, payment_method_id)
    if pm is None:
        raise serializers.ValidationError(
            {"detail": "No valid payment method found."}
        )

    provider = get_provider()

    with transaction.atomic():
        result = provider.charge(
            provider_payment_method_id=pm.provider_payment_method_id,
            amount=payment.amount,
            metadata={
                "ride_id": str(payment.ride_id),
                "user_id": str(user.id),
                "payment_id": str(payment.id),
                "retry": "true",
            },
        )

        payment.payment_method = pm
        payment.status = (
            Payment.Status.COMPLETED
            if result.status == "completed"
            else Payment.Status.FAILED
        )
        payment.provider_payment_id = result.provider_payment_id
        payment.provider_metadata = result.metadata
        payment.failure_reason = result.failure_reason or ""
        payment.save(
            update_fields=[
                "payment_method",
                "status",
                "provider_payment_id",
                "provider_metadata",
                "failure_reason",
                "updated_at",
            ]
        )

        if payment.status == Payment.Status.COMPLETED and payment.promo_code:
            _consume_promo(payment.promo_code, user)

    return payment


# ─────────────────────────────────────────────────────────────────────────────
# Webhooks
# ─────────────────────────────────────────────────────────────────────────────


def process_stripe_webhook(event: dict) -> None:
    """
    Update local Payment records based on incoming Stripe webhook events.
    Idempotent — safe to call multiple times for the same event.
    """
    event_type = event.get("type", "")
    obj = event.get("data", {}).get("object", {})
    payment_id = (obj.get("metadata") or {}).get("payment_id")

    if event_type == "payment_intent.succeeded" and payment_id:
        Payment.objects.filter(pk=payment_id, status=Payment.Status.PENDING).update(
            status=Payment.Status.COMPLETED,
            provider_payment_id=obj.get("id", ""),
        )

    elif event_type == "payment_intent.payment_failed" and payment_id:
        failure = (obj.get("last_payment_error") or {})
        Payment.objects.filter(pk=payment_id).update(
            status=Payment.Status.FAILED,
            provider_payment_id=obj.get("id", ""),
            failure_reason=failure.get("message", "Payment failed"),
        )

    elif event_type == "charge.refunded":
        intent_id = obj.get("payment_intent", "")
        if intent_id:
            Payment.objects.filter(
                provider_payment_id=intent_id,
                status=Payment.Status.COMPLETED,
            ).update(status=Payment.Status.REFUNDED)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _provider_label(provider) -> str:
    return type(provider).__name__.lower().replace("provider", "")


def _consume_promo(promo: PromoCode, user) -> None:
    promo.used_by.add(user)
    PromoCode.objects.filter(pk=promo.pk).update(
        uses_count=promo.uses_count + 1
    )
