#!/usr/bin/env bash
# Usage: bash apps/reports/tests/test.sh
# Requires a running server on PORT (default 8000) and valid operator creds.

BASE="${BASE_URL:-http://localhost:8000}"
EMAIL="${OPERATOR_EMAIL:-operator@example.com}"
PASSWORD="${OPERATOR_PASSWORD:-password}"

echo "=== Reports API tests ==="
echo "Server: $BASE"

# --- auth -----------------------------------------------------------
TOKEN=$(curl -s -X POST "$BASE/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access',''))")

if [ -z "$TOKEN" ]; then
  echo "FAIL: could not obtain access token"
fi
echo "Token: ${TOKEN:0:20}..."
AUTH="Authorization: Bearer $TOKEN"

# --- 1. daily stats (no data yet, expect 200 empty list) ------------
echo ""
echo "--- GET /api/reports/daily-stats/ ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "$AUTH" "$BASE/api/reports/daily-stats/"

# with date range
echo "--- GET /api/reports/daily-stats/?start_date=2025-01-01&end_date=2025-01-31 ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "$AUTH" "$BASE/api/reports/daily-stats/?start_date=2025-01-01&end_date=2025-01-31"

# bad date format
echo "--- GET /api/reports/daily-stats/?start_date=bad (expect 400) ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "$AUTH" "$BASE/api/reports/daily-stats/?start_date=bad"

# start > end (expect 400)
echo "--- GET /api/reports/daily-stats/?start_date=2025-06-10&end_date=2025-06-01 (expect 400) ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "$AUTH" "$BASE/api/reports/daily-stats/?start_date=2025-06-10&end_date=2025-06-01"

# --- 2. revenue ------------------------------------------------------
echo ""
echo "--- GET /api/reports/revenue/ ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "$AUTH" "$BASE/api/reports/revenue/"

# --- 3. zone activity -----------------------------------------------
echo ""
echo "--- GET /api/reports/zone-activity/ ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -H "$AUTH" "$BASE/api/reports/zone-activity/"

# --- 4. unauthenticated request (expect 401) ------------------------
echo ""
echo "--- GET /api/reports/daily-stats/ (no token, expect 401) ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BASE/api/reports/daily-stats/"

echo ""
echo "=== Done ==="
