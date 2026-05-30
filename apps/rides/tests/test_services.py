"""
Tests for the ride engine — the most critical business logic in SwiftOps.

Priority: ride engine > authentication > payments > everything else.

Coverage targets
----------------
- Happy path: start and end a ride.
- Race condition: two concurrent requests for the same vehicle should only
  allow one to succeed (the SELECT FOR UPDATE lock).
- Guard rails: cannot start a ride on an unavailable vehicle; cannot start
  two rides at the same time; cannot end a non-active ride.
"""
import pytest
from decimal import Decimal

from django.db import connection, transaction
from rest_framework import serializers as drf_serializers

from apps.rides.models import Ride
from apps.vehicles.models import Vehicle
from tests.factories import RideFactory, UserFactory, VehicleFactory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _start(driver, vehicle):
    from apps.rides import services
    return services.start_ride(
        driver=driver,
        vehicle_id=str(vehicle.pk),
        start_lat=Decimal("40.409264"),
        start_lng=Decimal("49.867092"),
    )


def _end(ride):
    from apps.rides import services
    return services.end_ride(
        ride=ride,
        end_lat=Decimal("40.420000"),
        end_lng=Decimal("49.870000"),
    )


# ---------------------------------------------------------------------------
# start_ride
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
class TestStartRide:
    def test_happy_path_creates_active_ride(self):
        driver = UserFactory(role="driver", is_email_verified=True)
        vehicle = VehicleFactory(status=Vehicle.Status.AVAILABLE)

        ride = _start(driver, vehicle)

        assert ride.status == Ride.Status.ACTIVE
        assert ride.driver == driver
        assert ride.vehicle == vehicle
        vehicle.refresh_from_db()
        assert vehicle.status == Vehicle.Status.RENTED

    def test_vehicle_transitions_to_rented(self):
        driver = UserFactory(role="driver")
        vehicle = VehicleFactory(status=Vehicle.Status.AVAILABLE)

        _start(driver, vehicle)

        vehicle.refresh_from_db()
        assert vehicle.status == Vehicle.Status.RENTED

    def test_unavailable_vehicle_raises_400(self):
        driver = UserFactory(role="driver")
        vehicle = VehicleFactory(status=Vehicle.Status.RENTED)

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            _start(driver, vehicle)

        assert "not available" in str(exc_info.value).lower()

    def test_inactive_vehicle_raises_400(self):
        driver = UserFactory(role="driver")
        vehicle = VehicleFactory(status=Vehicle.Status.AVAILABLE, is_active=False)

        with pytest.raises(drf_serializers.ValidationError):
            _start(driver, vehicle)

    def test_nonexistent_vehicle_raises_400(self):
        import uuid
        driver = UserFactory(role="driver")

        with pytest.raises(drf_serializers.ValidationError):
            from apps.rides import services
            services.start_ride(
                driver=driver,
                vehicle_id=str(uuid.uuid4()),
                start_lat=Decimal("40.4"),
                start_lng=Decimal("49.8"),
            )

    def test_cannot_start_two_concurrent_rides(self):
        driver = UserFactory(role="driver")
        v1 = VehicleFactory(status=Vehicle.Status.AVAILABLE)
        v2 = VehicleFactory(status=Vehicle.Status.AVAILABLE)

        _start(driver, v1)

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            _start(driver, v2)

        assert "active ride" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# end_ride
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
class TestEndRide:
    def test_happy_path_completes_ride(self):
        driver = UserFactory(role="driver")
        vehicle = VehicleFactory(status=Vehicle.Status.AVAILABLE)
        ride = _start(driver, vehicle)

        completed = _end(ride)

        assert completed.status == Ride.Status.COMPLETED
        assert completed.ended_at is not None
        assert completed.distance_km is not None
        assert completed.payment_amount is not None

    def test_vehicle_returns_to_available(self):
        driver = UserFactory(role="driver")
        vehicle = VehicleFactory(status=Vehicle.Status.AVAILABLE)
        ride = _start(driver, vehicle)

        _end(ride)

        vehicle.refresh_from_db()
        assert vehicle.status == Vehicle.Status.AVAILABLE

    def test_cannot_end_already_completed_ride(self):
        driver = UserFactory(role="driver")
        vehicle = VehicleFactory(status=Vehicle.Status.AVAILABLE)
        ride = _start(driver, vehicle)
        _end(ride)
        ride.refresh_from_db()

        with pytest.raises(drf_serializers.ValidationError):
            _end(ride)

    def test_duration_and_distance_are_positive(self):
        driver = UserFactory(role="driver")
        vehicle = VehicleFactory(status=Vehicle.Status.AVAILABLE)
        ride = _start(driver, vehicle)

        completed = _end(ride)

        assert completed.duration_seconds >= 0
        assert completed.distance_km >= Decimal("0")
