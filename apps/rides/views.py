from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.accounts.permissions import IsDriver

from . import services
from .schemas import (
    ride_active_schema,
    ride_end_schema,
    ride_history_schema,
    ride_start_schema,
)
from .serializers import RideEndSerializer, RideSerializer, RideStartSerializer


class RidePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class RideViewSet(ViewSet):
    """Manages ride lifecycle: start, end, active ride lookup, and history."""

    def get_permissions(self):
        return [IsDriver()]

    @ride_history_schema
    def list(self, request):
        rides = services.list_ride_history(request.user)
        paginator = RidePagination()
        page = paginator.paginate_queryset(rides, request)
        serializer = RideSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @ride_start_schema
    def start(self, request):
        serializer = RideStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ride = services.start_ride(
            driver=request.user,
            vehicle_id=data["vehicle_id"],
            start_lat=data["start_latitude"],
            start_lng=data["start_longitude"],
        )
        return Response(
            RideSerializer(ride).data, status=status.HTTP_201_CREATED
        )

    @ride_active_schema
    def active(self, request):
        ride = services.get_active_ride(request.user)
        return Response(RideSerializer(ride).data)

    @ride_end_schema
    def end(self, request, pk=None):
        ride = services.get_ride(request.user, pk)
        serializer = RideEndSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ride = services.end_ride(
            ride, data["end_latitude"], data["end_longitude"]
        )
        return Response(RideSerializer(ride).data)
