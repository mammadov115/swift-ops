from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import DailyReport, ZoneActivityReport


@admin.register(DailyReport)
class DailyReportAdmin(ModelAdmin):
    list_display = (
        "date",
        "total_rides",
        "completed_rides",
        "cancelled_rides",
        "completion_rate_display",
        "total_revenue",
        "active_vehicles",
        "computed_at",
    )
    list_filter = ("date",)
    search_fields = ("date",)
    readonly_fields = (
        "date",
        "total_rides",
        "completed_rides",
        "cancelled_rides",
        "total_revenue",
        "active_vehicles",
        "computed_at",
    )
    date_hierarchy = "date"
    ordering = ("-date",)
    fieldsets = (
        (
            _("Rides"),
            {
                "classes": ("tab",),
                "fields": ("date", "total_rides", "completed_rides", "cancelled_rides"),
            },
        ),
        (
            _("Revenue & Fleet"),
            {
                "classes": ("tab",),
                "fields": ("total_revenue", "active_vehicles"),
            },
        ),
        (
            _("Metadata"),
            {
                "classes": ("tab",),
                "fields": ("computed_at",),
            },
        ),
    )

    @admin.display(description=_("Completion rate"))
    def completion_rate_display(self, obj: DailyReport) -> str:
        if not obj.total_rides:
            return "—"
        rate = obj.completed_rides / obj.total_rides * 100
        return f"{rate:.1f}%"

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(ZoneActivityReport)
class ZoneActivityReportAdmin(ModelAdmin):
    list_display = (
        "date",
        "zone",
        "rides_started",
        "rides_ended",
        "net_rides_display",
        "computed_at",
    )
    list_filter = ("zone",)
    search_fields = ("zone",)
    readonly_fields = (
        "date",
        "zone",
        "rides_started",
        "rides_ended",
        "computed_at",
    )
    date_hierarchy = "date"
    ordering = ("-date", "zone")
    fieldsets = (
        (
            _("Zone Activity"),
            {
                "classes": ("tab",),
                "fields": ("date", "zone", "rides_started", "rides_ended"),
            },
        ),
        (
            _("Metadata"),
            {
                "classes": ("tab",),
                "fields": ("computed_at",),
            },
        ),
    )

    @admin.display(description=_("Net rides"))
    def net_rides_display(self, obj: ZoneActivityReport) -> str:
        net = obj.rides_started - obj.rides_ended
        if net > 0:
            return f"+{net}"
        return str(net)

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
