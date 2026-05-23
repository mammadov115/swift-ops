import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .services import get_location


class VehicleLocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live vehicle location updates.

    Connection URL:  ws://host/ws/vehicles/{vehicle_id}/

    Flow:
      1. Client connects  →  added to group "vehicle_{id}",
                             current location sent immediately (if stored).
      2. GPS POST arrives →  services.store_location() calls group_send()
                             with type "location.update"
      3. location_update()  is called  →  payload forwarded to the client.

    The client should NOT send any messages – this is a one-way push channel.
    """

    async def connect(self):
        self.vehicle_id = self.scope["url_route"]["kwargs"]["vehicle_id"]
        self.group_name = f"vehicle_{self.vehicle_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send the last-known location so the client is immediately up-to-date.
        location = await sync_to_async(get_location)(self.vehicle_id)
        if location:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "location_update",
                        **location,
                    }
                )
            )
        else:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "connected",
                        "vehicle_id": self.vehicle_id,
                        "message": "No location data yet. Waiting for GPS events.",
                    }
                )
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name, self.channel_name
        )

    # Channels routes messages by type:  "location.update" → location_update()
    async def location_update(self, event):
        """Forward a channel layer group message to the WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "location_update",
                    "vehicle_id": event["vehicle_id"],
                    "lat": event["lat"],
                    "lng": event["lng"],
                    "battery": event["battery"],
                    "timestamp": event["timestamp"],
                }
            )
        )
