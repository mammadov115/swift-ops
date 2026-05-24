import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class Type(models.TextChoices):
        LOW_BATTERY = "low_battery", _("Low Battery")
        ZONE_VIOLATION = "zone_violation", _("Zone Violation")
        PAYMENT_FAILED = "payment_failed", _("Payment Failed")
        RIDE_STARTED = "ride_started", _("Ride Started")
        RIDE_COMPLETED = "ride_completed", _("Ride Completed")
        ACCOUNT_BLOCKED = "account_blocked", _("Account Blocked")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(_("type"), max_length=30, choices=Type.choices)
    title = models.CharField(_("title"), max_length=255)
    body = models.TextField(_("body"))
    data = models.JSONField(_("data"), default=dict, blank=True)
    is_read = models.BooleanField(_("read"), default=False, db_index=True)
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
        ]
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")

    def __str__(self) -> str:
        return f"{self.get_type_display()} → {self.user_id}"
