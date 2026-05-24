from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.accounts.permissions import IsOperatorOrSuperAdmin

from apps.vehicles.models import Vehicle

from . import services
from .schemas import gps_event_schema, live_map_schema, vehicle_location_schema
from .serializers import GPSEventSerializer, LiveMapItemSerializer, VehicleLocationSerializer


class TrackingViewSet(ViewSet):
    """
    Handles GPS event ingestion and last-known-location retrieval.

    WebSocket connections live in consumers.py and are entirely separate
    from this HTTP surface.
    """

    def get_permissions(self):
        # Only operators/superadmins may push GPS data or view the live map.
        # Any authenticated user may read a single vehicle's last known location.
        if self.action in {"ingest", "live_map"}:
            return [IsOperatorOrSuperAdmin()]
        return [IsAuthenticated()]

    @gps_event_schema
    def ingest(self, request, pk=None):
        """Accept a GPS event, persist to Redis, broadcast via WebSocket."""
        services.validate_vehicle_exists(pk)
        serializer = GPSEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = services.store_location(
            vehicle_id=str(pk),
            lat=serializer.validated_data["lat"],
            lng=serializer.validated_data["lng"],
            battery=serializer.validated_data["battery"],
        )
        return Response(VehicleLocationSerializer(payload).data)

    @vehicle_location_schema
    def current_location(self, request, pk=None):
        """Return the most recent GPS coordinates stored in Redis."""
        services.validate_vehicle_exists(pk)
        location = services.get_location(str(pk))
        if location is None:
            return Response(
                {"detail": "No location data available for this vehicle."},
                status=404,
            )
        return Response(VehicleLocationSerializer(location).data)

    @live_map_schema
    def live_map(self, request):
        """Return live coordinates for all active vehicles, read from Redis."""
        vehicle_ids = Vehicle.objects.filter(is_active=True).values_list(
            "id", flat=True
        )
        locations = [
            loc
            for vid in vehicle_ids
            if (loc := services.get_location(str(vid))) is not None
        ]
        return Response(LiveMapItemSerializer(locations, many=True).data)
