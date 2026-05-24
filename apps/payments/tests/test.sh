#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Payments API  |  Manual endpoint test script
#
# Prerequisites:
#   - Server running at BASE (default: http://localhost:8000)
#   - jq installed
#   - Driver account: john_driver / NewStrongPass2!
#   - Operator account: op_user / OperatorPass1!
#   - PAYMENT_PROVIDER=mock (default for local dev)
#
# Run a ride first to get a completed ride, then test payment endpoints.
# =============================================================================

BASE=http://localhost:8000

# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  obtain tokens
# ─────────────────────────────────────────────────────────────────────────────

DRIVER_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}')
echo "$DRIVER_RESPONSE" | jq
DRIVER_ACCESS=$(echo "$DRIVER_RESPONSE" | jq -r '.access')

OP_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "op_user", "password": "OperatorPass1!"}')
OP_ACCESS=$(echo "$OP_RESPONSE" | jq -r '.access')


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  end any existing active ride so we start from a clean state
# ─────────────────────────────────────────────────────────────────────────────

EXISTING_ACTIVE=$(curl -s $BASE/api/rides/active/ \
  -H "Authorization: Bearer $DRIVER_ACCESS")
EXISTING_RIDE_ID=$(echo "$EXISTING_ACTIVE" | jq -r '.id // empty')
if [ -n "$EXISTING_RIDE_ID" ]; then
  echo "Ending existing active ride: $EXISTING_RIDE_ID"
  curl -s -X POST $BASE/api/rides/$EXISTING_RIDE_ID/end/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $DRIVER_ACCESS" \
    -d '{"end_latitude": 40.415000, "end_longitude": 49.871000}' > /dev/null
fi


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  complete a ride to charge against
# ─────────────────────────────────────────────────────────────────────────────

VEHICLE_RESPONSE=$(curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "scooter",
    "battery_level": 90,
    "latitude": 40.409264,
    "longitude": 49.867092
  }')
VEHICLE_ID=$(echo "$VEHICLE_RESPONSE" | jq -r '.id')
echo "Vehicle ID: $VEHICLE_ID"

START_RESPONSE=$(curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"start_latitude\": 40.409264,
    \"start_longitude\": 49.867092
  }")
RIDE_ID=$(echo "$START_RESPONSE" | jq -r '.id')
echo "Ride ID: $RIDE_ID"

