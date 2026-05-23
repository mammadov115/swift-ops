import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.vehicles.models import Vehicle


class InactivityAlert(models.Model):
    """
    Raised when a vehicle has not sent a GPS event for longer than the
    configured inactivity threshold.  Automatically resolved when the
    vehicle resumes movement.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name="inactivity_alerts",
        verbose_name=_("vehicle"),
    )
    opened_at = models.DateTimeField(_("opened at"), auto_now_add=True)
    closed_at = models.DateTimeField(_("closed at"), null=True, blank=True)
    threshold_minutes = models.PositiveSmallIntegerField(
        _("threshold (minutes)"),
        help_text=_("Inactivity threshold (in minutes) that triggered this alert."),
    )

    class Meta:
        verbose_name = _("inactivity alert")
        verbose_name_plural = _("inactivity alerts")
        ordering = ["-opened_at"]
        indexes = [
            models.Index(fields=["vehicle", "closed_at"]),
        ]

    def __str__(self) -> str:
        status = "open" if self.closed_at is None else "closed"
        return f"InactivityAlert({self.vehicle_id}, {status})"

    @property
    def is_open(self) -> bool:
        return self.closed_at is None
