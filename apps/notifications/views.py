from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from . import services
from .models import Notification
from .schemas import notification_list_schema, notification_mark_read_schema
from .serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NotificationViewSet(ViewSet):
    def get_permissions(self):
        return [IsAuthenticated()]

    @notification_list_schema
    def list(self, request):
        qs = services.list_notifications(request.user)
        paginator = NotificationPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(
            NotificationSerializer(page, many=True).data
        )

    @notification_mark_read_schema
    def mark_read(self, request, pk=None):
        try:
            notif = services.mark_read(request.user, pk)
        except Notification.DoesNotExist:
            raise NotFound()
        return Response(NotificationSerializer(notif).data, status=status.HTTP_200_OK)
