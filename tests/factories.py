"""
Shared factory-boy factories for the entire test suite.

Rules
-----
- Use `factory.Faker` for realistic but random data — avoids hard-coded
  strings that break when unique constraints fire in parallel test runs.
- Always use `DjangoModelFactory`; factory-boy will use Django's ORM and
  respect `db` fixtures automatically.
- Keep factories here unless they are strictly app-specific (rare).
"""
from decimal import Decimal

import factory
from django.contrib.auth.hashers import make_password
from factory.django import DjangoModelFactory

from apps.accounts.models import User
from apps.rides.models import Ride
from apps.vehicles.models import Vehicle


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    # All test users share the same plain password for simplicity.
    # Use `make_password` so Django accepts the hash.
    password = factory.LazyFunction(lambda: make_password("testpass123"))
    role = User.Role.DRIVER
    is_active = True
    is_email_verified = True


class VehicleFactory(DjangoModelFactory):
    class Meta:
        model = Vehicle

    type = Vehicle.Type.SCOOTER
    status = Vehicle.Status.AVAILABLE
    battery_level = 80
    latitude = Decimal("40.409264")
    longitude = Decimal("49.867092")
    is_active = True


class RideFactory(DjangoModelFactory):
    class Meta:
        model = Ride

    driver = factory.SubFactory(UserFactory, role=User.Role.DRIVER)
    vehicle = factory.SubFactory(VehicleFactory, status=Vehicle.Status.RENTED)
    status = Ride.Status.ACTIVE
    start_latitude = Decimal("40.409264")
    start_longitude = Decimal("49.867092")
