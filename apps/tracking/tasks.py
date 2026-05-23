"""
Celery Beat periodic tasks for the tracking app.

All tasks are registered with @shared_task so they work regardless of which
Celery app instance is active.
"""

from datetime import datetime, timezone

from celery import shared_task

from apps.vehicles.models import Vehicle

from . import services


@shared_task(name="tracking.check_vehicle_inactivity")
def check_vehicle_inactivity() -> dict:
    """
    Scan every active vehicle and raise an InactivityAlert when no GPS event
    has arrived within the configured threshold.

    This task is intended to run every INACTIVITY_CHECK_INTERVAL_MINUTES
    minutes via Celery Beat.  Deduplication is handled in services.py using
    a Redis flag \u2014 a vehicle that is already flagged will not produce a second
    DB row, so this task is safe to call as frequently as needed.

    Returns a summary dict {"alerted": N, "skipped": M} for logging.
    """
    now = datetime.now(tz=timezone.utc)
    alerted = 0
    skipped = 0

    vehicles = Vehicle.objects.filter(is_active=True).only("id", "type").iterator()
    for vehicle in vehicles:
        vehicle_id = str(vehicle.id)
        threshold = services.get_inactivity_threshold(vehicle.type)

        last_seen = services.get_last_seen_timestamp(vehicle_id)
        if last_seen is None:
            # Vehicle has never reported a location \u2014 nothing to compare yet.
            continue

        elapsed_minutes = (now - last_seen).total_seconds() / 60
        if elapsed_minutes >= threshold:
            services.open_inactivity_alert(vehicle_id, vehicle.type)
            alerted += 1
        else:
            skipped += 1

    return {"alerted": alerted, "skipped": skipped}
