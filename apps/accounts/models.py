import uuid
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        DRIVER = "driver", _("Driver")
        OPERATOR = "operator", _("Operator")
        SUPERADMIN = "superadmin", _("Super Admin")

    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.DRIVER,
    )
    is_email_verified = models.BooleanField(_("email verified"), default=False)
    fcm_token = models.CharField(
        _("FCM token"),
        max_length=255,
        blank=True,
        default="",
        help_text=_("Firebase Cloud Messaging device token for push notifications."),
    )

    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.username


class EmailVerificationToken(models.Model):
    EXPIRY_HOURS = 24

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_token",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("email verification token")
        verbose_name_plural = _("email verification tokens")

    def is_expired(self) -> bool:
        return timezone.now() > self.created_at + timedelta(
            hours=self.EXPIRY_HOURS
        )


class PasswordResetToken(models.Model):
    EXPIRY_MINUTES = 30

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("password reset token")
        verbose_name_plural = _("password reset tokens")

    def is_expired(self) -> bool:
        return timezone.now() > self.created_at + timedelta(
            minutes=self.EXPIRY_MINUTES
        )
