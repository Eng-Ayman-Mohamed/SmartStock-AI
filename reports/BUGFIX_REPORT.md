# SmartStock-AI — Bug-Fix Report

Branch: `fix/bug-sweep-20260627`

## Summary

| Bug | Title | Status | Commit |
|-----|-------|--------|--------|
| Setup A | Drop AI attribution (.claude/settings.json) | Done | c0b88d7 |
| Setup C | Local Postgres + Redis for dev | Done | c5596e7 |
| 1 | Remove the "Ask AI" button | Fixed | see log |
| 2 | Source badge opens a blank object | _pending_ | — |
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
