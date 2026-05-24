import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PromoCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", _("Percentage")
        FIXED = "fixed", _("Fixed Amount")

    code = models.CharField(_("code"), max_length=50, unique=True)
    discount_type = models.CharField(
        _("discount type"),
        max_length=20,
        choices=DiscountType.choices,
    )
    discount_value = models.DecimalField(
        _("discount value"), max_digits=8, decimal_places=2
    )
    max_uses = models.PositiveIntegerField(
        _("max uses"), null=True, blank=True
    )
    uses_count = models.PositiveIntegerField(_("uses count"), default=0)
    valid_from = models.DateTimeField(_("valid from"))
    valid_until = models.DateTimeField(
        _("valid until"), null=True, blank=True
    )
    is_active = models.BooleanField(_("is active"), default=True)
    used_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="used_promo_codes",
        verbose_name=_("used by"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("promo code")
        verbose_name_plural = _("promo codes")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code


class PaymentMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        verbose_name=_("user"),
    )
    provider = models.CharField(_("provider"), max_length=50)
    provider_payment_method_id = models.CharField(
        _("provider payment method id"), max_length=255
    )
    type = models.CharField(_("type"), max_length=50)
    last4 = models.CharField(_("last 4 digits"), max_length=4)
    brand = models.CharField(_("brand"), max_length=50)
    is_default = models.BooleanField(_("is default"), default=False)
    is_active = models.BooleanField(_("is active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("payment method")
        verbose_name_plural = _("payment methods")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.brand} ****{self.last4} ({self.user})"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")
        REFUNDED = "refunded", _("Refunded")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ride = models.OneToOneField(
        "rides.Ride",
        on_delete=models.PROTECT,
        related_name="payment",
        verbose_name=_("ride"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name=_("user"),
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("payment method"),
    )
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name=_("promo code"),
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    amount = models.DecimalField(
        _("amount"), max_digits=10, decimal_places=2
    )
    discount_amount = models.DecimalField(
        _("discount amount"), max_digits=10, decimal_places=2, default=0
    )
    provider = models.CharField(_("provider"), max_length=50)
    provider_payment_id = models.CharField(
        _("provider payment id"), max_length=255, blank=True
    )
    provider_metadata = models.JSONField(
        _("provider metadata"), default=dict
    )
    failure_reason = models.TextField(_("failure reason"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Payment {self.id} — {self.status} — {self.amount}"
