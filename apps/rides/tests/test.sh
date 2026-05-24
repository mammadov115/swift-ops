#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Rides API  |  Manual endpoint test script
#
# Prerequisites:
#   - Server running at BASE (default: http://localhost:8000)
#   - jq installed  (brew install jq / apt install jq)
#   - Operator account: op_user / OperatorPass1!
#   - Driver account:   john_driver / NewStrongPass2!
#   - At least one AVAILABLE vehicle in the DB
#     Create one if needed:
#
#       curl -s -X POST $BASE/api/vehicles/ \
#         -H "Content-Type: application/json" \
#         -H "Authorization: Bearer $OP_ACCESS" \
#         -d '{"type":"scooter","battery_level":85,"latitude":40.4093,"longitude":49.8671}' | jq
#
# =============================================================================

BASE=http://localhost:8000


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  obtain tokens
# ─────────────────────────────────────────────────────────────────────────────

OP_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "op_user", "password": "OperatorPass1!"}')
echo "$OP_RESPONSE" | jq
OP_ACCESS=$(echo "$OP_RESPONSE" | jq -r '.access')

DRIVER_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}')
echo "$DRIVER_RESPONSE" | jq
DRIVER_ACCESS=$(echo "$DRIVER_RESPONSE" | jq -r '.access')


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  create a vehicle for the ride tests
# ─────────────────────────────────────────────────────────────────────────────
VEHICLE_RESPONSE=$(curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "scooter",
    "battery_level": 85,
    "latitude": 40.409264,
    "longitude": 49.867092
  }')
echo "$VEHICLE_RESPONSE" | jq
VEHICLE_ID=$(echo "$VEHICLE_RESPONSE" | jq -r '.id')
echo "Vehicle ID: $VEHICLE_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 1. START A RIDE
# Expected: 201 Created  —  ride in status "active", ended_at/end coords null
# ─────────────────────────────────────────────────────────────────────────────
START_RESPONSE=$(curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"start_latitude\": 40.409264,
    \"start_longitude\": 49.867092
  }")
echo "$START_RESPONSE" | jq
RIDE_ID=$(echo "$START_RESPONSE" | jq -r '.id')
echo "Ride ID: $RIDE_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 2. GET ACTIVE RIDE
# Expected: 200 OK  —  same ride, status "active"
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/rides/active/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 3. CONCURRENT RIDE ATTEMPT (same vehicle, same driver)
# Expected: 400  —  "You already have an active ride."
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"start_latitude\": 40.409264,
    \"start_longitude\": 49.867092
  }" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 4. VEHICLE IS NO LONGER AVAILABLE (status changed to "rented")
# Expected: 200  —  vehicle.status == "rented"
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/vehicles/$VEHICLE_ID/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq '.status'


# ─────────────────────────────────────────────────────────────────────────────
# 5. END THE RIDE
# Expected: 200 OK  —  status "completed", duration/distance/payment populated
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/rides/$RIDE_ID/end/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{
    "end_latitude": 40.415000,
    "end_longitude": 49.871000
  }' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 6. VEHICLE IS AVAILABLE AGAIN
# Expected: 200  —  vehicle.status == "available"
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/vehicles/$VEHICLE_ID/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq '.status'


# ─────────────────────────────────────────────────────────────────────────────
# 7. ACTIVE RIDE RETURNS 404 (no active ride)
# Expected: 404 Not Found
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/rides/active/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. RIDE HISTORY
# Expected: 200  —  paginated list with the completed ride
# ─────────────────────────────────────────────────────────────────────────────
curl -s "$BASE/api/rides/?page=1&page_size=5" \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

# 9. OPERATOR TRIES TO START A RIDE  →  should fail
# Expected: 403 Forbidden
curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d "{
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"start_latitude\": 40.409264,
    \"start_longitude\": 49.867092
  }" | jq


# 10. UNAUTHENTICATED REQUEST  →  should fail
# Expected: 401 Unauthorized
curl -s $BASE/api/rides/ | jq


# 11. END AN ALREADY-COMPLETED RIDE  →  should fail
# Expected: 400  —  "Only active rides can be ended."
curl -s -X POST $BASE/api/rides/$RIDE_ID/end/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"end_latitude": 40.416, "end_longitude": 49.872}' | jq


# 12. START RIDE ON UNAVAILABLE VEHICLE  →  should fail
# Expected: 400  —  "Vehicle is not available for rental."
curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"start_latitude\": 40.409264,
    \"start_longitude\": 49.867092
  }" | jq


# 13. START RIDE ON NON-EXISTENT VEHICLE  →  should fail
# Expected: 400  —  "Vehicle not found or deactivated."
curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{
    "vehicle_id": "00000000-0000-0000-0000-000000000000",
    "start_latitude": 40.409264,
    "start_longitude": 49.867092
  }' | jq


# 14. INVALID COORDINATES  →  should fail
# Expected: 400 Bad Request
curl -s -X POST $BASE/api/rides/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d "{
    \"vehicle_id\": \"$VEHICLE_ID\",
    \"start_latitude\": 999,
    \"start_longitude\": 49.867092
  }" | jq
