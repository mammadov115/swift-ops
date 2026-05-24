from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class PaymentMethodResult:
    provider_payment_method_id: str
    type: str
    last4: str
    brand: str


@dataclass
class ChargeResult:
    provider_payment_id: str
    status: str  # "completed" | "failed"
    failure_reason: Optional[str]
    metadata: dict = field(default_factory=dict)


@dataclass
class RefundResult:
    provider_refund_id: str
    status: str


class PaymentProvider(ABC):
    @abstractmethod
    def create_payment_method(self, token: str) -> PaymentMethodResult: ...

    @abstractmethod
    def charge(
        self,
        provider_payment_method_id: str,
        amount: Decimal,
        metadata: dict,
    ) -> ChargeResult: ...

    @abstractmethod
    def refund(
        self,
        provider_payment_id: str,
        amount: Decimal,
    ) -> RefundResult: ...

    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> dict: ...
