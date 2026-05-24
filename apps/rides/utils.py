from decimal import Decimal

from geopy.distance import distance as geo_distance

# ─── Pricing constants ────────────────────────────────────────────────────────
BASE_FEE: Decimal = Decimal("0.50")       # fixed charge per ride
RATE_PER_KM: Decimal = Decimal("0.50")   # per kilometre
RATE_PER_MINUTE: Decimal = Decimal("0.10")  # per minute


def calculate_distance(
    start_lat: Decimal,
    start_lng: Decimal,
    end_lat: Decimal,
    end_lng: Decimal,
) -> Decimal:
    """Return the geodesic distance in km between two GPS coordinates."""
    km = geo_distance(
        (float(start_lat), float(start_lng)),
        (float(end_lat), float(end_lng)),
    ).km
    return Decimal(str(round(km, 3)))


def calculate_payment(distance_km: Decimal, duration_seconds: int) -> Decimal:
    """
    Calculate ride payment.

    Formula: base_fee + (distance_km × rate_per_km) + (minutes × rate_per_minute)
    """
    minutes = Decimal(duration_seconds) / Decimal("60")
    amount = (
        BASE_FEE
        + (distance_km * RATE_PER_KM)
        + (minutes * RATE_PER_MINUTE)
    )
    return amount.quantize(Decimal("0.01"))
