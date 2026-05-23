"""
Zone utility helpers intended for use in the ride completion flow.

Usage example::

    from apps.zones.utils import validate_parking_allowed

    def complete_ride(ride, lat, lng):
        validate_parking_allowed(lat, lng)   # raises 400 if forbidden
        ride.end(lat, lng)
"""
from decimal import Decimal

from rest_framework import serializers

from .services import get_forbidden_zone_for_point


def validate_parking_allowed(lat: float | Decimal, lng: float | Decimal) -> None:
    """
    Raise a DRF ValidationError if the coordinates fall inside a forbidden zone.

    Call this at the start of the ride-completion handler. The error message
    includes the zone name and ID so the client can surface a meaningful
    warning to the driver.
    """
    zone = get_forbidden_zone_for_point(float(lat), float(lng))
    if zone is not None:
        raise serializers.ValidationError(
            {
                "detail": f"Cannot end ride in forbidden zone '{zone.name}'.",
                "zone": {"id": str(zone.id), "name": zone.name, "type": zone.zone_type},
            }
        )
