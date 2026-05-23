from drf_spectacular.utils import OpenApiResponse, extend_schema

from .serializers import (
    AccessTokenResponseSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    TokenRefreshInputSerializer,
    TokenResponseSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)

register_schema = extend_schema(
    summary="Register a new user",
    description=(
        "Creates a new driver account. An email verification link is sent "
        "to the provided address. The account cannot be used until the email "
        "is verified."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description="Registration successful."),
        400: OpenApiResponse(
            description="Validation error (e.g. username or email already exists)."
        ),
    },
    tags=["Authentication"],
)

email_verification_schema = extend_schema(
    summary="Verify email address",
    description=(
        "Verifies a user's email using the UUID token sent during registration. "
        "The token is single-use and expires after 24 hours."
    ),
    request=EmailVerificationSerializer,
    responses={
        200: OpenApiResponse(description="Email verified successfully."),
        400: OpenApiResponse(description="Invalid or expired token."),
    },
    tags=["Authentication"],
)

login_schema = extend_schema(
    summary="Login",
    description=(
        "Authenticates a user with username and password. "
        "Returns a JWT access token (60 min) and refresh token (7 days). "
        "Requires email to be verified."
    ),
    request=LoginSerializer,
    responses={
        200: TokenResponseSerializer,
        400: OpenApiResponse(
            description="Invalid credentials, inactive account, or unverified email."
        ),
    },
    tags=["Authentication"],
)

token_refresh_schema = extend_schema(
    summary="Refresh access token",
    description=(
        "Returns a new JWT access token given a valid refresh token. "
        "The refresh token is not rotated."
    ),
    request=TokenRefreshInputSerializer,
    responses={
        200: AccessTokenResponseSerializer,
        401: OpenApiResponse(description="Token is invalid or expired."),
    },
    tags=["Authentication"],
)

profile_retrieve_schema = extend_schema(
    summary="Retrieve own profile",
    description="Returns the authenticated user's profile data.",
    responses={200: UserProfileSerializer},
    tags=["Profile"],
)

profile_update_schema = extend_schema(
    summary="Update own profile",
    description="Partially updates the authenticated user's first and/or last name.",
    request=UserProfileUpdateSerializer,
    responses={
        200: UserProfileSerializer,
        400: OpenApiResponse(description="Validation error."),
    },
    tags=["Profile"],
)

user_block_schema = extend_schema(
    summary="Block a user",
    description=(
        "Deactivates a user account. Requires operator or superadmin role. "
        "Operators can only block drivers; superadmins can block anyone."
    ),
    responses={
        200: OpenApiResponse(description="User has been blocked."),
        400: OpenApiResponse(description="Cannot block this account."),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="User not found."),
    },
    tags=["User Management"],
)

user_activate_schema = extend_schema(
    summary="Activate a user",
    description=(
        "Reactivates a previously blocked user account. "
        "Requires operator or superadmin role."
    ),
    responses={
        200: OpenApiResponse(description="User has been activated."),
        400: OpenApiResponse(description="Cannot activate this account."),
        403: OpenApiResponse(description="Permission denied."),
        404: OpenApiResponse(description="User not found."),
    },
    tags=["User Management"],
)

password_reset_request_schema = extend_schema(
    summary="Request password reset",
    description=(
        "Sends a password reset link to the provided email address if it belongs "
        "to an active, registered account. Always returns 200 to prevent user "
        "enumeration."
    ),
    request=PasswordResetRequestSerializer,
    responses={
        200: OpenApiResponse(
            description="Reset link sent (or silently ignored if email not found)."
        ),
    },
    tags=["Authentication"],
)

password_reset_confirm_schema = extend_schema(
    summary="Confirm password reset",
    description=(
        "Resets the user's password using the token received by email. "
        "The token expires after 30 minutes and can only be used once."
    ),
    request=PasswordResetConfirmSerializer,
    responses={
        200: OpenApiResponse(
            description="Password has been reset successfully."
        ),
        400: OpenApiResponse(
            description=(
                "Invalid or expired token, or password failed validation."
            )
        ),
    },
    tags=["Authentication"],
)
