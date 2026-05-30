import uuid

import structlog

logger = structlog.get_logger(__name__)

# The header name we attach to every response so clients/operators can
# reference it when filing a bug report.
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    """
    Assign a unique UUID to every inbound request.

    The ID is:
    - Accepted from the incoming ``X-Request-ID`` header if the client sends
      one (useful for end-to-end tracing across services), otherwise generated
      fresh.
    - Stored on ``request.request_id`` so views can access it if needed.
    - Bound to structlog's context so every log line emitted during the
      request automatically includes ``request_id``.
    - Echoed back in the response ``X-Request-ID`` header so clients can
      correlate their request with server logs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = (
            request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        )
        request.request_id = request_id

        # Bind to structlog context — cleared automatically at request end
        # by django-structlog's RequestMiddleware (which runs after this one).
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request_id
        return response
