SPECTACULAR_SETTINGS = {
    "TITLE": "SwiftOps API",
    "DESCRIPTION": (
        "REST API for the SwiftOps ride-hailing platform.\n\n"
        "All error responses follow the shape:\n"
        "```json\n"
        '{\"error\": \"<code>\", \"message\": \"<human text>\", \"detail\": {}}\n'
        "```\n\n"
        "Every request carries a unique `X-Request-ID` header that can be "
        "used to trace logs."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Group endpoints by Django app label in the Swagger UI.
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]",
    "SORT_OPERATIONS": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_GENERATE_CHOICE_DESCRIPTION": False,
}
