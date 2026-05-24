from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationToken, PasswordResetToken
from .utils import send_password_reset_email, send_verification_email

User = get_user_model()


def register_user(validated_data: dict) -> None:
    """Create a new user account and dispatch an email verification link."""
    user = User.objects.create_user(
        username=validated_data["username"],
        password=validated_data["password"],
        email=validated_data["email"],
        first_name=validated_data["first_name"],
        last_name=validated_data["last_name"],
    )
    token = EmailVerificationToken.objects.create(user=user)
    send_verification_email(user.email, str(token.token))


def verify_email(token_value: str) -> None:
    """Mark a user's email as verified; delete the token on success."""
    try:
        token = EmailVerificationToken.objects.select_related("user").get(
            token=token_value
        )
    except EmailVerificationToken.DoesNotExist:
        raise serializers.ValidationError(
            {"detail": "Invalid or expired token."}
        )

    if token.is_expired():
        raise serializers.ValidationError(
            {"detail": "Invalid or expired token."}
        )

    user = token.user
    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])
    token.delete()


def login_user(username: str, password: str) -> dict:
    """Authenticate a user and return JWT access + refresh tokens."""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise serializers.ValidationError({"detail": "Invalid credentials."})

    if not user.check_password(password):
        raise serializers.ValidationError({"detail": "Invalid credentials."})

    if not user.is_active:
        raise serializers.ValidationError(
            {"detail": "This account has been deactivated."}
        )

    if not user.is_email_verified:
        raise serializers.ValidationError(
            {"detail": "Please verify your email address before logging in."}
        )

    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def update_user_profile(user, validated_data: dict) -> None:
    """Update mutable profile fields (first_name, last_name) for the given user."""
    updatable_fields = ("first_name", "last_name")
    fields_to_save = [f for f in updatable_fields if f in validated_data]
    if not fields_to_save:
        return
    for field in fields_to_save:
        setattr(user, field, validated_data[field])
    user.save(update_fields=fields_to_save)


def set_user_active_status(
    target_user, requesting_user, *, is_active: bool
) -> None:
    """
    Block or activate a user account with role-based restrictions.

    Rules:
    - Users cannot modify their own status.
    - Operators can only modify drivers; superadmins can modify anyone.
    """
    if target_user.pk == requesting_user.pk:
        raise serializers.ValidationError(
            {"detail": "You cannot modify your own account status."}
        )
    if (
        requesting_user.role != User.Role.SUPERADMIN
        and target_user.role != User.Role.DRIVER
    ):
        raise serializers.ValidationError(
            {"detail": "Only superadmins can modify non-driver accounts."}
        )
    target_user.is_active = is_active
    target_user.save(update_fields=["is_active"])


def request_password_reset(email: str) -> None:
    """
    Generate a password reset token and email it to the user.

    Intentionally silent when the email is not found to prevent user enumeration.
    """
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return

    token = PasswordResetToken.objects.create(user=user)
    send_password_reset_email(user.email, str(token.token))


def confirm_password_reset(token_value: str, new_password: str) -> None:
    """Validate the reset token, run password validators, and update the password."""
    try:
        token = PasswordResetToken.objects.select_related("user").get(
            token=token_value, is_used=False
        )
    except PasswordResetToken.DoesNotExist:
        raise serializers.ValidationError(
            {"detail": "Invalid or expired token."}
        )

    if token.is_expired():
        raise serializers.ValidationError(
            {"detail": "Invalid or expired token."}
        )

    user = token.user
    try:
        validate_password(new_password, user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"new_password": list(exc.messages)})

    user.set_password(new_password)
    user.save(update_fields=["password"])
    token.is_used = True
    token.save(update_fields=["is_used"])


def save_fcm_token(user, token: str) -> None:
    """Persist the FCM device token for push notification delivery."""
    user.fcm_token = token
    user.save(update_fields=["fcm_token"])
