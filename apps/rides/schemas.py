from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from .serializers import RideEndSerializer, RideSerializer, RideStartSerializer

ride_start_schema = extend_schema(
    summary="Start a ride",
    description=(
        "Starts a new ride for the authenticated driver on the specified vehicle. "
        "Uses row-level locking (SELECT FOR UPDATE) to prevent two drivers from "
        "simultaneously claiming the same vehicle. "
        "Returns 400 if the vehicle is unavailable or the driver already has an active ride."
    ),
    request=RideStartSerializer,
    responses={
        201: RideSerializer,
        400: OpenApiResponse(description="Validation error"),
        403: OpenApiResponse(description="Driver role required"),
    },
    tags=["Rides"],
)

ride_end_schema = extend_schema(
    summary="End a ride",
    description=(
        "Ends the specified active ride. "
        "Records end coordinates, calculates duration and geodesic distance "
        "(Haversine via geopy), computes the payment amount, and returns the "
        "vehicle to 'available' status — all inside a single DB transaction."
    ),
    request=RideEndSerializer,
    responses={
        200: RideSerializer,
        400: OpenApiResponse(description="Ride is not active"),
        404: OpenApiResponse(description="Ride not found"),
    },
    tags=["Rides"],
)

ride_active_schema = extend_schema(
    summary="Get active ride",
    description=(
        "Returns the driver's currently active ride. "
        "Returns 404 if the driver has no active ride."
    ),
    responses={
        200: RideSerializer,
        404: OpenApiResponse(description="No active ride"),
    },
    tags=["Rides"],
)

ride_history_schema = extend_schema(
    summary="Ride history",
    description=(
        "Returns a paginated list of completed and cancelled rides "
        "for the authenticated driver, ordered by most recent first. "
        "Default page size: 20."
    ),
    parameters=[
        OpenApiParameter(
            name="page",
            description="Page number",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="page_size",
            description="Results per page (max 100)",
            required=False,
            type=int,
        ),
    ],
    responses={200: RideSerializer(many=True)},
    tags=["Rides"],
)
