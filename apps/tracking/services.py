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
