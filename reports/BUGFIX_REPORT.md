# SmartStock-AI — Bug-Fix Report

Branch: `fix/bug-sweep-20260627`

## Summary

| Bug | Title | Status | Commit |
|-----|-------|--------|--------|
| Setup A | Drop AI attribution (.claude/settings.json) | Done | c0b88d7 |
| Setup C | Local Postgres + Redis for dev | Done | c5596e7 |
| 1 | Remove the "Ask AI" button | Fixed | 1b0f0c5 |
| 2 | Source badge opens a blank object | Fixed (NEEDS-VERIFICATION) | b62af00 |
| 3 | Tables "suspense" not complete | Fixed (same root cause as Bug 7) | 8d88945 |
| 4 | Invoice scan with PDF not working | Fixed | 01e5715 |
| 5 | Registration email in production | Fixed (NEEDS-VERIFICATION) | 8fa5560 |
| 6 | Inventory actions | Fixed | 1829da2 |
| 7 | PO history table | Fixed | 8d88945 |
| 8 | "Create new order" button | Fixed | cfcb635 |

---

## Setup

### Setup A — Remove AI attribution from commits/PRs
- **Change:** Added `.claude/settings.json` with `attribution.commit` and `attribution.pr` set to empty strings (the modern replacement for the deprecated `includeCoAuthoredBy`). Commits/PRs created from now on carry no AI trailer.
- **Commit:** `c0b88d7` — `chore: drop AI attribution from commits and PRs`

### Setup C — Local Postgres + Redis (performance)
- **Root cause of the 10–15s inventory lag:** `DATABASE_URL` pointed at a Neon free-tier DB in Singapore, which cold-starts after 5 min idle and round-trips every query; `docker-compose.yml` had no local DB. The inventory querysets already use `select_related`/`prefetch_related`, so the app code was not the bottleneck.
- **Change:** Added a local `db` (pgvector/pgvector:pg16) and `redis` service to `docker-compose.yml`, wired the app to them over the compose network (`db:5432`, `redis:6379`), and pointed the local (gitignored) `.env` `DATABASE_URL` at the local DB. Host DB published on `5433` to avoid the machine's existing Postgres on 5432. Also removed an `OPENAI_API_KEY: ${OPENAI_API_KEY:-}` override that was clobbering the `.env` value. Production `DATABASE_URL` is untouched and no `.env` is committed.
- **Commit:** `c5596e7` — `chore: add local postgres and redis services for dev`

---

## Bug 1 — Remove the "Ask AI" button

- **Status:** Fixed
- **Symptom:** An "Ask AI" pill button appeared in the AI Assistant chat toolbar (the first of three mode buttons).
- **Root cause:** `ModeSelector` renders one button per entry in its `modes` array; the entry `{ key: 'auto', label: 'Ask AI' }` produced the button. `'auto'` was also the default mode in `useChat` (initial state + `clearMessages` reset).
- **Fix:** Removed the `'auto'` entry from `ModeSelector.modes`, and repointed the two `useChat` defaults from `'auto'` to `'nl_query'` so the (now hidden) `'auto'` mode is never the active default. Left `'auto'` in the `ChatMode`/`engine` types since the backend still returns it as an engine value.
- **Files changed:** `smartstock-frontend/src/features/ai-assistant/components/ModeSelector.tsx`, `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts`
- **Verification:** `grep "Ask AI" src/` → none; `npx tsc --noEmit` → exit 0; `npx eslint <changed files>` → exit 0.
- **Notes / follow-ups:** None. Default chat mode is now NL Query.
- **Commit:** `fix(ai-assistant): remove the Ask AI mode button`

## Bug 2 — Source badge opens a blank object

