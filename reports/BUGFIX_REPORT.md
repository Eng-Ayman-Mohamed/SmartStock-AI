# SmartStock-AI — Bug-Fix Report

Branch: `fix/bug-sweep-20260627`

## Summary

| Bug | Title | Status | Commit |
|-----|-------|--------|--------|
| Setup A | Drop AI attribution (.claude/settings.json) | Done | c0b88d7 |
| Setup C | Local Postgres + Redis for dev | Done | c5596e7 |
| 1 | Remove the "Ask AI" button | Fixed | 1b0f0c5 |
| 2 | Source badge opens a blank object | Fixed (NEEDS-VERIFICATION) | see log |
| 3 | Tables "suspense" not complete | _pending_ | — |
| 4 | Invoice scan with PDF not working | _pending_ | — |
| 5 | Registration email in production | _pending_ | — |
| 6 | Inventory actions | _pending_ | — |
| 7 | PO history table | _pending_ | — |
| 8 | "Create new order" button | _pending_ | — |

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
