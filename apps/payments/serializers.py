from decimal import Decimal

from rest_framework import serializers

from .fare import FareBreakdown, calculate_fare
from .models import Payment, PaymentMethod, PromoCode


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "provider",
            "type",
            "last4",
            "brand",
            "is_default",
            "created_at",
        ]
        read_only_fields = fields


class CreatePaymentMethodSerializer(serializers.Serializer):
    """Accepts a provider token (e.g. Stripe payment_method ID). No raw card data."""

    token = serializers.CharField(
        help_text="Provider-issued payment method token (e.g. pm_xxx for Stripe)."
    )


class SetDefaultSerializer(serializers.Serializer):
    pass  # No body — pk is in the URL


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = [
            "id",
            "code",
            "discount_type",
            "discount_value",
            "valid_from",
            "valid_until",
        ]
        read_only_fields = fields


class ValidatePromoSerializer(serializers.Serializer):
    code = serializers.CharField()
    distance_km = serializers.DecimalField(
        max_digits=8,
        decimal_places=4,
        required=False,
        allow_null=True,
        help_text="Optional: provide to preview the discounted fare.",
    )
    duration_seconds = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=0,
    )


class FareBreakdownSerializer(serializers.Serializer):
    base_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    distance_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    duration_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()


class ValidatePromoResponseSerializer(serializers.Serializer):
    promo_code = PromoCodeSerializer()
    fare_preview = FareBreakdownSerializer(allow_null=True)


class PaymentSerializer(serializers.ModelSerializer):
    ride_id = serializers.UUIDField(source="ride.id", read_only=True)
    payment_method_last4 = serializers.CharField(
        source="payment_method.last4",
        read_only=True,
        allow_null=True,
    )
    payment_method_brand = serializers.CharField(
        source="payment_method.brand",
        read_only=True,
        allow_null=True,
    )
    promo_code = serializers.CharField(
        source="promo_code.code",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "ride_id",
            "status",
            "amount",
            "discount_amount",
            "provider",
            "provider_payment_id",
            "payment_method",
            "payment_method_last4",
            "payment_method_brand",
            "promo_code",
            "failure_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ChargeRideSerializer(serializers.Serializer):
    ride_id = serializers.UUIDField()
    payment_method_id = serializers.UUIDField(required=False, allow_null=True)
    promo_code = serializers.CharField(required=False, allow_null=True)


class RetryPaymentSerializer(serializers.Serializer):
    payment_method_id = serializers.UUIDField(required=False, allow_null=True)
