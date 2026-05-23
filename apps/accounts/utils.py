from django.conf import settings
from django.core.mail import send_mail


def send_verification_email(email: str, token: str) -> None:
    """Send an account verification email with a one-time link."""
    link = f"{settings.FRONTEND_URL}/auth/verify-email/?token={token}"
    send_mail(
        subject="Verify your SwiftOps account",
        message=(
            "Welcome to SwiftOps!\n\n"
            "Please verify your email address by visiting the link below:\n\n"
            f"{link}\n\n"
            "This link expires in 24 hours.\n\n"
            "If you did not create this account, you can safely ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_password_reset_email(email: str, token: str) -> None:
    """Send a password reset email with a one-time link."""
    link = (
        f"{settings.FRONTEND_URL}/auth/password-reset/confirm/?token={token}"
    )
    send_mail(
        subject="Reset your SwiftOps password",
        message=(
            "You requested a password reset for your SwiftOps account.\n\n"
            "Click the link below to set a new password:\n\n"
            f"{link}\n\n"
            "This link expires in 30 minutes.\n\n"
            "If you did not request a password reset, please ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
