import django_filters

from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    battery_level__lte = django_filters.NumberFilter(
        field_name="battery_level", lookup_expr="lte"
    )
    battery_level__gte = django_filters.NumberFilter(
        field_name="battery_level", lookup_expr="gte"
    )

    class Meta:
        model = Vehicle
        fields = ["status", "type", "zone"]
