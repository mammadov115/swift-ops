from django.urls import path

from .views import ReportViewSet

_v = ReportViewSet.as_view

urlpatterns = [
    path("daily-stats/", _v({"get": "daily_stats"}), name="report-daily-stats"),
    path("revenue/", _v({"get": "revenue"}), name="report-revenue"),
    path("zone-activity/", _v({"get": "zone_activity"}), name="report-zone-activity"),
]
