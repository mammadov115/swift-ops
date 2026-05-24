import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Ride(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rides",
        verbose_name=_("driver"),
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="rides",
        verbose_name=_("vehicle"),
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    start_latitude = models.DecimalField(
        _("start latitude"), max_digits=9, decimal_places=6
    )
    start_longitude = models.DecimalField(
        _("start longitude"), max_digits=9, decimal_places=6
    )
    end_latitude = models.DecimalField(
        _("end latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    end_longitude = models.DecimalField(
        _("end longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(_("started at"), auto_now_add=True)
    ended_at = models.DateTimeField(_("ended at"), null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(
        _("duration (seconds)"), null=True, blank=True
    )
    distance_km = models.DecimalField(
        _("distance (km)"),
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
    )
    payment_amount = models.DecimalField(
        _("payment amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("ride")
        verbose_name_plural = _("rides")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Ride {self.id} — {self.driver} on {self.vehicle}"
