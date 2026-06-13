#!/usr/bin/env bash
# =============================================================================
# SmartStock AI — Post-Deployment Smoke Test
# =============================================================================
# Usage:
#   ./scripts/smoke-test.sh https://smartstock-api.onrender.com
#
# Exit codes:
#   0  — all checks passed
#   1  — one or more checks failed
# =============================================================================
set -euo pipefail

BACKEND_URL="${1:?Usage: $0 <backend-url>}"
FAILED=0

pass() { echo "  ✓ $1"; }
fail() { echo "  ✗ $1"; FAILED=1; }

echo "============================================="
echo " SmartStock AI — Production Smoke Tests"
echo " Backend: ${BACKEND_URL}"
echo "============================================="
echo ""

# ---------------------------------------------------------------------------
# 1. Health check — must return 200 with connected database and redis
# ---------------------------------------------------------------------------
echo "[1/5] GET /api/health/"
HEALTH=$(curl -sf "${BACKEND_URL}/api/health/" 2>/dev/null || true)
if [ -z "$HEALTH" ]; then
  fail "Health endpoint unreachable or returned non-2xx"
else
  DB_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('database',''))" 2>/dev/null || true)
  REDIS_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('redis',''))" 2>/dev/null || true)
  SVC_STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || true)
  if [ "$SVC_STATUS" = "ok" ] && [ "$DB_STATUS" = "connected" ] && [ "$REDIS_STATUS" = "connected" ]; then
    pass "Health: status=ok, database=connected, redis=connected"
  else
    fail "Health unexpected: status=${SVC_STATUS} database=${DB_STATUS} redis=${REDIS_STATUS}"
  fi
fi

# ---------------------------------------------------------------------------
# 2. HTTP → HTTPS redirect
# ---------------------------------------------------------------------------
echo "[2/5] HTTP → HTTPS redirect"
HTTP_URL=$(echo "$BACKEND_URL" | sed 's|^https://|http://|')
REDIRECT_CODE=$(curl -so /dev/null -w "%{http_code}" -L --max-redirs 0 "$HTTP_URL" 2>/dev/null || true)
if [ "$REDIRECT_CODE" = "301" ] || [ "$REDIRECT_CODE" = "302" ] || [ "$REDIRECT_CODE" = "308" ]; then
  pass "HTTP redirects to HTTPS (HTTP ${REDIRECT_CODE})"
else
  # Some setups return 403 or similar — acceptable if HSTS header is present
  HSTS_HEADER=$(curl -sI "$BACKEND_URL" 2>/dev/null | grep -i strict-transport || true)
  if [ -n "$HSTS_HEADER" ]; then
    pass "HSTS header present (HTTP ${REDIRECT_CODE} — proxy handles redirect)"
  else
    fail "No HTTPS redirect or HSTS header (HTTP ${REDIRECT_CODE})"
  fi
fi

# ---------------------------------------------------------------------------
# 3. API docs (Swagger UI)
# ---------------------------------------------------------------------------
echo "[3/5] GET /api/docs/"
DOCS_CODE=$(curl -so /dev/null -w "%{http_code}" "${BACKEND_URL}/api/docs/" 2>/dev/null || true)
if [ "$DOCS_CODE" = "200" ]; then
  pass "Swagger UI accessible (HTTP 200)"
else
  fail "Swagger UI returned HTTP ${DOCS_CODE}"
fi

# ---------------------------------------------------------------------------
# 4. Authentication — login with test credentials (or verify endpoint exists)
# ---------------------------------------------------------------------------
echo "[4/5] POST /api/auth/login/"
AUTH_CODE=$(curl -so /dev/null -w "%{http_code}" \
  -X POST "${BACKEND_URL}/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"email":"nonexistent@test.com","password":"wrongpassword"}' \
  2>/dev/null || true)
# A 400/401 means the endpoint is live and validating — that's success
if [ "$AUTH_CODE" = "400" ] || [ "$AUTH_CODE" = "401" ]; then
  pass "Auth endpoint live and validating (HTTP ${AUTH_CODE})"
else
  fail "Auth endpoint returned unexpected HTTP ${AUTH_CODE}"
fi

# ---------------------------------------------------------------------------
# 5. HSTS header check
# ---------------------------------------------------------------------------
echo "[5/5] Security headers"
HEADERS=$(curl -sI "${BACKEND_URL}/api/health/" 2>/dev/null || true)
HSTS=$(echo "$HEADERS" | grep -i strict-transport || true)
CT=$(echo "$HEADERS" | grep -i content-type-options || true)
if [ -n "$HSTS" ]; then
  pass "Strict-Transport-Security header present"
else
  fail "Missing Strict-Transport-Security header"
fi

if [ -n "$CT" ]; then
  pass "X-Content-Type-Options header present"
else
  fail "Missing X-Content-Type-Options header"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
if [ "$FAILED" -eq 0 ]; then
  echo " All smoke tests PASSED"
else
  echo " Some smoke tests FAILED"
fi
echo "============================================="

exit "$FAILED"
