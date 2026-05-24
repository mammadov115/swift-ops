from django.db import models
from django.utils.translation import gettext_lazy as _


class DailyReport(models.Model):
    """
    Pre-computed daily aggregate of ride and revenue metrics.

    Populated by the ``reports.compute_daily_report`` Celery task which runs
    every night after midnight to process the previous day's data.
    The dashboard reads directly from this table — no heavy DB queries on
    every request.
    """

    date = models.DateField(_("date"), unique=True, db_index=True)
    total_rides = models.PositiveIntegerField(_("total rides"), default=0)
    completed_rides = models.PositiveIntegerField(_("completed rides"), default=0)
    cancelled_rides = models.PositiveIntegerField(_("cancelled rides"), default=0)
    total_revenue = models.DecimalField(
        _("total revenue (AZN)"),
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    active_vehicles = models.PositiveIntegerField(
        _("active vehicles (snapshot)"), default=0
    )
    computed_at = models.DateTimeField(_("computed at"), auto_now=True)

    class Meta:
        verbose_name = _("daily report")
        verbose_name_plural = _("daily reports")
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"Daily Report — {self.date}"


class ZoneActivityReport(models.Model):
    """
    Per-zone ride activity for a given calendar day.

    Populated by the ``reports.compute_zone_activity`` Celery task.
    ``rides_started`` / ``rides_ended`` are counted using the vehicle's
    current zone at the time of aggregation (best-effort approximation —
    historical zone data is not stored on the Ride model).
    """

    date = models.DateField(_("date"), db_index=True)
    zone = models.CharField(_("zone"), max_length=100, db_index=True)
    rides_started = models.PositiveIntegerField(_("rides started"), default=0)
    rides_ended = models.PositiveIntegerField(_("rides ended"), default=0)
    computed_at = models.DateTimeField(_("computed at"), auto_now=True)

    class Meta:
        verbose_name = _("zone activity report")
        verbose_name_plural = _("zone activity reports")
        ordering = ["-date", "zone"]
        unique_together = [("date", "zone")]

    def __str__(self) -> str:
        return f"Zone Activity — {self.zone} — {self.date}"
