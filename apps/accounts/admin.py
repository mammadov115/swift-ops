from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import User


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    ordering = ["email"]
    list_display = [
        "email",
        "username",
        "role",
        "is_email_verified",
        "is_staff",
        "is_active",
    ]
    list_filter = ["role", "is_staff", "is_active", "is_email_verified"]
    search_fields = ["email", "username", "first_name", "last_name"]
    readonly_fields = ["last_login", "date_joined"]
    fieldsets = (
        (
            _("Account"),
            {
                "classes": ("tab",),
                "fields": ("username", "email", "password"),
            },
        ),
        (
            _("Personal info"),
            {
                "classes": ("tab",),
                "fields": ("first_name", "last_name"),
            },
        ),
        (
            _("Role & verification"),
            {
                "classes": ("tab",),
                "fields": ("role", "is_email_verified"),
            },
        ),
        (
            _("Permissions"),
            {
                "classes": ("tab",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Important dates"),
            {
                "classes": ("tab",),
                "fields": ("last_login", "date_joined"),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "role",
                ),
            },
        ),
    )
