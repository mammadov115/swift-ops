from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.accounts.permissions import IsDriver
from apps.rides.models import Ride

from . import services
from .fare import calculate_fare
from .providers import get_provider
from .schemas import (
    payment_charge_schema,
    payment_list_schema,
    payment_method_create_schema,
    payment_method_delete_schema,
    payment_method_list_schema,
    payment_method_set_default_schema,
    payment_retry_schema,
    promo_validate_schema,
    webhook_stripe_schema,
)
from .serializers import (
    ChargeRideSerializer,
    CreatePaymentMethodSerializer,
    FareBreakdownSerializer,
    PaymentMethodSerializer,
    PaymentSerializer,
    PromoCodeSerializer,
    RetryPaymentSerializer,
    ValidatePromoSerializer,
)


class PaymentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ─────────────────────────────────────────────────────────────────────────────
# Payment Methods
# ─────────────────────────────────────────────────────────────────────────────


class PaymentMethodViewSet(ViewSet):
    def get_permissions(self):
        return [IsDriver()]

    @payment_method_list_schema
    def list(self, request):
        methods = services.list_payment_methods(request.user)
        return Response(PaymentMethodSerializer(methods, many=True).data)

    @payment_method_create_schema
    def create(self, request):
        serializer = CreatePaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = services.add_payment_method(
            request.user, serializer.validated_data["token"]
        )
        return Response(
            PaymentMethodSerializer(method).data,
            status=status.HTTP_201_CREATED,
        )

    @payment_method_delete_schema
    def destroy(self, request, pk=None):
        services.remove_payment_method(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @payment_method_set_default_schema
    def set_default(self, request, pk=None):
        method = services.set_default_payment_method(request.user, pk)
        return Response(PaymentMethodSerializer(method).data)


# ─────────────────────────────────────────────────────────────────────────────
# Payments
# ─────────────────────────────────────────────────────────────────────────────


class PaymentViewSet(ViewSet):
    def get_permissions(self):
        if self.action == "webhook_stripe":
            return [AllowAny()]
        return [IsDriver()]

    @payment_list_schema
    def list(self, request):
        payments = services.get_payment_history(request.user)
        paginator = PaymentPagination()
        page = paginator.paginate_queryset(payments, request)
        return paginator.get_paginated_response(
            PaymentSerializer(page, many=True).data
        )

    @payment_charge_schema
    def charge(self, request):
        serializer = ChargeRideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            ride = Ride.objects.get(
                pk=data["ride_id"],
                driver=request.user,
                status=Ride.Status.COMPLETED,
            )
        except Ride.DoesNotExist:
            return Response(
                {"detail": "Completed ride not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment = services.charge_for_ride(
            ride=ride,
            user=request.user,
            payment_method_id=data.get("payment_method_id"),
            promo_code_str=data.get("promo_code"),
        )
        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )

    @payment_retry_schema
    def retry(self, request, pk=None):
        serializer = RetryPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = services.retry_payment(
            payment_id=pk,
            user=request.user,
            payment_method_id=serializer.validated_data.get("payment_method_id"),
        )
        return Response(PaymentSerializer(payment).data)

    @csrf_exempt
    @webhook_stripe_schema
    def webhook_stripe(self, request):
        provider = get_provider()
        signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = provider.verify_webhook(request.body, signature)
        except Exception:
            return Response(
                {"detail": "Invalid webhook signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        services.process_stripe_webhook(event)
        return Response({"detail": "ok"})


# ─────────────────────────────────────────────────────────────────────────────
# Promo Codes
# ─────────────────────────────────────────────────────────────────────────────


class PromoCodeViewSet(ViewSet):
    def get_permissions(self):
        return [IsDriver()]

    @promo_validate_schema
    def validate(self, request):
        serializer = ValidatePromoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        promo = services.validate_promo_code(data["code"], request.user)

        fare_preview = None
        distance_km = data.get("distance_km")
        duration_seconds = data.get("duration_seconds")
        if distance_km is not None and duration_seconds is not None:
            breakdown = calculate_fare(distance_km, duration_seconds, promo)
            fare_preview = FareBreakdownSerializer(breakdown).data

        return Response(
            {
                "promo_code": PromoCodeSerializer(promo).data,
                "fare_preview": fare_preview,
            }
        )
