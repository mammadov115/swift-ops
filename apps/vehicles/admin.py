from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(ModelAdmin):
    list_display = [
        "id",
        "type",
        "status",
        "battery_level",
        "zone",
        "qr_code",
        "is_active",
        "updated_at",
    ]
    list_filter = ["status", "type", "is_active"]
    search_fields = ["id", "qr_code", "zone"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    fieldsets = (
        (
            _("Identity"),
            {
                "classes": ("tab",),
                "fields": ("id", "type", "qr_code", "zone"),
            },
        ),
        (
            _("Status"),
            {
                "classes": ("tab",),
                "fields": ("status", "battery_level", "is_active"),
            },
        ),
        (
            _("Location"),
            {
                "classes": ("tab",),
                "fields": ("latitude", "longitude"),
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
