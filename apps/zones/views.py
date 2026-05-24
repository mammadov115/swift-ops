from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.accounts.permissions import IsOperatorOrSuperAdmin

from . import services
from .schemas import (
    zone_create_schema,
    zone_destroy_schema,
    zone_list_schema,
    zone_retrieve_schema,
    zone_update_schema,
)
from .serializers import ZoneCreateSerializer, ZoneSerializer, ZoneUpdateSerializer


class ZoneViewSet(ViewSet):
    """Manages zone lifecycle: creation, listing, updates, and soft deletion."""

    _WRITE_ACTIONS = frozenset({"create", "partial_update", "destroy"})

    def get_permissions(self):
        if self.action in self._WRITE_ACTIONS:
            return [IsOperatorOrSuperAdmin()]
        return [IsAuthenticated()]

    @zone_list_schema
    def list(self, request):
        zones = services.list_active_zones()
        return Response(ZoneSerializer(zones, many=True).data)

    @zone_create_schema
    def create(self, request):
        serializer = ZoneCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        zone = services.create_zone(serializer.validated_data)
        return Response(ZoneSerializer(zone).data, status=status.HTTP_201_CREATED)

    @zone_retrieve_schema
    def retrieve(self, request, pk=None):
        zone = services.get_active_zone(pk)
        return Response(ZoneSerializer(zone).data)

    @zone_update_schema
    def partial_update(self, request, pk=None):
        zone = services.get_active_zone(pk)
        serializer = ZoneUpdateSerializer(zone, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = {k: v for k, v in serializer.validated_data.items() if v is not None}
        zone = services.update_zone(zone, data)
        return Response(ZoneSerializer(zone).data)

    @zone_destroy_schema
    def destroy(self, request, pk=None):
        zone = services.get_active_zone(pk)
        services.deactivate_zone(zone)
        return Response(status=status.HTTP_204_NO_CONTENT)
