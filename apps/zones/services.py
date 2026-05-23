from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404

from .models import Zone


def list_active_zones():
    return Zone.objects.filter(is_active=True)


def get_active_zone(pk) -> Zone:
    return get_object_or_404(Zone, pk=pk, is_active=True)


def create_zone(validated_data: dict) -> Zone:
    return Zone.objects.create(**validated_data)


def update_zone(zone: Zone, validated_data: dict) -> Zone:
    for field, value in validated_data.items():
        setattr(zone, field, value)
    zone.save()
    return zone


def deactivate_zone(zone: Zone) -> None:
    """Soft-delete: preserve historical data by setting is_active=False."""
    zone.is_active = False
    zone.save(update_fields=["is_active", "updated_at"])


def get_zones_containing_point(lat: float, lng: float):
    """Return all active zones that contain the given WGS-84 coordinates (DB-level ST_Contains)."""
    point = Point(lng, lat, srid=4326)  # GEOSGeometry: x=lng, y=lat
    return Zone.objects.filter(geometry__contains=point, is_active=True)


def get_forbidden_zone_for_point(lat: float, lng: float) -> Zone | None:
    """Return the first forbidden zone containing the coordinates, or None."""
    return (
        get_zones_containing_point(lat, lng)
        .filter(zone_type=Zone.ZoneType.FORBIDDEN)
        .first()
    )
