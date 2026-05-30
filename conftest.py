"""
Root conftest — fixtures available to every test module in the project.

Philosophy
----------
- Use real DB (pytest-django creates an isolated test database).
- Use fakeredis instead of mocking Redis so cache/session/Celery broker
  behaviour is realistic without needing a running Redis instance.
- Keep fixtures small and composable; build complex state by combining them.
"""
import fakeredis
import pytest
from django.core.cache import caches
from pytest_django.fixtures import SettingsWrapper
from rest_framework.test import APIClient

from apps.accounts.models import User


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def fake_redis(settings: SettingsWrapper):
    """
    Replace the real Redis backend with an in-memory fakeredis instance for
    every test.  `autouse=True` means no test ever accidentally hits a real
    Redis server.
    """
    server = fakeredis.FakeServer()

    settings.CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://localhost:1",  # address is ignored by fakeredis
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {"connection_class": fakeredis.FakeConnection, "server": server},
            },
        }
    }

    # Force Django to re-create the cache backend with the new settings.
    for cache in caches.all():
        cache.close()

    yield server


# ---------------------------------------------------------------------------
# API client helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF test client."""
    return APIClient()


@pytest.fixture
def auth_client(driver_user: User) -> APIClient:
    """DRF test client pre-authenticated as a driver."""
    client = APIClient()
    client.force_authenticate(user=driver_user)
    return client


@pytest.fixture
def operator_client(operator_user: User) -> APIClient:
    """DRF test client pre-authenticated as an operator."""
    client = APIClient()
    client.force_authenticate(user=operator_user)
    return client


# ---------------------------------------------------------------------------
# User fixtures  (rely on UserFactory defined per-app or in tests/factories.py)
# ---------------------------------------------------------------------------

@pytest.fixture
def driver_user(db) -> User:
    from tests.factories import UserFactory
    return UserFactory(role=User.Role.DRIVER, is_email_verified=True)


@pytest.fixture
def operator_user(db) -> User:
    from tests.factories import UserFactory
    return UserFactory(role=User.Role.OPERATOR, is_email_verified=True)
