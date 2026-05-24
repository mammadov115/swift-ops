#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Zones API  |  Manual endpoint test script
#
# Prerequisites:
#   - Server running at BASE (default: http://localhost:8000)
#   - jq installed  (brew install jq / apt install jq)
#   - An operator account already exists, OR create one:
#
      uv run --env-file .envs/.local/.env \
        python manage.py shell --settings=config.settings.local -c "
      from apps.accounts.models import User
      User.objects.create_user(
          username='op_user', email='op@example.com',
          password='OperatorPass1!', role='operator', is_email_verified=True)"
#
#   - A driver account (john_driver / NewStrongPass2!) from accounts test.sh
# =============================================================================

BASE=http://localhost:8000


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  obtain tokens for both roles
# ─────────────────────────────────────────────────────────────────────────────

# Operator token (needed for create / update / deactivate)
OP_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "op_user", "password": "OperatorPass1!"}')
echo "$OP_RESPONSE" | jq
OP_ACCESS=$(echo "$OP_RESPONSE" | jq -r '.access')

# Driver token (read-only)
DRIVER_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}')
echo "$DRIVER_RESPONSE" | jq
DRIVER_ACCESS=$(echo "$DRIVER_RESPONSE" | jq -r '.access')


# ─────────────────────────────────────────────────────────────────────────────
# 1. CREATE A FORBIDDEN ZONE
# Expected: 201 Created  —  GeoJSON Feature with all properties
# ─────────────────────────────────────────────────────────────────────────────
CREATE_RESPONSE=$(curl -s -X POST $BASE/api/zones/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [49.800, 40.400],
        [49.900, 40.400],
        [49.900, 40.500],
        [49.800, 40.500],
        [49.800, 40.400]
      ]]
    },
    "properties": {
      "name": "Downtown Forbidden Zone",
      "zone_type": "forbidden"
    }
  }')
echo "$CREATE_RESPONSE" | jq

ZONE_ID=$(echo "$CREATE_RESPONSE" | jq -r '.properties.id // .id')
echo "Zone ID: $ZONE_ID"


# ─────────────────────────────────────────────────────────────────────────────
# 2. CREATE A NO-PARKING ZONE
# Expected: 201 Created
# ─────────────────────────────────────────────────────────────────────────────
SECOND_RESPONSE=$(curl -s -X POST $BASE/api/zones/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [49.850, 40.410],
        [49.870, 40.410],
        [49.870, 40.430],
        [49.850, 40.430],
        [49.850, 40.410]
      ]]
    },
    "properties": {
      "name": "Airport No-Parking Zone",
      "zone_type": "no_parking"
    }
  }')
echo "$SECOND_RESPONSE" | jq
SECOND_ID=$(echo "$SECOND_RESPONSE" | jq -r '.properties.id // .id')


# ─────────────────────────────────────────────────────────────────────────────
# 3. CREATE A SPEED-LIMITED ZONE
# Expected: 201 Created
# ─────────────────────────────────────────────────────────────────────────────
THIRD_RESPONSE=$(curl -s -X POST $BASE/api/zones/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [49.820, 40.420],
        [49.840, 40.420],
        [49.840, 40.440],
        [49.820, 40.440],
        [49.820, 40.420]
      ]]
    },
    "properties": {
      "name": "School Speed Zone",
      "zone_type": "speed_limited"
    }
  }')
echo "$THIRD_RESPONSE" | jq
THIRD_ID=$(echo "$THIRD_RESPONSE" | jq -r '.properties.id // .id')


# ─────────────────────────────────────────────────────────────────────────────
# 4. LIST ALL ZONES (as operator)
# Expected: 200 OK  —  GeoJSON FeatureCollection with all 3 zones
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/zones/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 5. LIST ZONES AS DRIVER  (read-only access)
# Expected: 200 OK  —  same FeatureCollection; drivers can read all active zones
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/zones/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 6. RETRIEVE A SINGLE ZONE
# Expected: 200 OK  —  GeoJSON Feature for the forbidden zone
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/zones/$ZONE_ID/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 7. PARTIAL UPDATE  –  rename the zone
# Expected: 200 OK  —  Feature with updated name, geometry unchanged
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/zones/$ZONE_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": null,
    "properties": {
      "name": "City Centre Forbidden Zone"
    }
  }' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. PARTIAL UPDATE  –  change zone type only
