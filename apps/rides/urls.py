from django.urls import path

from .views import RideViewSet

_v = RideViewSet.as_view

urlpatterns = [
    path(
        "",
        _v({"get": "list", "post": "start"}),
        name="ride-list",
    ),
    path(
        "active/",
        _v({"get": "active"}),
        name="ride-active",
    ),
    path(
        "<uuid:pk>/end/",
        _v({"post": "end"}),
        name="ride-end",
    ),
]
