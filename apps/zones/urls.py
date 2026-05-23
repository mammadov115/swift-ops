from django.urls import path

from .views import ZoneViewSet

_v = ZoneViewSet.as_view

urlpatterns = [
    path("", _v({"get": "list", "post": "create"}), name="zone-list"),
    path(
        "<uuid:pk>/",
        _v({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="zone-detail",
    ),
]
