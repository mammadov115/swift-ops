#!/usr/bin/env bash
# =============================================================================
# SwiftOps – Accounts API  |  Manual endpoint test script
#
# Prerequisites:
#   - Server running at BASE (default: http://localhost:8000)
#   - jq installed  (brew install jq / apt install jq)
#
# Run individual sections by copying them into your terminal, or execute the
# whole file and fill in the <paste …> placeholders as you go.
# =============================================================================

BASE=http://localhost:8000

# ─────────────────────────────────────────────────────────────────────────────
# 1. REGISTER A NEW DRIVER ACCOUNT
# Expected: 201 Created
#   {"detail": "Registration successful. Please check your email to verify your account."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_driver",
    "email": "john@example.com",
    "password": "StrongPass1!",
    "first_name": "John",
    "last_name": "Driver"
  }' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 2. VERIFY EMAIL ADDRESS
# Expected: 200 OK
#   {"detail": "Email verified successfully."}
#
# Get the UUID token from the verification email sent to john@example.com
# and paste it below.
# ─────────────────────────────────────────────────────────────────────────────
VERIFY_TOKEN=<paste email verification token here>

curl -s -X POST $BASE/api/auth/verify-email/ \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$VERIFY_TOKEN\"}" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 3. LOGIN  →  save access + refresh tokens
# Expected: 200 OK
#   {"access": "eyJ...", "refresh": "eyJ..."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "StrongPass1!"}' | jq

ACCESS=<paste access token here>
REFRESH=<paste refresh token here>


# ─────────────────────────────────────────────────────────────────────────────
# 4. REFRESH ACCESS TOKEN
# Expected: 200 OK
#   {"access": "eyJ..."}  — a fresh short-lived access token
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$REFRESH\"}" | jq

# Update ACCESS with the new token if desired:
# ACCESS=<paste new access token here>


# ─────────────────────────────────────────────────────────────────────────────
# 5. RETRIEVE OWN PROFILE
# Expected: 200 OK
#   {id, username, email, first_name, last_name, role, is_email_verified, date_joined}
# ─────────────────────────────────────────────────────────────────────────────
curl -s $BASE/api/auth/profile/ \
  -H "Authorization: Bearer $ACCESS" | jq

# Save the driver's user ID for later block/activate tests:
DRIVER_ID=<paste user id here>


# ─────────────────────────────────────────────────────────────────────────────
# 6. UPDATE OWN PROFILE  (PATCH – only first_name / last_name)
# Expected: 200 OK  — full profile object with updated fields
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X PATCH $BASE/api/auth/profile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"first_name": "Johnny", "last_name": "Rider"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 7. REQUEST PASSWORD RESET
# Expected: 200 OK  — always, even if the email is not registered
#   {"detail": "If this email is registered, a password reset link has been sent."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 8. CONFIRM PASSWORD RESET
# Expected: 200 OK
#   {"detail": "Password has been reset successfully."}
#
# Get the UUID token from the password-reset email and paste it below.
# The token expires in 30 minutes and is single-use.
# ─────────────────────────────────────────────────────────────────────────────
RESET_TOKEN=<paste password reset token here>

curl -s -X POST $BASE/api/auth/password-reset/confirm/ \
  -H 'Content-Type: application/json' \
  -d '{"token": "'"$RESET_TOKEN"'", "new_password": "NewStrongPass2!"}' | jq

# ─────────────────────────────────────────────────────────────────────────────
# 9. LOGIN AGAIN WITH THE NEW PASSWORD  →  refresh tokens
# Expected: 200 OK  — tokens issued with updated credentials
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}' | jq


# =============================================================================
# USER MANAGEMENT  (requires operator or superadmin account)
#
# Create an operator/superadmin account via Django shell first:
#
  uv run --env-file .envs/.local/.env python manage.py shell --settings=config.settings.local -c "
  from apps.accounts.models import User
  User.objects.create_user(
      username='op_user',
      email='op@example.com',
      password='OperatorPass1!',
      role='operator',
      is_email_verified=True,
  )"
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# 10. LOGIN AS OPERATOR  →  save operator access token
# Expected: 200 OK  — {"access": "eyJ...", "refresh": "eyJ..."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "op_user", "password": "OperatorPass1!"}' | jq

OP_ACCESS=<paste operator access token here>


# ─────────────────────────────────────────────────────────────────────────────
# 11. BLOCK THE DRIVER ACCOUNT
# Expected: 200 OK
#   {"detail": "User has been blocked."}
# Operators can only block drivers. Superadmins can block anyone.
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/users/$DRIVER_ID/block/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# 12. VERIFY THE DRIVER CANNOT LOG IN WHILE BLOCKED
# Expected: 400 Bad Request
#   {"detail": "This account has been deactivated."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "NewStrongPass2!"}' | jq


# ─────────────────────────────────────────────────────────────────────────────
# 13. ACTIVATE THE DRIVER ACCOUNT
# Expected: 200 OK
#   {"detail": "User has been activated."}
# ─────────────────────────────────────────────────────────────────────────────
curl -s -X POST $BASE/api/auth/users/$DRIVER_ID/activate/ \
  -H "Authorization: Bearer $OP_ACCESS" | jq


# ─────────────────────────────────────────────────────────────────────────────
# EDGE CASES
# ─────────────────────────────────────────────────────────────────────────────

# 14. DUPLICATE REGISTRATION  →  should fail
# Expected: 400 Bad Request  — "A user with this email already exists."
curl -s -X POST $BASE/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_driver",
    "email": "john@example.com",
    "password": "StrongPass1!",
    "first_name": "John",
    "last_name": "Driver"
  }' | jq

# 15. LOGIN WITH WRONG PASSWORD  →  should fail
# Expected: 400 Bad Request  — {"detail": "Invalid credentials."}
curl -s -X POST $BASE/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john_driver", "password": "WrongPassword"}' | jq

# 16. PROFILE WITHOUT TOKEN  →  should fail
# Expected: 401 Unauthorized
curl -s $BASE/api/auth/profile/ | jq

# 17. EXPIRED / INVALID REFRESH TOKEN
# Expected: 401 Unauthorized  — {"detail": "Token is invalid or expired."}
curl -s -X POST $BASE/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "invalid.token.here"}' | jq
