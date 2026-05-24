import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Personal notification WebSocket feed.

    Connection URL:  ws://host/ws/notifications/

    Any authenticated user may connect.  Each user is placed in their own
    channel group ``notifications_{user_id}`` so that notifications are
    delivered only to the intended recipient.

    Message format pushed to the client::

        {
            "type":              "notification",
            "id":                "<uuid>",
            "notification_type": "low_battery" | "payment_failed" | ...,
            "title":             "Low Battery Alert",
            "body":              "Vehicle X battery is at 15%.",
            "data":              { ...extra context... },
            "created_at":        "2026-05-24T10:00:00+00:00"
        }
    """

    async def connect(self):
        user = self.scope.get("user")
        if not (user and user.is_authenticated):
            await self.accept()
            await self.close(code=4001)
            return

        self.group_name = f"notifications_{user.pk}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name
            )

    # Channels routes: "notification.push" → notification_push()
    async def notification_push(self, event):
        """Forward a notification payload to the connected WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "id": event["id"],
                    "notification_type": event["notification_type"],
                    "title": event["title"],
                    "body": event["body"],
                    "data": event["data"],
                    "created_at": event["created_at"],
                }
            )
        )
