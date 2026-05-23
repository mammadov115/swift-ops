import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Vehicle(models.Model):
    class Type(models.TextChoices):
        SCOOTER = "scooter", _("Scooter")
        BICYCLE = "bicycle", _("Bicycle")
        MOPED = "moped", _("Moped")

    class Status(models.TextChoices):
        AVAILABLE = "available", _("Available")
        RENTED = "rented", _("Rented")
        CHARGING = "charging", _("Charging")
        MAINTENANCE = "maintenance", _("Maintenance")
        RETIRED = "retired", _("Retired")

    # Valid transitions: key = current status, value = allowed next statuses.
    # Anything not listed here is forbidden and will raise ValidationError.
    _TRANSITIONS: dict = {
        "available": {"rented", "maintenance", "charging", "retired"},
        "rented": {"available"},
        "charging": {"available", "maintenance"},
        "maintenance": {"available", "retired"},
        "retired": set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(_("type"), max_length=20, choices=Type.choices)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    battery_level = models.PositiveSmallIntegerField(
        _("battery level (%)"),
        default=100,
        validators=[MaxValueValidator(100)],
    )
    latitude = models.DecimalField(
        _("latitude"), max_digits=9, decimal_places=6
    )
    longitude = models.DecimalField(
        _("longitude"), max_digits=9, decimal_places=6
    )
    qr_code = models.CharField(
        _("QR code"), max_length=100, unique=True, blank=True, null=True
    )
    zone = models.CharField(_("zone"), max_length=100, blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("vehicle")
        verbose_name_plural = _("vehicles")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_type_display()} — {self.id}"

    def transition_to(self, new_status: str) -> None:
        """
        Attempt a status transition. Raises ValidationError if the move is
        not permitted from the current status.

        Calling code is responsible for persisting the model afterward.
        This method calls save() internally so all callers get consistent
        DB writes through a single code path.
        """
        allowed = self._TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValidationError(
                _(
                    "Cannot transition from '%(current)s' to '%(new)s'. "
                    "Allowed transitions: %(allowed)s."
                )
                % {
                    "current": self.status,
                    "new": new_status,
                    "allowed": ", ".join(sorted(allowed)) or "none",
                }
            )
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])
