from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Payment, PaymentMethod, PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(ModelAdmin):
    list_display = [
        "code",
        "discount_type",
        "discount_value",
        "uses_count",
        "max_uses",
        "is_active",
        "valid_from",
        "valid_until",
    ]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code"]
    readonly_fields = ["uses_count", "created_at", "updated_at"]
    ordering = ["-created_at"]
    fieldsets = (
        (
            _("Code"),
            {
                "classes": ("tab",),
                "fields": ("code", "is_active"),
            },
        ),
        (
            _("Discount"),
            {
                "classes": ("tab",),
                "fields": ("discount_type", "discount_value"),
            },
        ),
        (
            _("Limits"),
            {
                "classes": ("tab",),
                "fields": ("max_uses", "uses_count", "valid_from", "valid_until"),
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


@admin.register(PaymentMethod)
class PaymentMethodAdmin(ModelAdmin):
    list_display = [
        "id",
        "user",
        "provider",
        "brand",
        "last4",
        "is_default",
        "is_active",
        "created_at",
    ]
    list_filter = ["provider", "brand", "is_default", "is_active"]
    search_fields = ["user__username", "last4"]
    readonly_fields = [
        "id",
        "provider",
        "provider_payment_method_id",
        "type",
        "last4",
        "brand",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    fieldsets = (
        (
            _("Identity"),
            {
                "classes": ("tab",),
                "fields": ("id", "user", "is_default", "is_active"),
            },
        ),
        (
            _("Provider"),
            {
                "classes": ("tab",),
                "fields": (
                    "provider",
                    "provider_payment_method_id",
                    "type",
                    "last4",
                    "brand",
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


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = [
        "id",
        "user",
        "ride",
        "status",
        "amount",
        "discount_amount",
        "provider",
        "created_at",
    ]
    list_filter = ["status", "provider"]
    search_fields = ["user__username", "provider_payment_id"]
    readonly_fields = [
        "id",
        "ride",
        "user",
        "payment_method",
        "promo_code",
        "amount",
        "discount_amount",
        "provider",
        "provider_payment_id",
        "provider_metadata",
        "failure_reason",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    fieldsets = (
        (
            _("Identity"),
            {
                "classes": ("tab",),
                "fields": ("id", "user", "ride", "status"),
            },
        ),
        (
            _("Amounts"),
            {
                "classes": ("tab",),
                "fields": ("amount", "discount_amount", "promo_code"),
            },
        ),
        (
            _("Provider"),
            {
                "classes": ("tab",),
                "fields": (
                    "provider",
                    "provider_payment_id",
                    "provider_metadata",
                    "failure_reason",
                    "payment_method",
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
