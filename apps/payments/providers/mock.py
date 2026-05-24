import json
import uuid
from decimal import Decimal

from .base import (
    ChargeResult,
    PaymentMethodResult,
    PaymentProvider,
    RefundResult,
)


class MockProvider(PaymentProvider):
    """Fake provider for local development and tests. Always succeeds."""

    def create_payment_method(self, token: str) -> PaymentMethodResult:
        last4 = token[-4:] if len(token) >= 4 else "4242"
        return PaymentMethodResult(
            provider_payment_method_id=f"mock_pm_{token}",
            type="card",
            last4=last4,
            brand="visa",
        )

    def charge(
        self,
        provider_payment_method_id: str,
        amount: Decimal,
        metadata: dict,
    ) -> ChargeResult:
        return ChargeResult(
            provider_payment_id=f"mock_ch_{uuid.uuid4().hex[:12]}",
            status="completed",
            failure_reason=None,
            metadata=metadata,
        )

    def refund(
        self,
        provider_payment_id: str,
        amount: Decimal,
    ) -> RefundResult:
        return RefundResult(
            provider_refund_id=f"mock_re_{uuid.uuid4().hex[:12]}",
            status="refunded",
        )

    def verify_webhook(self, payload: bytes, signature: str) -> dict:
        return json.loads(payload)
