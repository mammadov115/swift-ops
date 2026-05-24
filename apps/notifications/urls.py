from django.urls import path

from .views import NotificationViewSet

app_name = "notifications"

urlpatterns = [
    path(
        "",
        NotificationViewSet.as_view({"get": "list"}),
        name="notification-list",
    ),
    path(
        "<uuid:pk>/",
        NotificationViewSet.as_view({"patch": "mark_read"}),
        name="notification-mark-read",
    ),
]
