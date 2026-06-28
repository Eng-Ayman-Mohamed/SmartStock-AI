# Swagger/OpenAPI Documentation Report

## What Was Done

Completed `@extend_schema` / `@extend_schema_view` documentation coverage across all backend apps for drf-spectacular (Swagger UI at `GET /api/docs/`).

## Apps Modified

### 1. `apps/ai/views.py` — ConversationViewSet

**Before:** Zero `@extend_schema` decorators on any method. The ViewSet (not a ModelViewSet) had no serializer auto-discovery, so all 6 endpoints were invisible to Swagger.

**After:** Full `@extend_schema_view` covering:
- `list` — `ChatConversationListSerializer(many=True)` response, 401, 403
- `create` — `ChatConversationCreateSerializer` request, `ChatConversationDetailSerializer` response, 400, 401, 403, 422, with request example
- `retrieve` — `ChatConversationDetailSerializer` response, 401, 403, 404
- `partial_update` — `ChatConversationRenameSerializer` request, `ChatConversationDetailSerializer` response, 400, 401, 403, 404, 422, with request example
- `destroy` — 204, 401, 403, 404
- `messages` — Paginated `ChatMessageSerializer` response with pagination meta, 401, 403, 404

### 2. `apps/notifications/views.py` — NotificationViewSet + UnreadCountView

**Before:** Only bare `tags` and `summary` on list/retrieve. Custom actions (mark_read, mark_all_read, dismiss) had tags only. No response schemas, no error codes anywhere.

**After:** Full `@extend_schema_view` on all CRUD methods plus `@extend_schema` on all custom actions and `UnreadCountView`:
- CRUD methods use `NotificationListSerializer` / `NotificationSerializer`
- Custom actions document the `{'status': 'success'}` response shape and error codes 401, 403, 404
- UnreadCountView documents `{'count': int}` response

### 3. `apps/monitoring/views.py` — 6 Views

**Before:** No `@extend_schema` on any view. Also, the `monitoring` tag did not exist in `SPECTACULAR_SETTINGS.TAGS`.

**After:**
- Added `monitoring` tag to `config/settings/base.py` `SPECTACULAR_SETTINGS.TAGS`
- `MetricsView` — documented as Prometheus text/plain response, unauthenticated
- `DashboardBannersView` — inline serializer for banner items, 401
- `DismissBannerView` — success response, 401, 403, 404
- `AlertEventsView` — inline serializer for alert event items, 401
- `TriggerAlertEvaluationView` — dict response, 401, 403
- `EvaluationMetricsView` — inline serializer with precision/faithfulness fields, 401, 403

### 4. `apps/ingestion/views.py` — 4 Views

**Before:** InvoiceScanView, InvoiceScanConfirmView, InvoiceScanRejectView, and ChatStreamView had no `@extend_schema`.

**After:**
- `InvoiceScanView` — `InvoiceScanUploadSerializer` request, `InvoiceScanSerializer` response, error codes 400, 422, 501, 504
- `InvoiceScanConfirmView` — `InvoiceScanConfirmSerializer` request, `InvoiceScanSerializer` response, error codes 400, 403, 404, 409, 422
- `InvoiceScanRejectView` — no request body, `InvoiceScanSerializer` response, error codes 403, 404, 409
- `ChatStreamView` — `ChatSerializer` request, SSE text/event-stream response, request example, error codes 400, 404, 422

### 5. `apps/audit/views.py` — Query Parameters

**Before:** `AuditLogView` had response schemas but no documented query parameters. `AgentRunViewSet` had no documented `days` parameter.

**After:**
- `AuditLogView.get` — added `OpenApiParameter` docs for `user_id`, `created_after`, `created_before`
- `AgentRunViewSet.list` — added `OpenApiParameter` docs for `days` (1-365, default 7)

### 6. `config/settings/base.py`

Added `monitoring` tag to `SPECTACULAR_SETTINGS.TAGS`:
```python
{'name': 'monitoring', 'description': 'Dashboard banners, alerts, and evaluation metrics'},
```

## Pattern Used

Every view follows the same established pattern from the already-documented apps (inventory, authentication):

1. **ViewSets** → `@extend_schema_view` at class level with per-method `extend_schema(...)`
2. **APIViews** → `@extend_schema(...)` on the method
3. **Response schemas** → existing serializers where available, `inline_serializer` for ad-hoc response shapes
4. **Error codes** → `OpenApiResponse(response=ErrorResponseSerializer, description='...')` for 4xx/5xx
5. **Tags** → using the existing tag names from `SPECTACULAR_SETTINGS.TAGS`
6. **Examples** → `OpenApiExample` for request/response samples where helpful

## Verification

- `ruff check` — all modified files pass with 0 errors
- `python manage.py check` — 0 system check issues
- `python manage.py spectacular` — schema generates successfully with 0 errors
- Schema is valid OpenAPI 3.0.3

## Flow

```
Developer adds @extend_schema → drf-spectacular auto-generates schema.yaml
                                    ↓
Schema served at GET /api/schema/ (SpectacularAPIView)
                                    ↓
Swagger UI at GET /api/docs/ renders interactive docs
                                    ↓
Frontend devs / API consumers read request shapes, response shapes, error codes
```

## What's Still Pre-Existing (not addressed)

- 16 schema generation warnings (type hints on SerializerMethodField, untyped path params, enum naming collisions) — all existed before this work
- ResponseEnvelopeRenderer wrapping behavior is documented in the schema via inline_serializer wrappers matching the actual `{'status': 'success', 'data': ...}` shape
