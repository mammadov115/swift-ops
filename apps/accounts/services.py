from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def register_user(validated_data: dict) -> None:
    """Create an active user account."""
    User.objects.create_user(
        username=validated_data["username"],
        password=validated_data["password"],
        email=validated_data["email"],
        first_name=validated_data["first_name"],
        last_name=validated_data["last_name"],
    )


def login_user(username: str, password: str) -> dict:
    """Authenticate a user with username/password and return JWT access + refresh tokens."""
    user = authenticate(username=username, password=password)

    if user is None:
        raise serializers.ValidationError({"detail": "Invalid credentials."})

    if not user.is_active:
        raise serializers.ValidationError(
            {"detail": "This account has been deactivated."}
        )

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