- **Status:** Fixed (NEEDS-VERIFICATION)
- **Symptom:** Clicking a RAG answer's source badge shows nothing / a blank tooltip instead of the source content.
- **Root cause:** The chat API helper `sendChatMessage` returned the raw axios body `{ status, data: {...} }` without unwrapping the response envelope, so callers read `chatResponse.sources` as `undefined` (the real value lives at `.data.sources`). Every sibling helper (`sendNLQuery`, `getConversation`, `getConversationMessages`) already unwraps `data?.data ?? data`; this one did not.
- **Fix:** `sendChatMessage` now unwraps the `{ status, data }` envelope and returns the inner payload, matching the rest of the API layer. The badge renderer (`MessageBubble` → `CitationTag`) and the backend source shape (`extract_sources` → `{document, page, chunk_text}`, served identically by the live `/ai/chat/stream/` SSE `done` event) are already correct.
- **Files changed:** `smartstock-frontend/src/features/ai-assistant/api.ts`
- **Verification:** `npx tsc --noEmit` → exit 0; `npx eslint api.ts` → exit 0. Reproduced the live RAG path: `POST /api/ai/chat/stream/` returns `event: done` with `{"sources":[...]}` in the correct `{document, page, chunk_text}` shape (no envelope on the SSE stream, so the streaming UI path was already correct).
- **Notes / follow-ups:** NEEDS-VERIFICATION for the exact end-user symptom: the active chat UI uses the **streaming** path (`sendChatMessageStream`), which already returns correct shapes; the fixed `sendChatMessage` is the non-streamed helper. With the seeded `DocumentChunk` rows lacking real embeddings, RAG returns no sources locally, so a populated badge can't be reproduced until a real document is ingested (see Bug 4). If the blank badge persists after ingesting a real PDF, the remaining cause would be data-level (a `page_number` of `null` not matching the `[Source: …, Page: N]` marker in the answer text), not an API-shape mismatch.
- **Commit:** `fix(ai-assistant): unwrap response envelope in sendChatMessage`

## Bug 3 — Tables "suspense" not complete  /  Bug 7 — PO history table

> Bugs 3 and 7 are the **same defect**. Investigation found no broken React Suspense boundary or never-resolving query: the only `Suspense` in the app is route-level code-splitting (`router.tsx`) with a working fallback, and every list table uses clean server pagination — **except** the PO History table. Its "loads the top then stalls" symptom is the PO-history pagination bug below. One fix resolves both.

- **Status:** Fixed
- **Symptom:** The Purchase-Order History table shows fewer rows than the page size (rows silently missing) and an inflated total in the pager; navigating pages yields empty/short pages, so the table looks frozen / incomplete.
- **Root cause:** `listPOHistory` fetched `/purchasing/orders/` with **no status filter** (server-side pagination over ALL statuses), then discarded `draft`/`pending_approval` rows **client-side**. But the pagination `total` came from the server's unfiltered count, so `totalPages`/`hasNext` were computed from 500 records while only history-eligible rows were shown. Because default ordering is `-created_at`, the newest (pending) orders land on page 1 and get filtered away, leaving empty pages. Regressed when the view was switched from client-side to server-side pagination without a matching server-side status filter (`PurchaseOrderViewSet.filterset_fields = ['status']` only supports exact match, with no "not in" lookup).
- **Fix:** Added server-side exclusion so the paginated count matches the visible rows. Backend: new `PurchaseOrderFilter` (with a `CharInFilter = BaseInFilter + CharFilter` mixin) exposing `status_exclude`, and `PurchaseOrderViewSet` now uses `filterset_class = PurchaseOrderFilter` (the exact `status` filter is preserved). Frontend: `listPOHistory` passes `status_exclude=draft,pending_approval` and no longer filters client-side.
- **Files changed:** `smartstock-backend/apps/purchasing/views.py`, `smartstock-frontend/src/features/purchasing/api.ts`
- **Verification:** `manage.py check` → no issues; `ruff check --no-cache` → passed; `tsc --noEmit` / `eslint` → exit 0. Live API: `GET /purchasing/orders/?status_exclude=draft,pending_approval` returns only history statuses (no draft/pending) with `meta.total = 402` (vs 500 unfiltered) — the count now matches the filtered rows, so pagination is correct on every page.
- **Notes / follow-ups:** The `status_exclude` param is additive and backward-compatible; existing `?status=` exact filtering is unchanged.
- **Commit:** `fix(purchasing): exclude draft/pending from PO history server-side`

## Bug 4 — Invoice scan with PDF not working

