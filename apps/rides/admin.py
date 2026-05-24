from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Ride


@admin.register(Ride)
class RideAdmin(ModelAdmin):
    list_display = [
        "id",
        "driver",
        "vehicle",
        "status",
        "started_at",
        "ended_at",
        "distance_km",
        "payment_amount",
    ]
    list_filter = ["status"]
    search_fields = ["id", "driver__username", "vehicle__id"]
    readonly_fields = [
        "id",
        "started_at",
        "duration_seconds",
        "distance_km",
        "payment_amount",
        "created_at",
        "updated_at",
    ]
    ordering = ["-started_at"]
    fieldsets = (
        (
            _("Ride"),
            {
                "classes": ("tab",),
                "fields": ("id", "driver", "vehicle", "status"),
            },
        ),
        (
            _("Start"),
            {
                "classes": ("tab",),
                "fields": ("start_latitude", "start_longitude", "started_at"),
            },
        ),
        (
            _("End"),
            {
                "classes": ("tab",),
                "fields": (
                    "end_latitude",
                    "end_longitude",
                    "ended_at",
                ),
            },
        ),
        (
            _("Billing"),
            {
                "classes": ("tab",),
                "fields": (
                    "duration_seconds",
                    "distance_km",
                    "payment_amount",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ("tab",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
