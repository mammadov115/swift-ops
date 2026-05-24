from decimal import Decimal

from django.conf import settings

from .base import (
    ChargeResult,
    PaymentMethodResult,
    PaymentProvider,
    RefundResult,
)


class StripeProvider(PaymentProvider):
    def __init__(self):
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._stripe = stripe

    def create_payment_method(self, token: str) -> PaymentMethodResult:
        pm = self._stripe.PaymentMethod.retrieve(token)
        return PaymentMethodResult(
            provider_payment_method_id=pm.id,
            type=pm.type,
            last4=pm.card.last4,
            brand=pm.card.brand,
        )

    def charge(
        self,
        provider_payment_method_id: str,
        amount: Decimal,
        metadata: dict,
    ) -> ChargeResult:
        try:
            intent = self._stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=getattr(settings, "STRIPE_CURRENCY", "usd"),
                payment_method=provider_payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
                metadata=metadata,
            )
            succeeded = intent.status == "succeeded"
            return ChargeResult(
                provider_payment_id=intent.id,
                status="completed" if succeeded else "failed",
                failure_reason=None,
                metadata={"intent_status": intent.status},
            )
        except self._stripe.error.CardError as exc:
            return ChargeResult(
                provider_payment_id="",
                status="failed",
                failure_reason=exc.user_message,
                metadata={"code": exc.code},
            )

    def refund(
        self,
        provider_payment_id: str,
        amount: Decimal,
    ) -> RefundResult:
        refund = self._stripe.Refund.create(
            payment_intent=provider_payment_id,
            amount=int(amount * 100),
        )
        return RefundResult(
            provider_refund_id=refund.id,
            status="refunded",
        )

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        event = self._stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
        return event
