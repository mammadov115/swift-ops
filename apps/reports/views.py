from datetime import date

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.accounts.permissions import IsOperatorOrSuperAdmin

from django.utils import timezone

from .models import DailyReport, ZoneActivityReport
from .schemas import daily_stats_schema, revenue_schema, zone_activity_schema
from .serializers import (
    DailyReportSerializer,
    RevenueReportSerializer,
    ZoneActivityReportSerializer,
)


class ReportPagination(PageNumberPagination):
    page_size = 31
    page_size_query_param = "page_size"
    max_page_size = 365


class ReportViewSet(ViewSet):
    """
    Read-only endpoints that serve pre-computed report snapshots.

    All endpoints are restricted to operators and superadmins.
    Reports are populated by the ``reports.compute_daily_report`` and
    ``reports.compute_zone_activity`` Celery Beat tasks.
    """

    permission_classes = [IsOperatorOrSuperAdmin]

    def _parse_date_range(self, request) -> tuple[date, date]:
        today = timezone.now().date()
        start_str = request.query_params.get("start_date")
        end_str = request.query_params.get("end_date")
        try:
            start = date.fromisoformat(start_str) if start_str else today
            end = date.fromisoformat(end_str) if end_str else today
        except ValueError as exc:
            raise ValidationError(
                {"detail": "Invalid date format. Use YYYY-MM-DD."}
            ) from exc
        if start > end:
            raise ValidationError(
                {"detail": "start_date must not be after end_date."}
            )
        return start, end

    @daily_stats_schema
    def daily_stats(self, request):
        start, end = self._parse_date_range(request)
        qs = DailyReport.objects.filter(
            date__gte=start, date__lte=end
        ).order_by("-date")
        paginator = ReportPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                DailyReportSerializer(page, many=True).data
            )
        return Response(DailyReportSerializer(qs, many=True).data)

    @revenue_schema
    def revenue(self, request):
        start, end = self._parse_date_range(request)
        qs = DailyReport.objects.filter(
            date__gte=start, date__lte=end
        ).order_by("-date")
        paginator = ReportPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                RevenueReportSerializer(page, many=True).data
            )
        return Response(RevenueReportSerializer(qs, many=True).data)

    @zone_activity_schema
    def zone_activity(self, request):
        start, end = self._parse_date_range(request)
        qs = ZoneActivityReport.objects.filter(
            date__gte=start, date__lte=end
        ).order_by("-date", "zone")
        paginator = ReportPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            return paginator.get_paginated_response(
                ZoneActivityReportSerializer(page, many=True).data
            )
        return Response(ZoneActivityReportSerializer(qs, many=True).data)
