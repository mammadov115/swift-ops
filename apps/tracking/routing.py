from django.urls import re_path

from .consumers import VehicleLocationConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/vehicles/(?P<vehicle_id>[0-9a-f-]{36})/$",
        VehicleLocationConsumer.as_asgi(),
    ),
]
