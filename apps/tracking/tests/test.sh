#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Tracking API  |  Manual endpoint test script
#
# Prerequisites:
#   - Server running at BASE via daphne (ASGI):
#       uv run --env-file .envs/.local/.env \
#         daphne -p 8000 config.asgi:application \
#         --settings config.settings.local
#   - Redis running locally (docker compose up -d redis)
#   - jq installed   (apt install jq / brew install jq)
#   - wscat installed  (npm install -g wscat)
#   - An operator account: op_user / OperatorPass1!
#   - A driver account:    john_driver / NewStrongPass2!
#   - At least one vehicle already created (run apps/vehicles/tests/test.sh first)
#
# Usage:
#   chmod +x apps/tracking/tests/test.sh
#   ./apps/tracking/tests/test.sh
# =============================================================================

BASE=http://localhost:8000
WS_BASE=ws://localhost:8000


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  obtain tokens and a vehicle ID
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

# Grab the first active vehicle ID from the list endpoint
VEHICLE_ID=$(curl -s $BASE/api/vehicles/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq -r '.[0].id')
echo "Using vehicle: $VEHICLE_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 1. INGEST A GPS EVENT  (operator)
# Expected: 200 OK  —  location payload with lat/lng/battery/timestamp
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 1. Ingest GPS event ==="
curl -s -X POST $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "lat": "40.409264",
    "lng": "49.867092",
    "battery": 78
  }' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 2. READ LAST KNOWN LOCATION  (any authenticated user)
# Expected: 200 OK  —  same payload as step 1
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 2. Read current location (operator) ==="
curl -s $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 3. READ LOCATION AS DRIVER  (read is allowed for all authenticated users)
# Expected: 200 OK
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 3. Read current location (driver) ==="
curl -s $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 4. INGEST MULTIPLE EVENTS  –  simulate vehicle moving
# Expected: each call returns 200 with updated coordinates
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 4. Simulate movement (3 GPS pings) ==="
for i in 1 2 3; do
  LAT="40.40$(shuf -i 1000-9999 -n 1)"
  LNG="49.86$(shuf -i 1000-9999 -n 1)"
  BAT=$((80 - i * 5))

  curl -s -X POST $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $OP_ACCESS" \
    -d "{\"lat\": \"$LAT\", \"lng\": \"$LNG\", \"battery\": $BAT}" | jq '.lat, .lng, .battery'
  sleep 0.3
done


# ─────────────────────────────────────────────────────────────────────────────
# 5. UNAUTHENTICATED GPS INGEST  →  should fail
# Expected: 401 Unauthorized
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 5. Unauthenticated ingest → 401 ==="
curl -s -X POST $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
  -H "Content-Type: application/json" \
  -d '{"lat": "40.0", "lng": "49.0", "battery": 50}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 6. DRIVER TRIES TO INGEST GPS  →  should fail
# Expected: 403 Forbidden
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 6. Driver ingest → 403 ==="
curl -s -X POST $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"lat": "40.0", "lng": "49.0", "battery": 50}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 7. INVALID GPS PAYLOAD  –  battery out of range, coords out of range
# Expected: 400 Bad Request  –  validation errors
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 7. Invalid payload → 400 ==="
curl -s -X POST $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"lat": "999.0", "lng": "49.0", "battery": 150}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. UNKNOWN VEHICLE ID  →  should fail
# Expected: 404 Not Found
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 8. Unknown vehicle → 404 ==="
FAKE_UUID="00000000-0000-0000-0000-000000000000"
curl -s -X POST $BASE/api/tracking/vehicles/$FAKE_UUID/location/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"lat": "40.0", "lng": "49.0", "battery": 50}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 9. NO LOCATION DATA YET  –  try a freshly created vehicle
# Expected: 404  –  "No location data available for this vehicle."
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 9. No location yet → 404 ==="
FRESH_VEHICLE=$(curl -s -X POST $BASE/api/vehicles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "bicycle",
    "battery_level": 90,
    "latitude": "40.41",
    "longitude": "49.87",
    "zone": "test-zone"
  }')
FRESH_ID=$(echo "$FRESH_VEHICLE" | jq -r '.id')
echo "Fresh vehicle ID: $FRESH_ID"

curl -s $BASE/api/tracking/vehicles/$FRESH_ID/location/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 10. WEBSOCKET  –  connect and receive the current location
#
# Requires wscat:  npm install -g wscat
#
# NOTE: wscat connects, receives one message (the stored location or
#       "connected" acknowledgement), then exits after 3 seconds.
#       In a real scenario the client stays connected and receives
#       a message every time a GPS POST arrives.
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 10. WebSocket connect – receive current location ==="
echo "Connecting to: $WS_BASE/ws/vehicles/$VEHICLE_ID/"
echo "(press Ctrl+C to stop, or wait for wscat timeout)"

# First ingest fresh coordinates so there is something to receive on connect
curl -s -X POST $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{"lat": "40.412000", "lng": "49.871000", "battery": 72}' > /dev/null

# Connect, wait 3 s for the initial push, then disconnect
wscat --connect "$WS_BASE/ws/vehicles/$VEHICLE_ID/" --wait 3 2>&1 || \
  echo "wscat not installed – skipping WebSocket test (npm install -g wscat)"


# ─────────────────────────────────────────────────────────────────────────────
# 11. WEBSOCKET + LIVE PUSH  –  connect first, then ingest a GPS event
#
# In one terminal run:
#   wscat --connect ws://localhost:8000/ws/vehicles/<VEHICLE_ID>/
#
# In a second terminal run (after substituting the vehicle UUID):
  curl -s -X POST http://localhost:8000/api/tracking/vehicles/<VEHICLE_ID>/location/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <OP_ACCESS>" \
    -d '{"lat": "40.415", "lng": "49.875", "battery": 65}'

# Expected: the first terminal immediately receives a location_update message.
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== 11. Manual live-push instructions ==="
echo "Terminal 1:  wscat --connect $WS_BASE/ws/vehicles/$VEHICLE_ID/"
echo "Terminal 2:  curl -s -X POST $BASE/api/tracking/vehicles/$VEHICLE_ID/location/ \\"
echo "               -H 'Content-Type: application/json' \\"
echo "               -H \"Authorization: Bearer \$OP_ACCESS\" \\"
echo "               -d '{\"lat\": \"40.415\", \"lng\": \"49.875\", \"battery\": 65}'"
echo ""
echo "You should see a location_update message arrive in Terminal 1 immediately."
