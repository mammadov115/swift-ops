from rest_framework import serializers

from .models import Vehicle


class VehicleCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=Vehicle.Type.choices)
    battery_level = serializers.IntegerField(
        min_value=0, max_value=100, default=100
    )
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    zone = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )


class VehicleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id",
            "type",
            "status",
            "battery_level",
            "zone",
            "latitude",
            "longitude",
        ]


class VehicleDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id",
            "type",
            "status",
            "battery_level",
            "latitude",
            "longitude",
            "qr_code",
            "zone",
            "is_active",
            "created_at",
            "updated_at",
        ]


class VehicleStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Vehicle.Status.choices)


class QRCodeAssignSerializer(serializers.Serializer):
    qr_code = serializers.CharField(max_length=100)
