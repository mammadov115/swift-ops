from drf_spectacular.utils import OpenApiResponse, extend_schema

from .serializers import NotificationSerializer

notification_list_schema = extend_schema(
    summary="List notifications",
    description=(
        "Returns the authenticated user's notification history, newest first. "
        "Supports pagination via page and page_size query parameters."
    ),
    responses={200: NotificationSerializer(many=True)},
    tags=["Notifications"],
)

notification_mark_read_schema = extend_schema(
    summary="Mark notification as read",
    description=(
        "Marks a single notification as read and records the timestamp. "
        "Idempotent — calling it on an already-read notification is a no-op."
    ),
    responses={
        200: NotificationSerializer,
        404: OpenApiResponse(description="Notification not found."),
    },
    tags=["Notifications"],
)
