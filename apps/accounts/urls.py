from django.urls import path

from .views import AuthViewSet, UserViewSet

app_name = "accounts"


urlpatterns = [
    # Authentication
    path(
        "register/", AuthViewSet.as_view({"post": "register"}), name="register"
    ),
    path(
        "verify-email/",
        AuthViewSet.as_view({"post": "verify_email"}),
        name="verify-email",
    ),
    path("login/", AuthViewSet.as_view({"post": "login"}), name="login"),
    path(
        "token/refresh/",
        AuthViewSet.as_view({"post": "token_refresh"}),
        name="token-refresh",
    ),
    # Password reset
    path(
        "password-reset/",
        AuthViewSet.as_view({"post": "password_reset"}),
        name="password-reset",
    ),
    path(
        "password-reset/confirm/",
        AuthViewSet.as_view({"post": "password_reset_confirm"}),
        name="password-reset-confirm",
    ),
    # Profile
    path(
        "profile/",
        UserViewSet.as_view(
            {"get": "retrieve_profile", "patch": "update_profile"}
        ),
        name="profile",
    ),
    # User management
    path(
        "users/<int:pk>/block/",
        UserViewSet.as_view({"post": "block"}),
        name="user-block",
    ),
    path(
        "users/<int:pk>/activate/",
        UserViewSet.as_view({"post": "activate"}),
        name="user-activate",
    ),
]