- **Status:** Fixed
- **Symptom:** Scanning a PDF invoice fails (HTTP 400 from the vision API); image invoices (JPEG/PNG) work.
- **Root cause:** `VisionExtractor._extract_openai_compatible` passed the raw `data:application/pdf;base64,…` URL straight into the `image_url` content field. The Groq/OpenAI vision APIs only accept raster images there and return 400 for PDFs. No rasterization existed; `pdf2image`/Poppler were absent from the deps. (The Gemini path was unaffected — it uses `Part.from_bytes`, which handles PDFs natively.)
- **Fix:** Added `VisionExtractor._pdf_data_url_to_image_data_url`, which decodes the base64 PDF, renders page 1 with `pdf2image`/Poppler at 200 DPI, and returns a PNG data URL. `_extract_openai_compatible` now detects a `data:application/pdf` prefix and rasterizes before the vision call (image/JPEG/PNG uploads are untouched). Added `pdf2image` + `Pillow` to `requirements.txt` and `poppler-utils` to the `Dockerfile` apt layer.
- **Files changed:** `smartstock-backend/ai/multimodal/vision.py`, `smartstock-backend/requirements.txt`, `smartstock-backend/Dockerfile`
- **Verification:** `manage.py check` → ok; `ruff check --no-cache vision.py` → passed. Reproduced with the repo's `rag_pdf_test.pdf` inside the backend container: `_pdf_data_url_to_image_data_url` returns a valid `data:image/png;base64,…` URL, and the full `VisionExtractor().extract(pdf_url)` via the live Groq vision model now returns a parsed `{header, line_items}` dict (previously 400).
- **Notes / follow-ups:** Rasterizes the **first page** only (covers single-page invoices, which is the norm); multi-page line items would need rendering subsequent pages — noted as a follow-up. The running dev container had `poppler-utils`/`pdf2image` installed ad-hoc for verification; a `docker compose build backend` is required to bake them in from the committed Dockerfile/requirements.
- **Commit:** `fix(ingestion): rasterize PDF invoices before the vision API call`

## Bug 5 — Registration email in production

- **Status:** Fixed (NEEDS-VERIFICATION)
- **Symptom:** Registration verification email never arrives in production despite Brevo SMTP env vars being set; in some cases registration returns 500.
- **Root cause:** Two compounding defects in `config/settings/production.py`: (1) `EMAIL_USE_TLS = True` was hardcoded and `EMAIL_USE_SSL` was never set — so a port-465 (implicit-SSL) deployment does STARTTLS on an SSL socket and raises `ssl WRONG_VERSION_NUMBER`, which (with no try/except in the register view) 500s the request and orphans the new user; (2) `FRONTEND_URL` was **absent** from production settings, so `send_verification_email` fell back to `http://localhost:5173`, making every verification link dead even when the send succeeded.
- **Fix:** (a) `production.py` now reads `EMAIL_USE_SSL`/`EMAIL_USE_TLS` from env (SSL on → TLS auto-off) and defines `FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://smart-stock-dev.vercel.app')`. (b) `RegisterView.post` wraps the send in try/except, logs with context, and still returns 201 (account exists; user can re-request) instead of 500. (c) `send_verification_email`'s failure log now includes `host/port/tls/ssl/from/email` so the real production cause is visible.
- **Files changed:** `smartstock-backend/config/settings/production.py`, `smartstock-backend/apps/authentication/views.py`, `smartstock-backend/apps/authentication/services.py`
- **Verification:** `manage.py check` → ok; `ruff` → passed; the TLS/SSL env logic resolves correctly (SSL=False→TLS=True for 587; SSL=True→TLS=False for 465); a **live Brevo SMTP connect+auth on 587/TLS succeeded** with the configured credentials (no message sent). Full end-to-end confirmation requires production.
- **Notes / follow-ups (what to check in prod once logs are available):**
  1. Confirm `EMAIL_HOST/PORT/USER/PASSWORD` and `DEFAULT_FROM_EMAIL` are set in the prod environment and that `DEFAULT_FROM_EMAIL` is a **Brevo-verified sender** (Brevo rejects unverified senders).
  2. Set `FRONTEND_URL` to the real frontend origin (e.g. the Vercel URL) and verify the received link points there, not localhost.
  3. If using port 465, set `EMAIL_USE_SSL=True`; if 587, leave defaults (TLS).
  4. Register a test user and grep prod logs for `verification email` — a success log or the new structured failure log will pinpoint the state.
