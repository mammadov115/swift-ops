from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from .serializers import (
    DailyReportSerializer,
    RevenueReportSerializer,
    ZoneActivityReportSerializer,
)

_DATE_PARAMS = [
    OpenApiParameter(
        name="start_date",
        description="Start of the date range (YYYY-MM-DD). Defaults to today.",
        required=False,
        type=str,
    ),
    OpenApiParameter(
        name="end_date",
        description="End of the date range (YYYY-MM-DD). Defaults to today.",
        required=False,
        type=str,
    ),
]

daily_stats_schema = extend_schema(
    summary="Daily ride statistics",
    description=(
        "Returns pre-computed daily ride metrics (total, completed, cancelled, "
        "active vehicles) for the requested date range. "
        "Data is computed nightly by a Celery Beat task. "
        "Requires operator or superadmin role."
    ),
    parameters=_DATE_PARAMS,
    responses={
        200: DailyReportSerializer(many=True),
        400: OpenApiResponse(description="Invalid date format or range."),
    },
    tags=["Reports"],
)

revenue_schema = extend_schema(
    summary="Revenue report",
    description=(
        "Returns pre-computed daily revenue figures for the requested date range. "
        "Revenue is the sum of payment amounts from completed rides. "
        "Data is computed nightly by a Celery Beat task. "
        "Requires operator or superadmin role."
    ),
    parameters=_DATE_PARAMS,
    responses={
        200: RevenueReportSerializer(many=True),
        400: OpenApiResponse(description="Invalid date format or range."),
    },
    tags=["Reports"],
)

zone_activity_schema = extend_schema(
    summary="Zone activity report",
    description=(
        "Returns pre-computed per-zone ride start/end counts for the requested "
        "date range. "
        "Data is computed nightly by a Celery Beat task. "
        "Requires operator or superadmin role."
    ),
    parameters=_DATE_PARAMS,
    responses={
        200: ZoneActivityReportSerializer(many=True),
        400: OpenApiResponse(description="Invalid date format or range."),
    },
    tags=["Reports"],
)
