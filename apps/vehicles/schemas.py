from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)

from .serializers import (
    QRCodeAssignSerializer,
    VehicleCreateSerializer,
    VehicleDetailSerializer,
    VehicleListSerializer,
    VehicleStatusUpdateSerializer,
)

vehicle_list_schema = extend_schema(
    summary="List active vehicles",
    description=(
        "Returns all active vehicles. "
        "Drivers are automatically restricted to AVAILABLE vehicles only. "
        "Filter by status, type, or zone using query parameters."
    ),
    parameters=[
        OpenApiParameter(
            name="status",
            description="Filter by status",
            required=False,
            type=str,
            enum=[
                "available",
                "rented",
                "charging",
                "maintenance",
                "retired",
            ],
        ),
        OpenApiParameter(
            name="type",
            description="Filter by vehicle type",
            required=False,
            type=str,
            enum=["scooter", "bicycle", "moped"],
        ),
        OpenApiParameter(
            name="zone",
            description="Filter by zone",
            required=False,
            type=str,
        ),
    ],
    responses={200: VehicleListSerializer(many=True)},
    tags=["Vehicles"],
)

vehicle_create_schema = extend_schema(
    summary="Create a vehicle",
    description=(
        "Operators and superadmins only. "
        "Status defaults to 'available'. "
        "QR code is assigned later via the dedicated endpoint."
    ),
    request=VehicleCreateSerializer,
    responses={201: VehicleDetailSerializer},
    tags=["Vehicles"],
)

vehicle_retrieve_schema = extend_schema(
    summary="Retrieve a vehicle",
    responses={
        200: VehicleDetailSerializer,
        404: OpenApiResponse(description="Vehicle not found or deactivated"),
    },
    tags=["Vehicles"],
)

vehicle_update_status_schema = extend_schema(
    summary="Update vehicle status",
    description=(
        "Validates the status transition against allowed rules. "
        "Returns 400 if the transition is not permitted. "
        "Allowed transitions: available→rented/maintenance/charging/retired, "
        "rented→available, charging→available/maintenance, "
        "maintenance→available/retired, retired→(none)."
    ),
    request=VehicleStatusUpdateSerializer,
    responses={
        200: VehicleDetailSerializer,
        400: OpenApiResponse(description="Invalid status transition"),
    },
    tags=["Vehicles"],
)

vehicle_delete_schema = extend_schema(
    summary="Deactivate a vehicle",
    description=(
        "Soft-deletes the vehicle by setting is_active=False. "
        "The record is retained so historical ride data remains intact."
    ),
    responses={
        204: None,
        404: OpenApiResponse(description="Vehicle not found"),
    },
    tags=["Vehicles"],
)

vehicle_assign_qr_schema = extend_schema(
    summary="Assign QR code to a vehicle",
    description=(
        "Links a physical QR code string to a vehicle. "
        "QR codes must be globally unique. "
        "This endpoint exists because QR codes are printed first and "
        "linked to the system later."
    ),
    request=QRCodeAssignSerializer,
    responses={
        200: VehicleDetailSerializer,
        400: OpenApiResponse(description="QR code already in use"),
    },
    tags=["Vehicles"],
)
