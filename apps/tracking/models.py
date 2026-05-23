import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.vehicles.models import Vehicle


class TrackingConfig(models.Model):
    """
    Singleton model for runtime-configurable inactivity thresholds.

    There is always exactly one row (pk=1).  Edit it from the admin panel
    under Tracking → Tracking Configuration.  Changes are reflected within
    CACHE_TTL seconds across all worker processes.
    """

    CACHE_KEY = "tracking:config"
    CACHE_TTL = 300  # seconds

    default_threshold_minutes = models.PositiveSmallIntegerField(
        _("default threshold (minutes)"),
        default=30,
        help_text=_("Fallback used for vehicle types not listed below."),
    )
    scooter_threshold_minutes = models.PositiveSmallIntegerField(
        _("scooter threshold (minutes)"),
        default=15,
    )
    bicycle_threshold_minutes = models.PositiveSmallIntegerField(
        _("bicycle threshold (minutes)"),
        default=20,
    )
    moped_threshold_minutes = models.PositiveSmallIntegerField(
        _("moped threshold (minutes)"),
        default=30,
    )

    class Meta:
        verbose_name = _("tracking configuration")
        verbose_name_plural = _("tracking configuration")

    def __str__(self) -> str:
        return "Tracking Configuration"

    # ── Singleton enforcement ─────────────────────────────────────────────

    def save(self, *args, **kwargs) -> None:
        self.pk = 1
        super().save(*args, **kwargs)
        self._invalidate_cache()

    def delete(self, *args, **kwargs) -> tuple:
        # Prevent accidental deletion of the singleton record.
        return 0, {}

    def _invalidate_cache(self) -> None:
        from django.core.cache import cache

        cache.delete(self.CACHE_KEY)

    # ── Class-level helpers ───────────────────────────────────────────────

    @classmethod
    def get_solo(cls) -> "TrackingConfig":
        """Return the singleton row, creating it with defaults if absent."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def get_thresholds(cls) -> dict:
        """
        Return a {vehicle_type: minutes} dict, served from cache when warm.
        """
        from django.core.cache import cache

        cached: dict | None = cache.get(cls.CACHE_KEY)
        if cached is not None:
            return cached
        config = cls.get_solo()
        thresholds = {
            "scooter": config.scooter_threshold_minutes,
            "bicycle": config.bicycle_threshold_minutes,
            "moped": config.moped_threshold_minutes,
            "default": config.default_threshold_minutes,
        }
        cache.set(cls.CACHE_KEY, thresholds, cls.CACHE_TTL)
        return thresholds


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
