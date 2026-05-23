from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
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
    list_filter = ["status", "type", "is_active", "zone"]
    search_fields = ["id", "qr_code", "zone"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
