"""
Tracking services – all Redis I/O and channel layer dispatch lives here.

Redis key schema
----------------
  vehicle:{uuid}:location  →  Redis hash
      lat        Decimal string  e.g. "40.409264"
      lng        Decimal string  e.g. "49.867092"
      battery    Integer string  e.g. "85"
      timestamp  ISO-8601 UTC    e.g. "2026-05-23T10:00:00+00:00"

Channel group schema
--------------------
  vehicle_{uuid}  →  all WebSocket consumers subscribed to that vehicle
"""

from datetime import datetime, timezone

import redis
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.shortcuts import get_object_or_404

from apps.vehicles.models import Vehicle

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    """Return a lazily-created, module-level Redis client (thread-safe)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
    return _redis_client


def _location_key(vehicle_id: str) -> str:
    return f"vehicle:{vehicle_id}:location"


def store_location(vehicle_id: str, lat: str, lng: str, battery: int) -> dict:
    """
    Persist live coordinates to Redis and broadcast to the vehicle's
    WebSocket group.

    Returns the location payload that was stored.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    payload = {
        "vehicle_id": vehicle_id,
        "lat": str(lat),
        "lng": str(lng),
        "battery": battery,
        "timestamp": timestamp,
    }

    r = _get_redis()
    r.hset(
        _location_key(vehicle_id),
        mapping={
            "lat": payload["lat"],
            "lng": payload["lng"],
            "battery": str(battery),
            "timestamp": timestamp,
        },
    )

    resolve_inactivity_alert(vehicle_id)
    _broadcast_location(vehicle_id, payload)
    return payload


def get_location(vehicle_id: str) -> dict | None:
    """
    Read the latest stored location for a vehicle from Redis.
    Returns None if no location has been recorded yet.
    """
    r = _get_redis()
    data = r.hgetall(_location_key(vehicle_id))
    if not data:
        return None
    return {
        "vehicle_id": vehicle_id,
        "lat": data["lat"],
        "lng": data["lng"],
        "battery": int(data["battery"]),
        "timestamp": data["timestamp"],
    }


def _broadcast_location(vehicle_id: str, payload: dict) -> None:
    """Push an update to every WebSocket client watching this vehicle."""
    channel_layer = get_channel_layer()
    group_name = f"vehicle_{vehicle_id}"
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "location.update",  # maps to consumer method location_update
            **payload,
        },
    )


def validate_vehicle_exists(vehicle_id: str) -> Vehicle:
    """
    Verify the vehicle exists and is active before accepting GPS data.
    Raises Http404 if not found.
    """
    return get_object_or_404(Vehicle, pk=vehicle_id, is_active=True)


# ── Inactivity alert helpers ──────────────────────────────────────────────────


def _alert_flag_key(vehicle_id: str) -> str:
    return f"vehicle:{vehicle_id}:inactivity_alert"


def get_last_seen_timestamp(vehicle_id: str) -> "datetime | None":
    """
    Return the last GPS timestamp for a vehicle from Redis, or None if the
    vehicle has never reported a location.
    """
    raw = _get_redis().hget(_location_key(vehicle_id), "timestamp")
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def get_inactivity_threshold(vehicle_type: str) -> int:
    """Return the inactivity threshold in minutes for the given vehicle type."""
    from .models import TrackingConfig  # noqa: PLC0415

    thresholds = TrackingConfig.get_thresholds()
    return thresholds.get(vehicle_type, thresholds["default"])


def _broadcast_inactivity_alert(
    vehicle_id: str,
    vehicle_type: str,
    threshold_minutes: int,
    opened_at: str,
) -> None:
    """Push a new inactivity alert to every connected operator WebSocket client."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "operator_alerts",
        {
            "type": "inactivity.alert",
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle_type,
            "threshold_minutes": threshold_minutes,
            "opened_at": opened_at,
        },
    )


def open_inactivity_alert(vehicle_id: str, vehicle_type: str) -> None:
    """
    Create an InactivityAlert if one is not already open for this vehicle.

    A Redis flag (vehicle:{id}:inactivity_alert) is set to avoid a DB query
    on every Beat run.  The flag is created here and deleted by
    resolve_inactivity_alert() when movement resumes.
    """
    # Import here to avoid a circular import at module load time.
    from .models import InactivityAlert  # noqa: PLC0415

    r = _get_redis()
    if r.exists(_alert_flag_key(vehicle_id)):
        return  # Redis flag present — alert already open

    # Guard against Redis eviction: double-check the DB.
    if InactivityAlert.objects.filter(
        vehicle_id=vehicle_id, closed_at__isnull=True
    ).exists():
        r.set(_alert_flag_key(vehicle_id), "1")  # re-sync the flag
        return

    threshold = get_inactivity_threshold(vehicle_type)
    alert = InactivityAlert.objects.create(
        vehicle_id=vehicle_id, threshold_minutes=threshold
    )
    r.set(_alert_flag_key(vehicle_id), "1")
    _broadcast_inactivity_alert(
        vehicle_id=vehicle_id,
        vehicle_type=vehicle_type,
        threshold_minutes=threshold,
        opened_at=alert.opened_at.isoformat(),
    )


def resolve_inactivity_alert(vehicle_id: str) -> None:
    """
    Close any open inactivity alert when the vehicle resumes movement.

    Called automatically from store_location() on every GPS event so that
    open alerts are resolved as soon as the vehicle is active again.
    Skips the DB entirely when no Redis flag is present (fast path).
    """
    from .models import InactivityAlert  # noqa: PLC0415

    r = _get_redis()
    if not r.exists(_alert_flag_key(vehicle_id)):
        return  # no open alert — nothing to do

    now = datetime.now(tz=timezone.utc)
    InactivityAlert.objects.filter(
        vehicle_id=vehicle_id, closed_at__isnull=True
    ).update(closed_at=now)
    r.delete(_alert_flag_key(vehicle_id))
