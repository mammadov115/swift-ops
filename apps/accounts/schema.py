from drf_spectacular.utils import OpenApiResponse, extend_schema

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    TokenResponseSerializer,
)

register_schema = extend_schema(
    summary="Register a new user",
    description="Creates a new user account. The account is immediately active.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description="Registration successful."),
        400: OpenApiResponse(
            description="Validation error (e.g. username or email already exists)."
        ),
    },
    tags=["Authentication"],
)

login_schema = extend_schema(
    summary="Login",
    description=(
        "Authenticates a user with username and password. "
        "Returns a JWT access token (60 min) and refresh token (7 days)."
    ),
    request=LoginSerializer,
    responses={
        200: TokenResponseSerializer,
        400: OpenApiResponse(
            description="Invalid credentials or inactive account."
        ),
    },
    tags=["Authentication"],
)
