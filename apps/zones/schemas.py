from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from .serializers import ZoneCreateSerializer, ZoneSerializer, ZoneUpdateSerializer

_GEO_FEATURE_EXAMPLE = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [49.800, 40.400],
                [49.900, 40.400],
                [49.900, 40.500],
                [49.800, 40.500],
                [49.800, 40.400],
            ]
        ],
    },
    "properties": {"name": "Downtown Forbidden Zone", "zone_type": "forbidden"},
}

zone_list_schema = extend_schema(
    summary="List active zones",
    description="Returns all active zones as a GeoJSON FeatureCollection.",
    responses={200: ZoneSerializer(many=True)},
    tags=["Zones"],
)

zone_create_schema = extend_schema(
    summary="Create a zone",
    description=(
        "Operators and superadmins only. "
        "Send a GeoJSON Feature with geometry (Polygon) and properties."
    ),
    request=ZoneCreateSerializer,
    responses={201: ZoneSerializer},
    examples=[
        OpenApiExample("Forbidden zone", value=_GEO_FEATURE_EXAMPLE, request_only=True)
    ],
    tags=["Zones"],
)

zone_retrieve_schema = extend_schema(
    summary="Retrieve a zone",
    responses={200: ZoneSerializer, 404: OpenApiResponse(description="Not found")},
    tags=["Zones"],
)

zone_update_schema = extend_schema(
    summary="Update a zone",
    description="Partial update — only send the fields you want to change.",
    request=ZoneUpdateSerializer,
    responses={200: ZoneSerializer, 404: OpenApiResponse(description="Not found")},
    tags=["Zones"],
)

zone_destroy_schema = extend_schema(
    summary="Delete (deactivate) a zone",
    description="Soft-delete: sets is_active=False to preserve historical data.",
    responses={204: None, 404: OpenApiResponse(description="Not found")},
    tags=["Zones"],
)
