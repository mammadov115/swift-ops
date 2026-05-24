from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = [
        "id",
        "user",
        "type",
        "title",
        "is_read",
        "created_at",
    ]
    list_filter = ["type", "is_read"]
    search_fields = ["user__username", "title", "body"]
    readonly_fields = ["id", "user", "type", "title", "body", "data", "read_at", "created_at"]
    ordering = ["-created_at"]
    fieldsets = (
        (
            _("Notification"),
            {
                "classes": ("tab",),
                "fields": ("id", "user", "type", "title", "body", "data"),
            },
        ),
        (
            _("Status"),
            {
                "classes": ("tab",),
                "fields": ("is_read", "read_at"),
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ("tab",),
                "fields": ("created_at",),
            },
        ),
    )
