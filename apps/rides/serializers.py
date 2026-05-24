from decimal import Decimal

from rest_framework import serializers

from .models import Ride


class RideStartSerializer(serializers.Serializer):
    vehicle_id = serializers.UUIDField()
    start_latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
    )
    start_longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
    )


class RideEndSerializer(serializers.Serializer):
    end_latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
    )
    end_longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
    )


class RideSerializer(serializers.ModelSerializer):
    driver = serializers.StringRelatedField(read_only=True)
    vehicle_id = serializers.UUIDField(source="vehicle.id", read_only=True)
    vehicle_type = serializers.CharField(source="vehicle.type", read_only=True)

    class Meta:
        model = Ride
        fields = [
            "id",
            "driver",
            "vehicle_id",
            "vehicle_type",
            "status",
            "start_latitude",
            "start_longitude",
            "end_latitude",
            "end_longitude",
            "started_at",
            "ended_at",
            "duration_seconds",
            "distance_km",
            "payment_amount",
        ]