- **Commit:** `fix(auth): make prod email TLS/SSL and FRONTEND_URL configurable; harden send`

## Bug 6 — Inventory actions

- **Status:** Fixed
- **Symptom:** Inventory actions were sluggish, and stock-level writes accepted invalid data (negative quantities) without error.
- **Root cause:** The sluggishness was the remote Neon DB (addressed in Setup C — now ~30 ms against the local DB). The functional defect: `StockLevelSerializer` declared `quantity = IntegerField(source='quantity_on_hand', read_only=True)` and a `validate_quantity` method — but field-level validators are matched by the **writable field name**, which (via `fields = '__all__'`) is `quantity_on_hand`, not the read-only alias `quantity`. So `validate_quantity` was unreachable dead code and negative stock writes passed through.
- **Fix:** Renamed `validate_quantity` → `validate_quantity_on_hand` so DRF invokes it on the actual writable field.
- **Files changed:** `smartstock-backend/apps/inventory/serializers.py`
- **Verification:** `manage.py check` → ok; `ruff` → passed. Live: `PATCH /api/inventory/stock-levels/62/` with `quantity_on_hand=-5` now returns **422** (validation error; was silently 200), and `quantity_on_hand=42` returns **200** with the updated record — both in ~30 ms against the local DB.
- **Notes / follow-ups:** Separate latent issue (not blocking, not fixed here to keep the diff minimal): `StockLevelRepository.get_by_product_id` uses `.get(sku__product_id=...)`, which raises `MultipleObjectsReturned` for a product with more than one SKU on the legacy `/api/inventory/stock/{product_id}/` endpoint. The frontend does not call that endpoint; recommend `.filter(...).first()` as a follow-up.
- **Commit:** `fix(inventory): enforce non-negative stock on the writable field`

## Bug 8 — "Create New Order" button

- **Status:** Fixed
- **Symptom:** Filling the New Order modal and clicking Create Order closes the modal with no error, but the new PO never appears anywhere.
- **Root cause:** A PO is created with the model default `status='draft'` (this is intentional — the backend has a `draft → pending_approval` transition map, the `approve`/`reject` endpoints accept `draft`, and three existing tests assert draft-on-create). The defect is on the **frontend**: the Pending Approval queue (`listPendingPOs`) queried `status='pending_approval'` only, and PO History excludes `draft`, so a freshly created `draft` order appeared in neither list. The POST returned 201 and the modal closed, hiding the order.
- **Fix:** Surface drafts in the approval queue instead of changing the (intentional) create contract. Backend: added an additive `status_in` filter to `PurchaseOrderFilter`. Frontend: `listPendingPOs` now queries `status_in=draft,pending_approval`. Both draft and pending orders await an approval decision and the approve/reject endpoints already accept either, so this is the correct queue. No backend create-contract change, so the existing PO tests stay green.
- **Files changed:** `smartstock-backend/apps/purchasing/views.py`, `smartstock-frontend/src/features/purchasing/api.ts`
- **Verification:** `manage.py check` → ok; `ruff` → passed; `tsc`/`eslint` → exit 0. Live: `POST /api/purchasing/orders/` returns 201 with `status='draft'` (id 502); `GET /purchasing/orders/?status_in=draft,pending_approval` now includes that id. `pytest tests/integration/test_purchasing_endpoints.py` → **46 passed** (the draft-on-create tests remain valid).
- **Notes / follow-ups (assumption):** Chose the frontend fix over forcing `status='pending_approval'` in `perform_create`, because draft-on-create is a deliberate, tested backend contract and overriding it would break three intentional tests. API-created POs still have `requested_by=None` (only the AI `draft_po` service sets a requester) — populating it on manual create is a reasonable, separate follow-up.
- **Commit:** `fix(purchasing): show draft orders in the approval queue`
