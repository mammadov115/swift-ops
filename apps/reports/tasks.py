from datetime import date, timedelta

from celery import shared_task
from django.utils import timezone


@shared_task(name="reports.compute_daily_report")
def compute_daily_report_task(date_str: str | None = None) -> dict:
    """
    Compute and store the DailyReport for *date_str* (ISO-8601) or yesterday.

    Called by Celery Beat every night so the previous day's metrics are ready
    before operators open the dashboard in the morning.  Can also be triggered
    manually for any past date:

        compute_daily_report_task.apply_async(args=["2025-06-01"])
    """
    from . import services

    target = (
        date.fromisoformat(date_str)
        if date_str
        else (timezone.now().date() - timedelta(days=1))
    )
    report = services.compute_daily_report(target)
    return {
        "date": str(report.date),
        "total_rides": report.total_rides,
        "completed_rides": report.completed_rides,
        "cancelled_rides": report.cancelled_rides,
        "total_revenue": str(report.total_revenue),
        "active_vehicles": report.active_vehicles,
    }


@shared_task(name="reports.compute_zone_activity")
def compute_zone_activity_task(date_str: str | None = None) -> dict:
    """
    Compute and store ZoneActivityReport rows for *date_str* or yesterday.

    Same scheduling strategy as ``compute_daily_report_task``.
    """
    from . import services

    target = (
        date.fromisoformat(date_str)
        if date_str
        else (timezone.now().date() - timedelta(days=1))
    )
    reports = services.compute_zone_activity(target)
    return {"date": str(target), "zones_computed": len(reports)}
