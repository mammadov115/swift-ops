"""
Celery Beat tasks for the notifications app.

check_battery_levels
    Reads live battery data from Redis for every active vehicle and alerts all
    operators when a vehicle drops below BATTERY_ALERT_THRESHOLD.  A Redis flag
    (TTL 30 min) prevents duplicate alerts for the same low-battery episode.
    When battery recovers above the threshold the flag is cleared so the next
    drop will trigger a fresh alert.

cleanup_old_notifications
    Deletes read notifications older than 30 days to keep the table lean.
"""

import logging
from datetime import timedelta

import redis
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.vehicles.models import Vehicle

from . import services
from .models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(name="notifications.check_battery_levels")
def check_battery_levels() -> dict:
    """
    Scan every active vehicle's Redis location hash and create a LOW_BATTERY
    notification for all operators when battery < BATTERY_ALERT_THRESHOLD.

    Deduplication: a Redis key ``battery_alert:{vehicle_id}`` with a 30-minute
    TTL prevents duplicate alerts for the same episode.  The key is deleted
    once the battery climbs back above the threshold so a future drop will
    produce a new alert.
    """
    import redis as _redis  # noqa: PLC0415

    from apps.tracking.services import get_battery_level  # noqa: PLC0415

    threshold = getattr(settings, "BATTERY_ALERT_THRESHOLD", 20)
    r = _redis.from_url(settings.REDIS_URL)

    alerted = 0
    skipped = 0

    vehicles = Vehicle.objects.filter(is_active=True).only("id").iterator()
    operators = list(
        User.objects.filter(role__in=["operator", "superadmin"]).only(
            "id", "fcm_token", "role"
        )
    )

    for vehicle in vehicles:
        vehicle_id = str(vehicle.id)
        battery = get_battery_level(vehicle_id)
        if battery is None:
            continue

        dedup_key = f"battery_alert:{vehicle_id}"

        if battery > threshold:
            # Battery recovered — clear flag so next drop triggers a fresh alert.
            r.delete(dedup_key)
            skipped += 1
            continue

        # Already alerted for this episode — skip.
        if r.get(dedup_key):
            skipped += 1
            continue

        for operator in operators:
            services.create(
                user=operator,
                notification_type=Notification.Type.LOW_BATTERY,
                title="Low Battery Alert",
                body=f"Vehicle {vehicle_id} battery is at {battery}%.",
                data={"vehicle_id": vehicle_id, "battery": str(battery)},
            )

        # Mark as alerted; TTL = 30 min so it re-alerts after prolonged inactivity.
        r.set(dedup_key, "1", ex=1800)
        alerted += 1

    return {"alerted": alerted, "skipped": skipped}


@shared_task(name="notifications.cleanup_old_notifications")
def cleanup_old_notifications() -> dict:
    """Delete read notifications older than 30 days."""
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(
        is_read=True, created_at__lt=cutoff
    ).delete()
    logger.info("Cleaned up %d old notifications", deleted)
    return {"deleted": deleted}
