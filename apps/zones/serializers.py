from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Zone


class ZoneSerializer(GeoFeatureModelSerializer):
    """Full GeoJSON Feature — used for list, retrieve, and create responses."""

    class Meta:
        model = Zone
        geo_field = "geometry"
        fields = ["id", "name", "zone_type", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]


class ZoneCreateSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Zone
        geo_field = "geometry"
        fields = ["name", "zone_type", "geometry"]


class ZoneUpdateSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Zone
        geo_field = "geometry"
        fields = ["name", "zone_type", "geometry"]
        extra_kwargs = {
            "name": {"required": False},
            "zone_type": {"required": False},
            "geometry": {"required": False},
        }
