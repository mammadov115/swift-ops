from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

# Maps DRF exception class names to short machine-readable error codes.
# Extend this dict if you add custom exception types.
_CODE_MAP: dict[type, str] = {
    exceptions.AuthenticationFailed: "authentication_failed",
    exceptions.NotAuthenticated: "not_authenticated",
    exceptions.PermissionDenied: "permission_denied",
    exceptions.NotFound: "not_found",
    exceptions.MethodNotAllowed: "method_not_allowed",
    exceptions.NotAcceptable: "not_acceptable",
    exceptions.UnsupportedMediaType: "unsupported_media_type",
    exceptions.Throttled: "throttled",
    exceptions.ValidationError: "validation_error",
}


def _extract_detail(exc: exceptions.APIException) -> dict | list | str:
    """
    Return a serialisable representation of the validation detail.

    DRF's `detail` attribute can be a string, a list, a dict, or nested
    structures of `ErrorDetail` objects. `exc.get_full_details()` converts
    all of that to plain Python structures with `message` and `code` keys,
    which is more useful for frontend consumers than raw ErrorDetail.
    """
    full = exc.get_full_details()
    # Unwrap the top-level `detail` key that DRF wraps non-dict errors in.
    if isinstance(full, dict) and set(full.keys()) == {"message", "code"}:
        return {}
    return full


def custom_exception_handler(exc, context):
    """
    Return every error in the shape:

        {"error": "<code>", "message": "<human text>", "detail": <extra>}

    This gives the frontend a single, predictable structure to handle
    regardless of which endpoint raised the error.

    Strategy
    --------
    1. Convert Django's Http404 / PermissionDenied / ValidationError to
       their DRF equivalents so we don't need separate handling.
    2. Call the default DRF handler (handles auth, throttling, etc.).
    3. Reshape the response into our standard envelope.
    """
    # --- Step 1: Convert Django-level exceptions ---
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

    # --- Step 2: Let DRF do its thing (sets WWW-Authenticate headers, etc.) ---
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception — let Django's 500 machinery take over.
        return None

    # --- Step 3: Reshape into our envelope ---
    api_exc: exceptions.APIException = exc  # type: ignore[assignment]
    error_code = _CODE_MAP.get(type(api_exc), "error")

    # `detail` may be a list (non-field errors) or dict (field errors).
    raw_detail = api_exc.detail  # type: ignore[union-attr]
    if isinstance(raw_detail, list) and len(raw_detail) == 1:
        message = str(raw_detail[0])
        detail: dict | list = {}
    elif isinstance(raw_detail, str):
        message = raw_detail
        detail = {}
    elif isinstance(raw_detail, dict) and "detail" in raw_detail and len(raw_detail) == 1:
        message = str(raw_detail["detail"])
        detail = {}
    else:
        # Field-level validation errors — preserve them in `detail`.
        message = _human_message(api_exc)
        detail = _serialise_detail(raw_detail)

    response.data = {
        "error": error_code,
        "message": message,
        "detail": detail,
    }
    return response


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _human_message(exc: exceptions.APIException) -> str:
    """Return a single human-readable sentence for the error."""
    if isinstance(exc.detail, dict):
        # e.g. ValidationError with field errors → list the first field
        first_key = next(iter(exc.detail))
        first_val = exc.detail[first_key]
        if isinstance(first_val, list) and first_val:
            return f"{first_key}: {first_val[0]}"
        return str(exc.detail)
    if isinstance(exc.detail, list) and exc.detail:
        return str(exc.detail[0])
    return str(exc.detail)


def _serialise_detail(detail) -> dict | list:
    """
    Recursively convert DRF ErrorDetail objects to plain strings so the
    response body is JSON-serialisable without any custom encoder.
    """
    if isinstance(detail, dict):
        return {k: _serialise_detail(v) for k, v in detail.items()}
    if isinstance(detail, list):
        return [_serialise_detail(v) for v in detail]
    return str(detail)
