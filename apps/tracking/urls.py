from django.urls import path

from .views import TrackingViewSet

_v = TrackingViewSet.as_view

urlpatterns = [
    path(
        "live-map/",
        _v({"get": "live_map"}),
        name="live-map",
    ),
    path(
        "<uuid:pk>/location/",
        _v({"post": "ingest", "get": "current_location"}),
        name="vehicle-location",
    ),
]
