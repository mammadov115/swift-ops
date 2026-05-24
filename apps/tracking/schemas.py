from drf_spectacular.utils import OpenApiResponse, extend_schema

from .serializers import GPSEventSerializer, LiveMapItemSerializer, VehicleLocationSerializer

gps_event_schema = extend_schema(
    summary="Ingest a GPS event",
    description=(
        "Called by vehicle hardware (or a simulator) to report the current "
        "position and battery level. "
        "Coordinates are immediately stored in Redis and broadcast to all "
        "WebSocket clients subscribed to this vehicle."
    ),
    request=GPSEventSerializer,
    responses={
        200: VehicleLocationSerializer,
        400: OpenApiResponse(description="Invalid payload"),
        404: OpenApiResponse(description="Vehicle not found or deactivated"),
    },
    tags=["Tracking"],
)

vehicle_location_schema = extend_schema(
    summary="Get current vehicle location",
    description=(
        "Returns the most recent GPS coordinates for a vehicle, "
        "read directly from Redis. Returns 404 if no location has been "
        "recorded yet."
    ),
    responses={
        200: VehicleLocationSerializer,
        404: OpenApiResponse(description="No location data yet"),
    },
    tags=["Tracking"],
)

live_map_schema = extend_schema(
    summary="Live map — all vehicle coordinates",
    description=(
        "Returns the last-known GPS position and battery level for every "
        "active vehicle, read directly from Redis. Vehicles with no location "
        "data recorded yet are omitted. "
        "Requires operator or superadmin role."
    ),
    responses={200: LiveMapItemSerializer(many=True)},
    tags=["Tracking"],
)
