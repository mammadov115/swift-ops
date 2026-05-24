from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from apps.vehicles.models import Vehicle

from .models import Ride
from .utils import calculate_distance, calculate_payment


def start_ride(
    driver,
    vehicle_id: str,
    start_lat: Decimal,
    start_lng: Decimal,
) -> Ride:
    """
    Atomically start a ride.

    Acquires a row-level lock on the vehicle so that two concurrent requests
    for the same vehicle cannot both succeed. Raises a DRF ValidationError on
    any constraint violation so the view returns a clean 400 response.
    """
    with transaction.atomic():
        try:
            vehicle = Vehicle.objects.select_for_update().get(
                pk=vehicle_id, is_active=True
            )
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(
                {"vehicle": "Vehicle not found or deactivated."}
            )

        if vehicle.status != Vehicle.Status.AVAILABLE:
            raise serializers.ValidationError(
                {"vehicle": "Vehicle is not available for rental."}
            )

        if Ride.objects.filter(
            driver=driver, status=Ride.Status.ACTIVE
        ).exists():
            raise serializers.ValidationError(
                {"detail": "You already have an active ride."}
            )

        try:
            vehicle.transition_to(Vehicle.Status.RENTED)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"vehicle": exc.message})

        ride = Ride.objects.create(
            driver=driver,
            vehicle=vehicle,
            start_latitude=start_lat,
            start_longitude=start_lng,
        )
        return Ride.objects.select_related("vehicle", "driver").get(pk=ride.pk)


def end_ride(ride: Ride, end_lat: Decimal, end_lng: Decimal) -> Ride:
    """
    Complete a ride inside a single transaction.

    Steps (in order):
      1. Record end time and coordinates.
      2. Calculate duration.
      3. Calculate distance (Haversine via geopy).
      4. Calculate payment amount.
      5. Persist ride fields.
      6. Update vehicle location and return it to available.
    """
    if ride.status != Ride.Status.ACTIVE:
        raise serializers.ValidationError(
            {"detail": "Only active rides can be ended."}
        )

    with transaction.atomic():
        now = timezone.now()
        duration_seconds = int((now - ride.started_at).total_seconds())
        distance_km = calculate_distance(
            ride.start_latitude, ride.start_longitude, end_lat, end_lng
        )
        payment_amount = calculate_payment(distance_km, duration_seconds)

        ride.ended_at = now
        ride.end_latitude = end_lat
        ride.end_longitude = end_lng
        ride.status = Ride.Status.COMPLETED
        ride.duration_seconds = duration_seconds
        ride.distance_km = distance_km
        ride.payment_amount = payment_amount
        ride.save(
            update_fields=[
                "ended_at",
                "end_latitude",
                "end_longitude",
                "status",
                "duration_seconds",
                "distance_km",
                "payment_amount",
                "updated_at",
            ]
        )

        vehicle = ride.vehicle
        vehicle.latitude = end_lat
        vehicle.longitude = end_lng
        vehicle.save(update_fields=["latitude", "longitude", "updated_at"])

        try:
            vehicle.transition_to(Vehicle.Status.AVAILABLE)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"vehicle": exc.message})

    return Ride.objects.select_related("vehicle", "driver").get(pk=ride.pk)


def get_active_ride(driver) -> Ride:
    """Return the driver's current active ride or raise 404."""
    return get_object_or_404(
        Ride.objects.select_related("vehicle", "driver"),
        driver=driver,
        status=Ride.Status.ACTIVE,
    )


def get_ride(driver, pk) -> Ride:
    """Return a specific ride owned by the driver or raise 404."""
    return get_object_or_404(
        Ride.objects.select_related("vehicle"),
        pk=pk,
        driver=driver,
    )


def list_ride_history(driver):
    """Return completed and cancelled rides for the driver, newest first."""
    return Ride.objects.filter(
        driver=driver,
        status__in=[Ride.Status.COMPLETED, Ride.Status.CANCELLED],
    ).select_related("vehicle", "driver")
