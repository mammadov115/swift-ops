from rest_framework import serializers


class GPSEventSerializer(serializers.Serializer):
    """Validates an inbound GPS event from a vehicle device."""

    lat = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-90,
        max_value=90,
    )
    lng = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=-180,
        max_value=180,
    )
    battery = serializers.IntegerField(min_value=0, max_value=100)


class VehicleLocationSerializer(serializers.Serializer):
    """Shape returned to WebSocket clients and in the HTTP response."""

    vehicle_id = serializers.UUIDField()
    lat = serializers.CharField()
    lng = serializers.CharField()
    battery = serializers.IntegerField()
    timestamp = serializers.CharField()
