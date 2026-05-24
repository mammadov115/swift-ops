#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Reports API  |  Manual endpoint test script
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
#
# Reports are pre-computed by Celery Beat tasks. To seed data manually before
# testing, run the task directly (see §SETUP below).
# =============================================================================

BASE=http://localhost:8000


# ─────────────────────────────────────────────────────────────────────────────
# SETUP  –  obtain tokens for both roles
# ─────────────────────────────────────────────────────────────────────────────

# Operator token (required for all report endpoints)
OP_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "op_user", "password": "OperatorPass1!"}')
echo "$OP_RESPONSE" | jq
OP_ACCESS=$(echo "$OP_RESPONSE" | jq -r '.access')

# Driver token (should be rejected by report endpoints with 403)
DRIVER_RESPONSE=$(curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}')
echo "$DRIVER_RESPONSE" | jq
DRIVER_ACCESS=$(echo "$DRIVER_RESPONSE" | jq -r '.access')

# ─────────────────────────────────────────────────────────────────────────────
# SEED  –  trigger report computation for today and yesterday via Django shell
#
#   uv run --env-file .envs/.local/.env \
#     python manage.py shell --settings=config.settings.local -c "
#   from apps.reports.tasks import compute_daily_report_task, compute_zone_activity_task
#   compute_daily_report_task.apply()
#   compute_zone_activity_task.apply()"
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# 1. DAILY STATS  –  no date range (defaults to today)
# Expected: 200 OK  —  paginated list of DailyReport objects
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/reports/daily-stats/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 2. DAILY STATS  –  with explicit date range
# Expected: 200 OK  —  filtered list for the given range
# ─────────────────────────────────────────────────────────────────────────────
curl -s "$BASE/api/reports/daily-stats/?start_date=2026-01-01&end_date=2026-05-24" \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 3. DAILY STATS  –  bad date format
# Expected: 400 Bad Request
#   {"detail": "Invalid date format. Use YYYY-MM-DD."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s "$BASE/api/reports/daily-stats/?start_date=not-a-date" \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 4. DAILY STATS  –  start_date after end_date
# Expected: 400 Bad Request
#   {"detail": "start_date must not be after end_date."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s "$BASE/api/reports/daily-stats/?start_date=2026-06-01&end_date=2026-05-01" \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 5. REVENUE REPORT  –  no date range (defaults to today)
# Expected: 200 OK  —  paginated list with date / total_revenue / completed_rides
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/reports/revenue/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 6. REVENUE REPORT  –  with explicit date range
# Expected: 200 OK
# ─────────────────────────────────────────────────────────────────────────────
curl -s "$BASE/api/reports/revenue/?start_date=2026-01-01&end_date=2026-05-24" \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 7. ZONE ACTIVITY REPORT  –  no date range (defaults to today)
# Expected: 200 OK  —  paginated list with date / zone / rides_started / rides_ended
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/reports/zone-activity/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. ZONE ACTIVITY REPORT  –  with explicit date range
# Expected: 200 OK
# ─────────────────────────────────────────────────────────────────────────────
curl -s "$BASE/api/reports/zone-activity/?start_date=2026-01-01&end_date=2026-05-24" \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# PERMISSION CHECKS
# ─────────────────────────────────────────────────────────────────────────────

# 9. DRIVER ATTEMPTS TO ACCESS DAILY STATS
# Expected: 403 Forbidden
curl -s $BASE/api/reports/daily-stats/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq

# 10. DRIVER ATTEMPTS TO ACCESS REVENUE REPORT
# Expected: 403 Forbidden
curl -s $BASE/api/reports/revenue/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq

# 11. DRIVER ATTEMPTS TO ACCESS ZONE ACTIVITY
# Expected: 403 Forbidden
curl -s $BASE/api/reports/zone-activity/ \
  -H "Authorization: Bearer $DRIVER_ACCESS" | jq

# 12. UNAUTHENTICATED REQUEST
# Expected: 401 Unauthorized
curl -s $BASE/api/reports/daily-stats/ | jq
