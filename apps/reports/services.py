from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.rides.models import Ride
from apps.vehicles.models import Vehicle

from .models import DailyReport, ZoneActivityReport


def _day_window(target: date) -> tuple[datetime, datetime]:
    """Return timezone-aware start/end datetimes for *target* (local timezone)."""
    start = timezone.make_aware(datetime(target.year, target.month, target.day))
    return start, start + timedelta(days=1)


def compute_daily_report(target_date: date) -> DailyReport:
    """
    Aggregate ride and revenue metrics for *target_date* and upsert a
    DailyReport row.  Safe to call multiple times (idempotent).
    """
    day_start, day_end = _day_window(target_date)

    rides_qs = Ride.objects.filter(
        started_at__gte=day_start, started_at__lt=day_end
    )
    agg = rides_qs.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=Ride.Status.COMPLETED)),
        cancelled=Count("id", filter=Q(status=Ride.Status.CANCELLED)),
        revenue=Sum(
            "payment_amount", filter=Q(status=Ride.Status.COMPLETED)
        ),
    )

    report, _ = DailyReport.objects.update_or_create(
        date=target_date,
        defaults={
            "total_rides": agg["total"] or 0,
            "completed_rides": agg["completed"] or 0,
            "cancelled_rides": agg["cancelled"] or 0,
            "total_revenue": agg["revenue"] or Decimal("0.00"),
            "active_vehicles": Vehicle.objects.filter(is_active=True).count(),
        },
    )
    return report


def compute_zone_activity(target_date: date) -> list[ZoneActivityReport]:
    """
    Aggregate per-zone ride counts for *target_date* and upsert
    ZoneActivityReport rows.  Safe to call multiple times (idempotent).

    Zone is read from ``vehicle.zone`` at aggregation time (current snapshot)
    because the Ride model does not store historical zone data.
    """
    day_start, day_end = _day_window(target_date)

    started_by_zone = (
        Ride.objects.filter(started_at__gte=day_start, started_at__lt=day_end)
        .values("vehicle__zone")
        .annotate(count=Count("id"))
    )
    ended_by_zone = (
        Ride.objects.filter(
            ended_at__gte=day_start,
            ended_at__lt=day_end,
            status=Ride.Status.COMPLETED,
        )
        .values("vehicle__zone")
        .annotate(count=Count("id"))
    )

    started_map = {
        (row["vehicle__zone"] or "unknown"): row["count"]
        for row in started_by_zone
    }
    ended_map = {
        (row["vehicle__zone"] or "unknown"): row["count"]
        for row in ended_by_zone
    }

    reports = []
    for zone in set(started_map) | set(ended_map):
        if not zone:
            continue
        r, _ = ZoneActivityReport.objects.update_or_create(
            date=target_date,
            zone=zone,
            defaults={
                "rides_started": started_map.get(zone, 0),
                "rides_ended": ended_map.get(zone, 0),
            },
        )
        reports.append(r)
    return reports
