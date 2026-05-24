from rest_framework.permissions import BasePermission


class IsOperatorOrSuperAdmin(BasePermission):
    """Grants access only to users with the 'operator' or 'superadmin' role."""

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role in ("operator", "superadmin")
        )


class IsDriver(BasePermission):
    """Grants access only to users with the 'driver' role."""

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "role")
            and request.user.role == "driver"
        )
