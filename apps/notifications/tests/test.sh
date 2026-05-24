#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Notifications API  |  Manual endpoint test script
#
# Prerequisites:
#   - Server running at BASE via daphne (ASGI):
#       uv run --env-file .envs/.local/.env \
#         daphne -p 8000 config.asgi:application
#   - Redis running locally (docker compose up -d redis)
#   - jq installed   (apt install jq / brew install jq)
#   - wscat installed  (npm install -g wscat)
#   - Test users:
#       op_user / OperatorPass1!
#       john_driver / NewStrongPass2!
#
# Usage:
#   chmod +x apps/notifications/tests/test.sh
#   ./apps/notifications/tests/test.sh
# =============================================================================

set -euo pipefail
BASE=http://localhost:8000

# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
echo "=== Auth: obtain tokens ==="
OP_RESPONSE=$(curl -s -X POST "$BASE/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "op_user", "password": "OperatorPass1!"}')
OP_ACCESS=$(echo "$OP_RESPONSE" | jq -r '.access')
echo "Operator token: ${OP_ACCESS:0:30}..."

DRIVER_RESPONSE=$(curl -s -X POST "$BASE/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}')
DRIVER_ACCESS=$(echo "$DRIVER_RESPONSE" | jq -r '.access')
echo "Driver token: ${DRIVER_ACCESS:0:30}..."


# ─────────────────────────────────────────────────────────────────────────────
# 1. Register FCM token
# Expected: 200  {"detail": "FCM token saved."}
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 1. Register FCM token ==="
curl -s -X POST "$BASE/api/auth/profile/fcm-token/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"fcm_token": "test_fcm_token_abc123"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 2. List notifications (empty initially)
# Expected: 200  paginated list  { count: 0, results: [] }
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 2. List notifications (driver – empty) ==="
curl -s "$BASE/api/notifications/" \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 3. Create a test notification via Django shell and then list it
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 3. Seed a notification via management shell ==="
uv run --env-file .envs/.local/.env python manage.py shell \
  --settings=config.settings.local -c "
from django.contrib.auth import get_user_model
from apps.notifications import services
from apps.notifications.models import Notification
User = get_user_model()
driver = User.objects.get(username='john_driver')
n = services.create(
    user=driver,
    notification_type=Notification.Type.ZONE_VIOLATION,
    title='Zone Violation',
    body='Your vehicle entered a restricted zone.',
    data={'zone_id': 'test-zone'},
)
print('Created notification:', n.id)
"

echo ""
echo "=== 3b. List notifications (driver – should have 1) ==="
LIST_RESPONSE=$(curl -s "$BASE/api/notifications/" \
  -H "Authorization: Bearer $DRIVER_ACCESS")
echo "$LIST_RESPONSE" | jq
NOTIF_ID=$(echo "$LIST_RESPONSE" | jq -r '.results[0].id')
echo "Notification ID: $NOTIF_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Mark notification as read
# Expected: 200  {... "is_read": true, "read_at": "..."}
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 4. Mark notification as read ==="
curl -s -X PATCH "$BASE/api/notifications/$NOTIF_ID/" \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 5. Mark notification as read again (idempotent)
# Expected: 200  same response
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 5. Mark as read again (idempotent) ==="
curl -s -X PATCH "$BASE/api/notifications/$NOTIF_ID/" \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 6. Mark notification owned by someone else → 404
# Expected: 404
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 6. Mark another user's notification → 404 ==="
curl -s -X PATCH "$BASE/api/notifications/$NOTIF_ID/" \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 7. Unauthenticated list → 401
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 7. Unauthenticated list → 401 ==="
curl -s "$BASE/api/notifications/" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. WebSocket connection (requires wscat)
# ─────────────────────────────────────────────────────────────────────────────
if command -v wscat &>/dev/null; then
  echo ""
  echo "=== 8. WebSocket notification feed (connects, waits 3 s) ==="
  timeout 3 wscat -c "ws://localhost:8000/ws/notifications/" \
    -H "Authorization: Bearer $DRIVER_ACCESS" || true
else
  echo ""
  echo "=== 8. Skipped (wscat not installed) ==="
fi

echo ""
echo "=== All notification tests done ==="
