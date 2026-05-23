from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import InactivityAlert


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

    @admin.display(boolean=True, description=_("Open"))
    def is_open_display(self, obj: InactivityAlert) -> bool:
        return obj.is_open
