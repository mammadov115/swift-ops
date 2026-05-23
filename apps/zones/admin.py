from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Zone


@admin.register(Zone)
class ZoneAdmin(ModelAdmin):
    list_display = ["name", "zone_type", "is_active", "created_at"]
    list_filter = ["zone_type", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    fieldsets = (
        (_("Identity"), {"classes": ("tab",), "fields": ("id", "name", "zone_type")}),
        (_("Geometry"), {"classes": ("tab",), "fields": ("geometry",)}),
        (_("Status"), {"classes": ("tab",), "fields": ("is_active",)}),
        (_("Timestamps"), {"classes": ("tab",), "fields": ("created_at", "updated_at")}),
    )
