from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import InactivityAlert, TrackingConfig


@admin.register(TrackingConfig)
class TrackingConfigAdmin(ModelAdmin):
    fieldsets = (
        (
            _("Inactivity thresholds"),
            {
                "classes": ("tab",),
                "fields": (
                    "default_threshold_minutes",
                    "scooter_threshold_minutes",
                    "bicycle_threshold_minutes",
                    "moped_threshold_minutes",
                ),
            },
        ),
    )

    def has_add_permission(self, request) -> bool:
        return not TrackingConfig.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def changelist_view(self, request, extra_context=None):
        obj = TrackingConfig.get_solo()
        url = reverse("admin:tracking_trackingconfig_change", args=[obj.pk])
        return redirect(url)


@admin.register(InactivityAlert)
class InactivityAlertAdmin(ModelAdmin):
    list_display = (
        "vehicle",
        "opened_at",
        "closed_at",
        "threshold_minutes",
        "is_open_display",
    )
    list_filter = ("closed_at",)
    readonly_fields = ("id", "vehicle", "opened_at", "threshold_minutes")
    search_fields = ("vehicle__id",)
    date_hierarchy = "opened_at"
    ordering = ("-opened_at",)

    def has_add_permission(self, request) -> bool:
        return False

    @admin.display(boolean=True, description=_("Open"))
    def is_open_display(self, obj: InactivityAlert) -> bool:
        return obj.is_open
