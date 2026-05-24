from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

# Pricing constants (single source of truth for fare calculation)
BASE_FEE = Decimal("0.50")
RATE_PER_KM = Decimal("0.50")
RATE_PER_MINUTE = Decimal("0.10")

if TYPE_CHECKING:
    from .models import PromoCode


@dataclass
class FareBreakdown:
    base_fee: Decimal
    distance_cost: Decimal
    duration_cost: Decimal
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str = "AZN"


def calculate_fare(
    distance_km: Decimal,
    duration_seconds: int,
    promo_code: Optional["PromoCode"] = None,
) -> FareBreakdown:
    minutes = Decimal(duration_seconds) / Decimal("60")
    base_fee = BASE_FEE
    distance_cost = (distance_km * RATE_PER_KM).quantize(Decimal("0.01"))
    duration_cost = (minutes * RATE_PER_MINUTE).quantize(Decimal("0.01"))
    subtotal = (base_fee + distance_cost + duration_cost).quantize(
        Decimal("0.01")
    )

    discount = Decimal("0.00")
    if promo_code is not None:
        if promo_code.discount_type == "percentage":
            discount = (
                subtotal * promo_code.discount_value / Decimal("100")
            ).quantize(Decimal("0.01"))
        else:  # fixed
            discount = min(promo_code.discount_value, subtotal)

    total = max(
        (subtotal - discount).quantize(Decimal("0.01")),
        Decimal("0.01"),  # minimum charge
    )

    return FareBreakdown(
        base_fee=base_fee,
        distance_cost=distance_cost,
        duration_cost=duration_cost,
        subtotal=subtotal,
        discount_amount=discount,
        total=total,
    )
