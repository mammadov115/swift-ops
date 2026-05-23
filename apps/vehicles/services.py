from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import Vehicle


def create_vehicle(validated_data: dict) -> Vehicle:
    """Persist a new vehicle with the supplied validated data."""
    return Vehicle.objects.create(**validated_data)


def get_active_vehicle(pk) -> Vehicle:
    """Return a vehicle by PK or raise 404 if not found or deactivated."""
    return get_object_or_404(Vehicle, pk=pk, is_active=True)


def update_vehicle_status(vehicle: Vehicle, new_status: str) -> Vehicle:
    """
    Attempt a status transition on the vehicle.
    Converts DjangoValidationError into a DRF ValidationError so views
    receive a clean 400 response without any extra error handling.
    """
    try:
        vehicle.transition_to(new_status)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"detail": exc.message})
    return vehicle


def deactivate_vehicle(vehicle: Vehicle) -> None:
    """Soft-delete: set is_active=False so historical data is preserved."""
    vehicle.is_active = False
    vehicle.save(update_fields=["is_active", "updated_at"])


def assign_qr_code(vehicle: Vehicle, qr_code: str) -> Vehicle:
    """
    Link a QR code to the vehicle.
    Raises ValidationError if the code is already taken by another vehicle.
    """
    conflict = (
        Vehicle.objects.filter(qr_code=qr_code).exclude(pk=vehicle.pk).exists()
    )
    if conflict:
        raise serializers.ValidationError(
            {"detail": "This QR code is already assigned to another vehicle."}
        )
    vehicle.qr_code = qr_code
    vehicle.save(update_fields=["qr_code", "updated_at"])
    return vehicle
