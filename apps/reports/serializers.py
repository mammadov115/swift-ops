from rest_framework import serializers

from .models import DailyReport, ZoneActivityReport


class DailyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReport
        fields = [
            "date",
            "total_rides",
            "completed_rides",
            "cancelled_rides",
            "total_revenue",
            "active_vehicles",
            "computed_at",
        ]


class RevenueReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReport
        fields = ["date", "total_revenue", "completed_rides", "computed_at"]


class ZoneActivityReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZoneActivityReport
        fields = ["date", "zone", "rides_started", "rides_ended", "computed_at"]