END_RESPONSE=$(curl -s -X POST $BASE/api/rides/$RIDE_ID/end/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{
    "end_latitude": 40.415000,
    "end_longitude": 49.871000
  }')
echo "$END_RESPONSE" | jq
echo "Ride completed. payment_amount: $(echo "$END_RESPONSE" | jq '.payment_amount')"


# ─────────────────────────────────────────────────────────────────────────────
# 1. LIST PAYMENT METHODS (empty)
# Expected: 200 OK  —  empty array
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 1. LIST PAYMENT METHODS (empty) ==="
curl -s $BASE/api/payments/methods/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 2. ADD A PAYMENT METHOD (mock provider — token becomes pm_id)
# Expected: 201 Created  —  method with last4, brand, is_default=true
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 2. ADD PAYMENT METHOD ==="
PM_RESPONSE=$(curl -s -X POST $BASE/api/payments/methods/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"token": "tok_test_4242"}')
echo "$PM_RESPONSE" | jq
PM_ID=$(echo "$PM_RESPONSE" | jq -r '.id')
echo "Payment Method ID: $PM_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 3. LIST PAYMENT METHODS (one result, is_default=true)
# Expected: 200 OK  —  array with one method
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 3. LIST PAYMENT METHODS (one result) ==="
curl -s $BASE/api/payments/methods/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 4. ADD A SECOND PAYMENT METHOD (not default)
# Expected: 201 Created  —  is_default=false
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 4. ADD SECOND PAYMENT METHOD ==="
PM2_RESPONSE=$(curl -s -X POST $BASE/api/payments/methods/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"token": "tok_test_5353"}')
echo "$PM2_RESPONSE" | jq
PM2_ID=$(echo "$PM2_RESPONSE" | jq -r '.id')


# ─────────────────────────────────────────────────────────────────────────────
# 5. SET SECOND METHOD AS DEFAULT
# Expected: 200 OK  —  is_default=true for PM2
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 5. SET DEFAULT PAYMENT METHOD ==="
curl -s -X POST $BASE/api/payments/methods/$PM2_ID/set-default/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 6. CHARGE FOR THE COMPLETED RIDE (uses default method)
# Expected: 201 Created  —  status=completed, amount matches ride.payment_amount
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 6. CHARGE FOR RIDE ==="
PAYMENT_RESPONSE=$(curl -s -X POST $BASE/api/payments/charge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{\"ride_id\": \"$RIDE_ID\"}")
echo "$PAYMENT_RESPONSE" | jq
PAYMENT_ID=$(echo "$PAYMENT_RESPONSE" | jq -r '.id')
echo "Payment ID: $PAYMENT_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 7. CHARGE SAME RIDE AGAIN  →  should fail (payment already exists)
# Expected: 400 Bad Request  —  "A payment already exists for this ride."
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 7. DUPLICATE CHARGE (should fail) ==="
curl -s -X POST $BASE/api/payments/charge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{\"ride_id\": \"$RIDE_ID\"}" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. PAYMENT HISTORY
# Expected: 200 OK  —  paginated list with the payment above
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 8. PAYMENT HISTORY ==="
curl -s "$BASE/api/payments/?page=1&page_size=5" \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 9. VALIDATE A PROMO CODE (no fare preview)
# First create one via Django shell, then validate via API
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 9. PROMO CODE SETUP (Django shell) ==="
PROMO_SETUP=$(cd /home/mammadov/Documents/workspace/swift-ops && \
  DJANGO_SETTINGS_MODULE=config.settings.local \
  uv run --env-file .envs/.local/.env python manage.py shell -c "
from apps.payments.models import PromoCode
from django.utils import timezone
import datetime
PromoCode.objects.filter(code='TEST10').delete()
p = PromoCode.objects.create(
    code='TEST10',
    discount_type='percentage',
    discount_value=10,
    valid_from=timezone.now() - datetime.timedelta(hours=1),
    is_active=True,
)
print('Created:', p.code)
" 2>/dev/null)
echo "$PROMO_SETUP"

echo ""
echo "=== 9b. VALIDATE PROMO CODE (with fare preview) ==="
curl -s -X POST $BASE/api/payments/promo/validate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{
    "code": "TEST10",
    "distance_km": "0.718",
    "duration_seconds": 300
  }' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 10. CHARGE NEW RIDE WITH PROMO CODE
# Expected: 201 Created  —  discount_amount > 0, amount < full fare
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 10. CHARGE WITH PROMO CODE ==="

VEHICLE2_RESPONSE=$(curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"type": "scooter", "battery_level": 80, "latitude": 40.409264, "longitude": 49.867092}')
VEHICLE2_ID=$(echo "$VEHICLE2_RESPONSE" | jq -r '.id')

curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{\"vehicle_id\": \"$VEHICLE2_ID\", \"start_latitude\": 40.409264, \"start_longitude\": 49.867092}" \
  > /dev/null

RIDE2_ID=$(curl -s $BASE/api/rides/active/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq -r '.id')

curl -s -X POST $BASE/api/rides/$RIDE2_ID/end/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"end_latitude": 40.415, "end_longitude": 49.871}' > /dev/null

PAYMENT2_RESPONSE=$(curl -s -X POST $BASE/api/payments/charge/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{\"ride_id\": \"$RIDE2_ID\", \"promo_code\": \"TEST10\"}")
echo "$PAYMENT2_RESPONSE" | jq
# Use whichever payment ID we have for retry test
if [ -z "$PAYMENT_ID" ] || [ "$PAYMENT_ID" = "null" ]; then
  PAYMENT_ID=$(echo "$PAYMENT2_RESPONSE" | jq -r '.id')
fi


# ─────────────────────────────────────────────────────────────────────────────
# 11. VALIDATE USED PROMO CODE  →  should fail (already used)
# Expected: 400 Bad Request
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 11. VALIDATE USED PROMO CODE (should fail) ==="
curl -s -X POST $BASE/api/payments/promo/validate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"code": "TEST10"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 12. RETRY A NON-FAILED PAYMENT  →  should fail
# Expected: 400 Bad Request  —  "Only failed payments can be retried."
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 12. RETRY COMPLETED PAYMENT (should fail) ==="
curl -s -X POST $BASE/api/payments/$PAYMENT_ID/retry/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 13. DELETE PAYMENT METHOD
# Expected: 204 No Content
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 13. DELETE PAYMENT METHOD ==="
curl -s -X DELETE $BASE/api/payments/methods/$PM_ID/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" -w "HTTP %{http_code}\n"


# ─────────────────────────────────────────────────────────────────────────────
# 14. LIST PAYMENT METHODS (only PM2 remains)
# Expected: 200 OK  —  one method
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 14. LIST PAYMENT METHODS (one remains) ==="
curl -s $BASE/api/payments/methods/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 15. VALIDATE INVALID PROMO CODE  →  should fail
# Expected: 400 Bad Request
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 15. INVALID PROMO CODE ==="
curl -s -X POST $BASE/api/payments/promo/validate/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"code": "DOESNOTEXIST"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 16. UNAUTHENTICATED REQUEST  →  should fail
# Expected: 401 Unauthorized
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 16. UNAUTHENTICATED ==="
curl -s $BASE/api/payments/ | jq


# ─────────────────────────────────────────────────────────────────────────────
# 17. OPERATOR TRIES TO USE PAYMENT ENDPOINT  →  should fail
# Expected: 403 Forbidden
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 17. OPERATOR ACCESS DENIED ==="
curl -s $BASE/api/payments/methods/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq
