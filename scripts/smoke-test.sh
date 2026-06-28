#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# Smoke test — post-deployment verification
# Usage:
#   ./scripts/smoke-test.sh                         # uses defaults
#   BACKEND_URL=https://smartstock-api.railway.app \
#   FRONTEND_URL=https://smart-stock-dev.vercel.app \
#   HEALTH_SECRET=mysecret \
#     ./scripts/smoke-test.sh
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"
HEALTH_SECRET="${HEALTH_SECRET:-}"

PASS=0
FAIL=0

pass() { printf "  \033[32m✓\033[0m %s\n" "$1"; PASS=$((PASS + 1)); }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; FAIL=$((FAIL + 1)); }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " SmartStock AI — Post-Deploy Smoke Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo " Backend  : $BACKEND_URL"
echo " Frontend : $FRONTEND_URL"
echo ""

# ── 1. Backend liveness ──────────────────────────────────────────────
echo "── Backend ──"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health/live/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    pass "Liveness probe (/api/health/live/) → 200"
else
    fail "Liveness probe → $HTTP_CODE (expected 200)"
fi

# ── 2. Backend readiness ─────────────────────────────────────────────
READY_ARGS=(-s -w "%{http_code}")
if [ -n "$HEALTH_SECRET" ]; then
    READY_ARGS+=(-H "X-Health-Secret: $HEALTH_SECRET")
fi

READY_CODE=$(curl "${READY_ARGS[@]}" -o /tmp/smoke_ready_body "$BACKEND_URL/api/health/ready/" 2>/dev/null || echo "000")
READY_BODY=$(cat /tmp/smoke_ready_body 2>/dev/null || echo "")

if [ "$READY_CODE" = "200" ]; then
    pass "Readiness probe (/api/health/ready/) → 200"
elif [ "$READY_CODE" = "503" ]; then
    fail "Readiness probe → 503 (degraded — check db/redis)"
elif [ "$READY_CODE" = "403" ]; then
    fail "Readiness probe → 403 (set HEALTH_SECRET or access from internal network)"
else
    fail "Readiness probe → $READY_CODE"
fi

# ── 3. Backend API root (unauthenticated) ────────────────────────────
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/" 2>/dev/null || echo "000")
if [ "$API_CODE" = "200" ] || [ "$API_CODE" = "404" ]; then
    pass "API root reachable ($API_CODE)"
else
    fail "API root unreachable → $API_CODE"
fi

# ── 4. Frontend ──────────────────────────────────────────────────────
echo ""
echo "── Frontend ──"

FE_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/" 2>/dev/null || echo "000")
if [ "$FE_CODE" = "200" ]; then
    pass "Homepage (/) → 200"
else
    fail "Homepage → $FE_CODE (expected 200)"
fi

# Check that the HTML contains the expected SPA entry
FE_BODY=$(curl -s "$FRONTEND_URL/" 2>/dev/null || echo "")
if echo "$FE_BODY" | grep -q "SmartStock\|<div id=\"root\""; then
    pass "SPA shell loaded (contains expected markup)"
else
    fail "SPA shell missing — response may not be the frontend"
fi

# Check API proxy works through frontend (if applicable)
PROXY_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/api/health/live/" 2>/dev/null || echo "000")
if [ "$PROXY_CODE" = "200" ]; then
    pass "API proxy (/api/health/live/ via frontend) → 200"
elif [ "$PROXY_CODE" = "404" ] || [ "$PROXY_CODE" = "502" ]; then
    # Expected if Vercel rewrites to external backend
    pass "API proxy → $PROXY_CODE (external backend — expected)"
else
    fail "API proxy → $PROXY_CODE"
fi

# ── Summary ──────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL=$((PASS + FAIL))
printf " Results: \033[32m%d passed\033[0m, \033[31m%d failed\033[0m, %d total\n" "$PASS" "$FAIL" "$TOTAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
