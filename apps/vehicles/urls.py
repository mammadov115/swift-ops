from django.urls import path

from .views import VehicleViewSet

_v = VehicleViewSet.as_view

urlpatterns = [
    path(
        "",
        _v({"get": "list", "post": "create"}),
        name="vehicle-list",
    ),
    path(
        "<uuid:pk>/",
        _v({"get": "retrieve", "delete": "destroy"}),
        name="vehicle-detail",
    ),
    path(
        "<uuid:pk>/status/",
        _v({"patch": "update_status"}),
        name="vehicle-status",
    ),
    path(
        "<uuid:pk>/qr/",
        _v({"post": "assign_qr"}),
        name="vehicle-qr",
    ),
]
