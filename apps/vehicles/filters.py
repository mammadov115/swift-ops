import django_filters

from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    class Meta:
        model = Vehicle
        fields = ["status", "type", "zone"]
