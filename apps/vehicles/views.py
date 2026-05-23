from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.accounts.permissions import IsOperatorOrSuperAdmin

from . import services
from .filters import VehicleFilter
from .models import Vehicle
from .schemas import (
    vehicle_assign_qr_schema,
    vehicle_create_schema,
    vehicle_delete_schema,
    vehicle_list_schema,
    vehicle_retrieve_schema,
    vehicle_update_status_schema,
)
from .serializers import (
    QRCodeAssignSerializer,
    VehicleCreateSerializer,
    VehicleDetailSerializer,
    VehicleListSerializer,
    VehicleStatusUpdateSerializer,
)


class VehicleViewSet(ViewSet):
    """
    Manages the full vehicle lifecycle:
    creation, listing, status transitions, QR assignment, and soft deletion.
    """

    _OPERATOR_ACTIONS = frozenset(
        {"create", "update_status", "destroy", "assign_qr"}
    )

    def get_permissions(self):
        if self.action in self._OPERATOR_ACTIONS:
            return [IsOperatorOrSuperAdmin()]
        return [IsAuthenticated()]

    @vehicle_list_schema
    def list(self, request):
        queryset = Vehicle.objects.filter(is_active=True)

        # Drivers may only see vehicles that are ready to rent.
        if getattr(request.user, "role", None) == "driver":
            queryset = queryset.filter(status=Vehicle.Status.AVAILABLE)

        filterset = VehicleFilter(
            request.GET, queryset=queryset, request=request
        )
        serializer = VehicleListSerializer(filterset.qs, many=True)
        return Response(serializer.data)

    @vehicle_create_schema
    def create(self, request):
        serializer = VehicleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = services.create_vehicle(serializer.validated_data)
        return Response(
            VehicleDetailSerializer(vehicle).data,
            status=status.HTTP_201_CREATED,
        )

    @vehicle_retrieve_schema
    def retrieve(self, request, pk=None):
        vehicle = services.get_active_vehicle(pk)
        return Response(VehicleDetailSerializer(vehicle).data)

    @vehicle_update_status_schema
    def update_status(self, request, pk=None):
        vehicle = services.get_active_vehicle(pk)
        serializer = VehicleStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = services.update_vehicle_status(
            vehicle, serializer.validated_data["status"]
        )
        return Response(VehicleDetailSerializer(vehicle).data)

    @vehicle_delete_schema
    def destroy(self, request, pk=None):
        vehicle = services.get_active_vehicle(pk)
        services.deactivate_vehicle(vehicle)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @vehicle_assign_qr_schema
    def assign_qr(self, request, pk=None):
        vehicle = services.get_active_vehicle(pk)
        serializer = QRCodeAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = services.assign_qr_code(
            vehicle, serializer.validated_data["qr_code"]
        )
        return Response(VehicleDetailSerializer(vehicle).data)
