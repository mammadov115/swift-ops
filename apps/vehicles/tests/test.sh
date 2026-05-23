#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Vehicles API  |  Manual endpoint test script
#
# Prerequisites:
#   - Server running at BASE (default: http://localhost:8000)
#   - jq installed  (brew install jq / apt install jq)
#   - An operator account already exists (see accounts/tests/test.sh §10)
#     OR create one via:
#
#       uv run --env-file .envs/.local/.env \
#         python manage.py shell --settings=config.settings.local -c "
#       from apps.accounts.models import User
#       User.objects.create_user(
#           username='op_user', email='op@example.com',
#           password='OperatorPass1!', role='operator', is_email_verified=True)"
#
#   - A driver account (john_driver / NewStrongPass2!) from accounts test.sh
# =============================================================================

BASE=http://localhost:8000


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  obtain tokens for both roles
# ─────────────────────────────────────────────────────────────────────────────

# Operator token (needed for create / status update / QR / deactivate)
OP_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "op_user", "password": "OperatorPass1!"}')
echo "$OP_RESPONSE" | jq
OP_ACCESS=$(echo "$OP_RESPONSE" | jq -r '.access')

# Driver token (read-only; should only see AVAILABLE vehicles)
DRIVER_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}')
echo "$DRIVER_RESPONSE" | jq
DRIVER_ACCESS=$(echo "$DRIVER_RESPONSE" | jq -r '.access')


# ─────────────────────────────────────────────────────────────────────────────
# 1. CREATE A VEHICLE
# Expected: 201 Created  —  full vehicle object; status defaults to "available"
# ─────────────────────────────────────────────────────────────────────────────
CREATE_RESPONSE=$(curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "scooter",
    "battery_level": 85,
    "latitude": "40.409264",
    "longitude": "49.867092",
    "zone": "downtown"
  }')
echo "$CREATE_RESPONSE" | jq

# Save the vehicle ID for subsequent calls
VEHICLE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
echo "Vehicle ID: $VEHICLE_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 2. CREATE A SECOND VEHICLE (will be used for deactivation test later)
# Expected: 201 Created
# ─────────────────────────────────────────────────────────────────────────────
SECOND_RESPONSE=$(curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "bicycle",
    "battery_level": 60,
    "latitude": "40.411000",
    "longitude": "49.870000",
    "zone": "uptown"
  }')
echo "$SECOND_RESPONSE" | jq
SECOND_ID=$(echo "$SECOND_RESPONSE" | jq -r '.id')


# ─────────────────────────────────────────────────────────────────────────────
# 3. LIST ALL VEHICLES (as operator)
# Expected: 200 OK  —  array with both vehicles
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/vehicles/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 4. LIST VEHICLES WITH FILTERS
# Expected: 200 OK  —  only scooters in downtown zone
# ─────────────────────────────────────────────────────────────────────────────
curl -s "$BASE/api/vehicles/?type=scooter&zone=downtown" \
  -H "Authorization: Bearer $OP_ACCESS" | jq

# Filter by status
curl -s "$BASE/api/vehicles/?status=available" \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 5. LIST VEHICLES AS DRIVER  (automatic filter: only AVAILABLE)
# Expected: 200 OK  —  only vehicles with status="available"
#   Even if other statuses exist, drivers see nothing else.
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/vehicles/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 6. RETRIEVE A SINGLE VEHICLE
# Expected: 200 OK  —  full vehicle detail object
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/vehicles/$VEHICLE_ID/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 7. ASSIGN QR CODE TO THE VEHICLE
# Expected: 200 OK  —  vehicle object now has qr_code set
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/vehicles/$VEHICLE_ID/qr/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"qr_code": "QR-SCT-001"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. UPDATE VEHICLE STATUS  –  available → rented  (valid transition)
# Expected: 200 OK  —  vehicle with status="rented"
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/vehicles/$VEHICLE_ID/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"status": "rented"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 9. INVALID STATUS TRANSITION  –  rented → maintenance  (forbidden)
# Expected: 400 Bad Request
#   {"detail": "Cannot transition from 'rented' to 'maintenance'. Allowed transitions: available."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/vehicles/$VEHICLE_ID/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"status": "maintenance"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 10. VALID CHAIN  –  rented → available → maintenance → retired
# Expected: each call returns 200 with updated status
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/vehicles/$VEHICLE_ID/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"status": "available"}' | jq '.status'

curl -s -X PATCH $BASE/api/vehicles/$VEHICLE_ID/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"status": "maintenance"}' | jq '.status'

curl -s -X PATCH $BASE/api/vehicles/$VEHICLE_ID/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"status": "retired"}' | jq '.status'


# ─────────────────────────────────────────────────────────────────────────────
# 11. TRANSITION FROM retired  →  should always fail
# Expected: 400 Bad Request
#   {"detail": "Cannot transition from 'retired' to 'available'. Allowed transitions: none."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/vehicles/$VEHICLE_ID/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"status": "available"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 12. DEACTIVATE THE SECOND VEHICLE  (soft delete)
# Expected: 204 No Content
# ─────────────────────────────────────────────────────────────────────────────
curl -s -o /dev/null -w "%{http_code}\n" \
  -X DELETE $BASE/api/vehicles/$SECOND_ID/ \
  -H "Authorization: Bearer $OP_ACCESS"


# ─────────────────────────────────────────────────────────────────────────────
# 13. DEACTIVATED VEHICLE NO LONGER APPEARS IN LIST
# Expected: 200  —  list does NOT include $SECOND_ID
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/vehicles/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq '.[].id'


# ─────────────────────────────────────────────────────────────────────────────
# 14. DEACTIVATED VEHICLE RETURNS 404 ON RETRIEVE
# Expected: 404 Not Found
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/vehicles/$SECOND_ID/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

# 15. DRIVER TRIES TO CREATE A VEHICLE  →  should fail
# Expected: 403 Forbidden
curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"type": "scooter", "battery_level": 90, "latitude": "40.4", "longitude": "49.8"}' | jq

# 16. DRIVER TRIES TO UPDATE STATUS  →  should fail
# Expected: 403 Forbidden
curl -s -X PATCH $BASE/api/vehicles/$VEHICLE_ID/status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"status": "available"}' | jq

# 17. ASSIGN DUPLICATE QR CODE  →  should fail
# Expected: 400 Bad Request  —  "This QR code is already assigned to another vehicle."
CREATE3=$(curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"type": "moped", "battery_level": 70, "latitude": "40.42", "longitude": "49.85"}')
THIRD_ID=$(echo "$CREATE3" | jq -r '.id')

curl -s -X POST $BASE/api/vehicles/$THIRD_ID/qr/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"qr_code": "QR-SCT-001"}' | jq

# 18. UNAUTHENTICATED REQUEST  →  should fail
# Expected: 401 Unauthorized
curl -s $BASE/api/vehicles/ | jq
