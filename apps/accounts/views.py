from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from . import services
from .permissions import IsOperatorOrSuperAdmin
from .schema import (
    email_verification_schema,
    fcm_token_schema,
    login_schema,
    password_reset_confirm_schema,
    password_reset_request_schema,
    profile_retrieve_schema,
    profile_update_schema,
    register_schema,
    token_refresh_schema,
    user_activate_schema,
    user_block_schema,
    user_list_schema,
)
from .serializers import (
    EmailVerificationSerializer,
    FCMTokenSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    TokenRefreshInputSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)

User = get_user_model()


class UserListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AuthViewSet(ViewSet):
    """Handles all stateless authentication flows."""

    permission_classes = [AllowAny]

    @register_schema
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.register_user(serializer.validated_data)
        return Response(
            {
                "detail": (
                    "Registration successful. "
                    "Please check your email to verify your account."
                )
            },
            status=status.HTTP_201_CREATED,
        )

    @email_verification_schema
    def verify_email(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.verify_email(str(serializer.validated_data["token"]))
        return Response(
            {"detail": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )

    @login_schema
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = services.login_user(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        return Response(tokens, status=status.HTTP_200_OK)

    @token_refresh_schema
    def token_refresh(self, request):
        serializer = TokenRefreshInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            return Response(
                {"access": str(refresh.access_token)},
                status=status.HTTP_200_OK,
            )
        except TokenError:
            return Response(
                {"detail": "Token is invalid or expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

    @password_reset_request_schema
    def password_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(serializer.validated_data["email"])
        return Response(
            {
                "detail": (
                    "If this email is registered, "
                    "a password reset link has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )

    @password_reset_confirm_schema
    def password_reset_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.confirm_password_reset(
            token_value=str(serializer.validated_data["token"]),
            new_password=serializer.validated_data["new_password"],
        )
        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class UserViewSet(ViewSet):
    """Handles user profile retrieval/update and operator-level user management."""

    _PROFILE_ACTIONS = frozenset({"retrieve_profile", "update_profile", "update_fcm_token"})

    def get_permissions(self):
        if self.action in self._PROFILE_ACTIONS:
            return [IsAuthenticated()]
        return [IsOperatorOrSuperAdmin()]

    @profile_retrieve_schema
    def retrieve_profile(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @profile_update_schema
    def update_profile(self, request):
        serializer = UserProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_user_profile(request.user, serializer.validated_data)
        return Response(
            UserProfileSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )

    @user_block_schema
    def block(self, request, pk: int):
        user = get_object_or_404(User, pk=pk)
        services.set_user_active_status(user, request.user, is_active=False)
        return Response(
            {"detail": "User has been blocked."},
            status=status.HTTP_200_OK,
        )

    @user_activate_schema
    def activate(self, request, pk: int):
        user = get_object_or_404(User, pk=pk)
        services.set_user_active_status(user, request.user, is_active=True)
        return Response(
            {"detail": "User has been activated."},
            status=status.HTTP_200_OK,
        )

    @fcm_token_schema
    def update_fcm_token(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.save_fcm_token(request.user, serializer.validated_data["fcm_token"])
        return Response({"detail": "FCM token saved."}, status=status.HTTP_200_OK)

    @user_list_schema
    def list_users(self, request):
        qs = User.objects.all()
        role = request.query_params.get("role")
        is_active_param = request.query_params.get("is_active")
        search = request.query_params.get("search")

        if role:
            qs = qs.filter(role=role)
        if is_active_param is not None:
            qs = qs.filter(is_active=is_active_param.lower() in ("true", "1", "yes"))
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        paginator = UserListPagination()
        page = paginator.paginate_queryset(qs.order_by("-date_joined"), request)
        if page is not None:
            return paginator.get_paginated_response(
                UserListSerializer(page, many=True).data
            )
        return Response(UserListSerializer(qs, many=True).data)
