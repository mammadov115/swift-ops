import uuid

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class Zone(models.Model):
    class ZoneType(models.TextChoices):
        PARKING_ALLOWED = "parking_allowed", _("Parking Allowed")
        NO_PARKING = "no_parking", _("No Parking")
        SPEED_LIMITED = "speed_limited", _("Speed Limited")
        FORBIDDEN = "forbidden", _("Forbidden")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("name"), max_length=100)
    zone_type = models.CharField(
        _("zone type"), max_length=20, choices=ZoneType.choices
    )
    geometry = models.PolygonField(_("geometry"), srid=4326)
    is_active = models.BooleanField(_("active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("zone")
        verbose_name_plural = _("zones")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_zone_type_display()})"
