from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import DailyReport, ZoneActivityReport


@admin.register(DailyReport)
class DailyReportAdmin(ModelAdmin):
    list_display = [
        "date",
        "total_rides",
        "completed_rides",
        "cancelled_rides",
        "total_revenue",
        "active_vehicles",
        "computed_at",
    ]
    list_filter = ["date"]
    search_fields = ["date"]
    readonly_fields = [
        "date",
        "total_rides",
        "completed_rides",
        "cancelled_rides",
        "total_revenue",
        "active_vehicles",
        "computed_at",
    ]
    fieldsets = [
        (
            "Report",
            {
                "classes": ("tab",),
                "fields": ["date", "total_rides", "completed_rides", "cancelled_rides"],
            },
        ),
        (
            "Revenue & Fleet",
            {
                "classes": ("tab",),
                "fields": ["total_revenue", "active_vehicles", "computed_at"],
            },
        ),
    ]


@admin.register(ZoneActivityReport)
class ZoneActivityReportAdmin(ModelAdmin):
    list_display = ["date", "zone", "rides_started", "rides_ended", "computed_at"]
    list_filter = ["date", "zone"]
    search_fields = ["zone"]
    readonly_fields = [
        "date",
        "zone",
        "rides_started",
        "rides_ended",
        "computed_at",
    ]
    fieldsets = [
        (
            "Zone Activity",
            {
                "classes": ("tab",),
                "fields": ["date", "zone", "rides_started", "rides_ended", "computed_at"],
            },
        ),
    ]
