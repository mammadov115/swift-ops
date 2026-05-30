"""
Authentication endpoint tests.

Priority: ride engine > **authentication** > payments > everything else.

These are integration-level tests — they exercise the full Django request/
response cycle so they also validate URL routing, serializers, and the
custom exception handler envelope.
"""
import pytest

from apps.accounts.models import User
from tests.factories import UserFactory


AUTH_REGISTER_URL = "/api/auth/register/"
AUTH_LOGIN_URL = "/api/auth/login/"


@pytest.mark.django_db
class TestRegister:
    def test_successful_registration_returns_201(self, api_client):
        payload = {
            "username": "newdriver",
            "email": "newdriver@example.com",
            "password": "Str0ng!Pass",
            "first_name": "New",
            "last_name": "Driver",
        }
        response = api_client.post(AUTH_REGISTER_URL, payload, format="json")

        assert response.status_code == 201

    def test_duplicate_email_returns_400_with_error_envelope(self, api_client):
        UserFactory(email="taken@example.com")
        payload = {
            "username": "another",
            "email": "taken@example.com",
            "password": "Str0ng!Pass",
            "first_name": "A",
            "last_name": "B",
        }
        response = api_client.post(AUTH_REGISTER_URL, payload, format="json")

        assert response.status_code == 400
        # Our custom exception handler must return the standard envelope.
        assert "error" in response.data
        assert "message" in response.data
        assert "detail" in response.data

    def test_missing_password_returns_error_envelope(self, api_client):
        payload = {"username": "x", "email": "x@example.com"}
        response = api_client.post(AUTH_REGISTER_URL, payload, format="json")

        assert response.status_code == 400
        assert response.data["error"] == "validation_error"


@pytest.mark.django_db
class TestLogin:
    def test_valid_credentials_return_tokens(self, api_client):
        user = UserFactory(is_email_verified=True)
        user.set_password("testpass123")
        user.save()

        response = api_client.post(
            AUTH_LOGIN_URL,
            {"username": user.username, "password": "testpass123"},
            format="json",
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_wrong_password_returns_error_envelope(self, api_client):
        user = UserFactory(is_email_verified=True)
        user.set_password("correct")
        user.save()

        response = api_client.post(
            AUTH_LOGIN_URL,
            {"username": user.username, "password": "wrong"},
            format="json",
        )

        assert response.status_code in (400, 401)
        assert "error" in response.data
        assert "message" in response.data

    def test_unverified_email_is_rejected(self, api_client):
        user = UserFactory(is_email_verified=False)
        user.set_password("testpass123")
        user.save()

        response = api_client.post(
            AUTH_LOGIN_URL,
            {"username": user.username, "password": "testpass123"},
            format="json",
        )

        # Must not hand out tokens for unverified accounts.
        assert response.status_code in (400, 401, 403)


@pytest.mark.django_db
class TestErrorEnvelope:
    """
    Sanity-check that *every* DRF error goes through our custom handler and
    returns the standard {"error", "message", "detail"} shape.
    """

    def test_unauthenticated_request_returns_envelope(self, api_client):
        # Any protected endpoint will do.
        response = api_client.get("/api/auth/profile/")

        assert response.status_code == 401
        assert set(response.data.keys()) >= {"error", "message", "detail"}
        assert response.data["error"] == "not_authenticated"

    def test_404_returns_envelope(self, api_client, operator_user):
        # POST as operator to a non-existent user ID → DRF 404 via get_object_or_404.
        api_client.force_authenticate(user=operator_user)
        response = api_client.post("/api/auth/users/99999/block/")

        assert response.status_code == 404
        assert "error" in response.data
