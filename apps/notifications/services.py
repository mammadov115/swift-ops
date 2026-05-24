"""
Notification services – creation, delivery, and history.

Responsibilities
----------------
create()          Store a notification in DB and attempt real-time delivery.
mark_read()       Flip is_read / read_at on a notification owned by a user.
list_notifications()  Return an ordered queryset for the notification history
                       endpoint.

Delivery is best-effort: if WebSocket or push delivery fails, the notification
is already persisted and the user will see it on next history load.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Notification
from .providers import get_push_provider

logger = logging.getLogger(__name__)


def _notification_group(user_id) -> str:
    return f"notifications_{user_id}"


def create(
    user,
    notification_type: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> Notification:
    """
    Persist a notification and attempt real-time delivery via WebSocket and
    FCM push.  Either delivery channel may fail silently — the DB record is
    always the source of truth.
    """
    notif = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        body=body,
        data=data or {},
    )
    _deliver_ws(notif, user)
    _deliver_push(notif, user)
    return notif


def mark_read(user, notification_id: str) -> Notification:
    """Mark a notification as read.  Raises DoesNotExist if not found or not owned."""
    notif = Notification.objects.get(pk=notification_id, user=user)
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save(update_fields=["is_read", "read_at"])
    return notif


def list_notifications(user):
    """Return all notifications for *user*, newest first."""
    return Notification.objects.filter(user=user)


# ─────────────────────────────────────────────────────────────────────────────
# Internal delivery helpers
# ─────────────────────────────────────────────────────────────────────────────


def _deliver_ws(notif: Notification, user) -> None:
    """Push the notification to any open WebSocket sessions for the user."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            _notification_group(user.pk),
            {
                "type": "notification.push",
                "id": str(notif.pk),
                "notification_type": notif.type,
                "title": notif.title,
                "body": notif.body,
                "data": notif.data,
                "created_at": notif.created_at.isoformat(),
            },
        )
    except Exception:
        logger.exception("WS delivery failed for notification %s", notif.pk)


def _deliver_push(notif: Notification, user) -> None:
    """Send an FCM push notification if the user has a device token registered."""
    fcm_token = getattr(user, "fcm_token", "") or ""
    if not fcm_token:
        return
    try:
        provider = get_push_provider()
        result = provider.send(
            fcm_token=fcm_token,
            title=notif.title,
            body=notif.body,
            data={"notification_id": str(notif.pk), "type": notif.type, **notif.data},
        )
        if not result.success:
            logger.warning(
                "FCM push failed for notification %s: %s", notif.pk, result.error
            )
    except Exception:
        logger.exception("FCM push raised for notification %s", notif.pk)