# Expected: 200 OK  —  zone_type updated to "parking_allowed"
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/zones/$SECOND_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": null,
    "properties": {
      "zone_type": "parking_allowed"
    }
  }' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 9. PARTIAL UPDATE  –  update geometry
# Expected: 200 OK  —  zone with a new polygon
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/zones/$THIRD_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [49.825, 40.425],
        [49.835, 40.425],
        [49.835, 40.435],
        [49.825, 40.435],
        [49.825, 40.425]
      ]]
    },
    "properties": {}
  }' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 10. DEACTIVATE THE THIRD ZONE  (soft delete)
# Expected: 204 No Content
# ─────────────────────────────────────────────────────────────────────────────
curl -s -o /dev/null -w "%{http_code}\n" \
  -X DELETE $BASE/api/zones/$THIRD_ID/ \
  -H "Authorization: Bearer $OP_ACCESS"


# ─────────────────────────────────────────────────────────────────────────────
# 11. DEACTIVATED ZONE NO LONGER APPEARS IN LIST
# Expected: 200  —  FeatureCollection does NOT include $THIRD_ID
# ─────────────────────────────────────────────────────────────────────────────
  curl -s $BASE/api/zones/ \
    -H "Authorization: Bearer $OP_ACCESS" | jq '[.features[].id]'


# ─────────────────────────────────────────────────────────────────────────────
# 12. DEACTIVATED ZONE RETURNS 404 ON RETRIEVE
# Expected: 404 Not Found
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/zones/$THIRD_ID/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

# 13. DRIVER TRIES TO CREATE A ZONE  →  should fail
# Expected: 403 Forbidden
curl -s -X POST $BASE/api/zones/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[49.8,40.4],[49.9,40.4],[49.9,40.5],[49.8,40.5],[49.8,40.4]]]
    },
    "properties": {"name": "Hack Zone", "zone_type": "forbidden"}
  }' | jq


# 14. DRIVER TRIES TO UPDATE A ZONE  →  should fail
# Expected: 403 Forbidden
curl -s -X PATCH $BASE/api/zones/$ZONE_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $DRIVER_ACCESS" \
  -d '{"type":"Feature","geometry":null,"properties":{"name":"Hacked"}}' | jq


# 15. DRIVER TRIES TO DEACTIVATE A ZONE  →  should fail
# Expected: 403 Forbidden
curl -s -o /dev/null -w "%{http_code}\n" \
  -X DELETE $BASE/api/zones/$ZONE_ID/ \
  -H "Authorization: Bearer $DRIVER_ACCESS"


# 16. INVALID zone_type  →  should fail
# Expected: 400 Bad Request
curl -s -X POST $BASE/api/zones/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[49.8,40.4],[49.9,40.4],[49.9,40.5],[49.8,40.5],[49.8,40.4]]]
    },
    "properties": {"name": "Bad Zone", "zone_type": "invalid_type"}
  }' | jq


# 17. MISSING geometry  →  should fail
# Expected: 400 Bad Request
curl -s -X POST $BASE/api/zones/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OP_ACCESS" \
  -d '{
    "type": "Feature",
    "geometry": null,
    "properties": {"name": "No Geometry Zone", "zone_type": "forbidden"}
  }' | jq


# 18. NON-EXISTENT ZONE  →  should fail
# Expected: 404 Not Found
curl -s $BASE/api/zones/00000000-0000-0000-0000-000000000000/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# 19. UNAUTHENTICATED REQUEST  →  should fail
# Expected: 401 Unauthorized
curl -s $BASE/api/zones/ | jq
