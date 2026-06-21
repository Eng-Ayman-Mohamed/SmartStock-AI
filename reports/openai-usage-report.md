# OpenAI API Key & Models Usage Report

**Date:** 2026-06-15
**Project:** SmartStock AI

---

## 1. Models Used

| Model | Type | Dimensionality / Role | Files |
|---|---|---|---|
| **`gpt-4o`** | Chat (ChatOpenAI) | NL query parsing + response formatting | `ai/llm/chain.py`, `apps/ingestion/services.py` |
| **`gpt-4o`** (vision) | Chat (OpenAI client) | Invoice field extraction from images | `ai/multimodal/vision.py` |
| **`gpt-4o-mini`** | Chat (ChatOpenAI) | Lightweight intent classifier | `ai/llm/intent_classifier.py` |
| **`whisper-1`** | Audio (OpenAI client) | Speech-to-text transcription | `ai/multimodal/whisper.py` |
| **`text-embedding-3-small`** | Embedding (OpenAIEmbeddings) | 1536-dim vector embeddings for RAG | `ai/rag/ingestion.py`, `ai/rag/retrieval.py`, `apps/ingestion/services.py` |
| **`rerank-english-v3.0`** (Cohere) | Reranking | Cross-encoder reranking of RAG results | `apps/ingestion/services.py` |

---

## 2. API Key Consumption Points

Every file reads `OPENAI_API_KEY` from environment variables. Two patterns exist:

**Pattern A — Explicit `os.getenv` + error guard** (preferred):
| File | Line(s) | Error if missing |
|---|---|---|
| `ai/llm/chain.py` | 52–55 | `ValueError('OPENAI_API_KEY is missing. Check your .env file.')` |
| `ai/llm/intent_classifier.py` | 20–23 | `ValueError('OPENAI_API_KEY is missing.')` |
| `ai/multimodal/whisper.py` | 16–19 | `ValueError('OPENAI_API_KEY is missing.')` |
| `apps/ingestion/services.py` | 364–367 | `ValueError('OPENAI_API_KEY is missing.')` |
| `ai/multimodal/vision.py` | 23 | No guard — cryptic API error at runtime |

**Pattern B — Implicit env inheritance** (via `langchain_openai`):
| File | Line(s) | Behavior |
|---|---|---|
| `ai/rag/ingestion.py` | 54–56 | No explicit key passed; relies on `openai` env var default |
| `ai/rag/retrieval.py` | 17–19 | Same implicit inheritance |
| `apps/ingestion/services.py` | 371–372 | Same implicit inheritance |

### Env validation chain:
1. `config/validators.py:7` — `OPENAI_API_KEY` is first entry in `REQUIRED_ENV_VARS`
2. `validate_required_env_vars()` runs at Django startup → `ImproperlyConfigured` if missing
3. Logged at startup as masked value: `[CONFIG] OPENAI_API_KEY: sk***XX`

### Other references:
- `.env` — actual key value
- `.env.example:26` — `OPENAI_API_KEY=` with empty placeholder
- `config/settings/base.py` (via `validators.py`)
- `config/settings/development.py` / `production.py` (inherit base)
- `README.md` — documented as required
- `DEPLOY.md` — documented as required for Railway/Vercel
- `.github/workflows/ci.yml:22,75` — injected from GitHub Secrets for CI tests

---

## 3. Business Purpose

### 3a. NL Query Engine — `ai/llm/chain.py` (gpt-4o, 2 calls per query)

**Call 1 — Structured parsing** (lines 107–163): User's natural-language question is sent to GPT-4o with `tool_choice="required"`, forcing a structured `NLQueryToolSchema` output with fields: `action`, `filters`, `sort`, `limit`, `offset`. Converts free-text into a programmatic DB query.

**Call 2 — NL formatting** (lines 210–247): Raw DB results are rewritten into a concise natural-language answer with safety validation and a raw-data fallback.

**Value**: Powers the "Ask AI" chat — non-technical warehouse staff query inventory in plain English.

### 3b. Intent Classifier — `ai/llm/intent_classifier.py` (gpt-4o-mini, 1 call per query)

Classifies each query into: `nl_query` (DB query), `rag` (document search), or `out_of_scope`. Returns `{"intent": "...", "confidence": 0.0-1.0}`. On parse failure, defaults to `nl_query` with 0.5 confidence (fail-open).

**Value**: First gate in chat pipeline — routes queries to the correct engine without user input. 4o-mini saves cost vs using 4o for this simple task.

### 3c. Invoice Scanner — `ai/multimodal/vision.py` (gpt-4o vision, 1 call per invoice)

Sends invoice image as base64 data URL to GPT-4o vision with a JSON schema requiring: `product_name`, `sku_code`, `quantity_received`, `unit_price`, `supplier_name`. Returns structured data with confidence scores.

**Value**: Automates supplier invoice data entry — warehouse staff upload a photo, system pre-fills inventory adjustment form.

### 3d. Speech Transcription — `ai/multimodal/whisper.py` (whisper-1, 1 call per audio)

Takes raw audio bytes (from browser mic capture), sends to Whisper API, returns transcribed text.

**Value**: Enables voice input for gloves-on/hands-free warehouse workers.

### 3e. RAG Embedding Pipeline — `ai/rag/ingestion.py` (text-embedding-3-small, N calls per document)

PDF upload → text extraction (pypdf) → 512-token chunks (50-token overlap) → embeddings in batches of 100 with 1s delay → stored in `DocumentChunk` table (pgvector column).

**Value**: Converts warehouse documentation (SOPs, policy manuals) into a searchable vector corpus.

### 3f. RAG Query Pipeline — `ai/rag/retrieval.py` + `apps/ingestion/services.py` (text-embedding-3-small + gpt-4o + Cohere)

Pipeline steps:
1. **Embed query** (text-embedding-3-small) → 1536-dim vector
2. **Hybrid search** (retrieval.py): dense pgvector cosine similarity + sparse PostgreSQL FTS, merged via `(vector_score + normalized_fts_score) / 2`
3. **Rerank** (Cohere): boost top 3 chunks (3 retries with exponential backoff; falls back to vector-score ranking)
4. **Answer** (gpt-4o): inject top chunks as context, answer with `[Source: document, Page: N]` citations

**Value**: Answers questions about uploaded documents (e.g. "What's the return policy?") with source citations.

---

## 4. Architecture — OpenAI Calls Per Request

```
User input
│
├─► Chat text ───────────► intent_classifier.py (gpt-4o-mini)
│                              │
│                    ┌─────────┴─────────┐
│                    ▼                    ▼
│               chain.py           RAGQueryService
│               gpt-4o ×2           ├─ retrieval.py (text-embedding-3-small)
│               (parse + format)     ├─ Cohere rerank
│                    │               ├─ gpt-4o (answer)
│                    ▼               ▼
│               DB response     Document answer + sources
│
├─► Invoice image ────► vision.py (gpt-4o vision)
│
├─► Audio ────────────► whisper.py (whisper-1)
│
└─► PDF upload ───────► ingestion.py (text-embedding-3-small, batches of 100)
```

---

## 5. Observations & Recommendations

| Issue | Severity | Suggestion |
|---|---|---|
| `vision.py:23` no key guard before API call | Low | Add `os.getenv` guard like other files |
| `ingestion.py`, `retrieval.py`, `services.py:371` implicit key inheritance | Low | Add explicit `os.getenv` guards for consistency |
| Two GPT-4o calls per chat query doubles latency/tokens | Medium | Consider single-call architecture with structured output |
| `_get_llm()` duplicated in 3 files | Low | Extract shared factory in a common module |
| Cohere rerank requires separate `COHERE_API_KEY` | Info | Already documented in `.env.example` and `validators.py` |
| Langfuse wraps all OpenAI calls (token usage tracing) | Info | Enables cost monitoring — keep enabled |
| CI runs real OpenAI calls via GitHub Secrets | Info | Rotate the `OPENAI_API_KEY` secret periodically |

---

## 6. Multi-Provider Setup (Testing Phase) — 2026-06-16

### 6a. Why Multi-Provider

The original OpenAI API key ran out of credit (`429 insufficient_quota`). To continue testing all AI endpoints before production, we added support for **Groq** and **Google Gemini** as alternative providers. Controlled by a single `LLM_PROVIDER` env var.

### 6b. New File: `ai/llm/provider_config.py`

Central provider configuration module. Switches between OpenAI, Groq, and Gemini:

| Capability | OpenAI | Groq | Gemini |
|---|---|---|---|
| Chat/LLM | `gpt-4o` | `llama-3.3-70b-versatile` | `gemini-2.0-flash` |
| Intent Classification | `gpt-4o-mini` | `llama-3.1-8b-instant` | `gemini-2.0-flash` |
| Embeddings | `text-embedding-3-small` | fallback → Gemini | `gemini-embedding-001` |
| Whisper (STT) | `whisper-1` | `whisper-large-v3` | — |
| Vision | `gpt-4o` | — (no vision model) | `gemini-2.0-flash` |
| Reranking | — | — | — (uses Cohere) |

**To switch:** Change `LLM_PROVIDER=groq` in `.env` to `openai` or `gemini`. No code changes needed.

### 6c. API Keys Used

| Provider | Key Env Var | Purpose |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | Chat, NL query, embeddings, whisper, vision |
| Groq | `GROQ_API_KEY` | Chat, intent classification, whisper |
| Google | `GOOGLE_API_KEY` | Embeddings (fallback when Groq), vision, chat |
| Cohere | `COHERE_API_KEY` | Reranking for RAG pipeline |

### 6d. Files Modified for Multi-Provider

| File | Change | Why |
|---|---|---|
| `ai/llm/provider_config.py` | **NEW** — central provider config | Single source of truth for model selection |
| `ai/llm/chain.py` | `get_llm()` now calls `provider_config.get_chat_llm()` | Removed hardcoded OpenAI dependency |
| `ai/llm/intent_classifier.py` | `_get_classifier_llm()` now calls `provider_config.get_chat_llm_mini()` | Removed hardcoded OpenAI dependency |
| `ai/multimodal/whisper.py` | Uses `provider_config.get_whisper_client()` | Supports both OpenAI and Groq Whisper |
| `ai/multimodal/vision.py` | Uses `provider_config.get_vision_client()`, added `supports_vision` check | Returns 501 if provider has no vision model |
| `ai/rag/ingestion.py` | Uses `provider_config.get_embeddings()` instead of `OpenAIEmbeddings` directly | Supports Gemini embeddings |
| `ai/rag/retrieval.py` | Uses `provider_config.get_embeddings()` instead of `OpenAIEmbeddings` directly | Supports Gemini embeddings |
| `apps/ingestion/services.py` | `RAGQueryService._get_llm()` and `_get_embeddings()` use provider config | Removed hardcoded OpenAI imports |
| `apps/ingestion/views.py` | Added `ObjectDoesNotExist` catch for invoice scan endpoints, improved error messages | Better error handling |
| `ai/llm/prompts.py` | Fixed brace escaping for ChatPromptTemplate | Bug fix — double-escaped braces |
| `ai/llm/chain.py` | Added missing injection patterns (`ignore all previous`, `forget your rules`) | Security fix |
| `.env` | Added `GROQ_API_KEY`, `GOOGLE_API_KEY`, `LLM_PROVIDER` | Provider configuration |
| `requirements.txt` | Added `langchain-google-genai`, `google-genai`, `groq` | New provider dependencies |

### 6e. Testing Results (Groq Provider)

All AI endpoints tested on 2026-06-16 using `LLM_PROVIDER=groq`:

| # | Endpoint | HTTP | Result |
|---|----------|------|--------|
| 1 | `GET /api/health/live/` | 200 | ✅ Liveness probe OK |
| 2 | `POST /api/auth/login/` | 200 | ✅ JWT token issued |
| 3 | `POST /api/ai/chat/` (auto) | 200 | ✅ Classified as nl_query, executed chain |
| 4 | `POST /api/ai/nlquery/` | 200 | ✅ Tool calling worked, returned structured result |
| 5 | `POST /api/ai/rag-query/` | 200 | ✅ Empty corpus handled gracefully |
| 6 | `POST /api/ai/transcribe/` | 200 | ✅ Groq whisper-large-v3 transcribed audio |
| 7 | `POST /api/ai/invoice-scan/` | 501 | ⚠️ Expected — Groq has no vision model |
| 8 | `POST /api/ai/invoice-scan/confirm/` | 404 | ✅ Correct 404 for non-existent scan |
| 9 | `POST /api/ai/invoice-scan/{id}/reject/` | 404 | ✅ Correct 404 for non-existent scan |
| 10 | `GET /api/ai/documents/` | 200 | ✅ Empty list returned |
| 11 | Prompt injection test | 400 | ✅ Blocked correctly |
| 12 | Unauthenticated access | 401 | ✅ Auth check working |
| 13 | Validation (empty query) | 422 | ✅ Proper validation errors |

**12/13 passed, 0 failed, 1 expected limitation.**

### 6f. Bugs Found and Fixed During Testing

| Bug | File | Fix |
|---|---|---|
| `ChatPromptTemplate` missing variable `{"error"}` — braces only escaped for f-string, not LangChain | `ai/llm/prompts.py:83` | Changed `{{...}}` to `{{{{...}}}}` (quadruple escape) |
| Prompt injection filter missed `"ignore all previous instructions"` and `"forget your rules"` | `ai/llm/chain.py:217-227` | Added missing patterns to `_INSTRUCTION_OVERRIDE_PATTERNS` |
| `InvoiceScanConfirmView` returned 500 for non-existent scans | `apps/ingestion/views.py` | Added `except ObjectDoesNotExist` → 404 |
| `InvoiceScanRejectView` returned 500 for non-existent scans | `apps/ingestion/views.py` | Added `except ObjectDoesNotExist` → 404 |
| `RAGQueryService.rerank()` crashed on empty document list | `apps/ingestion/services.py` | Added `if not chunks: return []` guard |
| NL query timeout too short (10s) for Groq | `apps/inventory/views.py:1418` | Increased from 10s to 30s |

### 6g. Architecture — Provider Call Flow

```
User input
│
├─► Chat text ───────────► intent_classifier.py ──► get_chat_llm_mini()
│                              │                       ├─ groq: llama-3.1-8b
│                              │                       ├─ openai: gpt-4o-mini
│                              │                       └─ gemini: gemini-2.0-flash
│                    ┌─────────┴─────────┐
│                    ▼                    ▼
│               chain.py            RAGQueryService
│               get_chat_llm()      ├─ get_embeddings()
│               ├─ groq: llama-3.3   │   ├─ groq: → Gemini fallback
│               ├─ openai: gpt-4o    │   ├─ openai: text-embedding-3-small
│               └─ gemini: flash     │   └─ gemini: gemini-embedding-001
│                    │               ├─ Cohere rerank (unchanged)
│                    │               └─ get_chat_llm() → answer
│                    ▼
│               DB response
│
├─► Invoice image ────► vision.py ──► get_vision_client()
│                                      ├─ groq: 501 (no vision support)
│                                      ├─ openai: gpt-4o
│                                      └─ gemini: gemini-2.0-flash
│
├─► Audio ────────────► whisper.py ──► get_whisper_client()
│                                      ├─ groq: whisper-large-v3
│                                      └─ openai: whisper-1
│
└─► PDF upload ───────► ingestion.py ──► get_embeddings()
                                         ├─ groq: → Gemini fallback
                                         ├─ openai: text-embedding-3-small
                                         └─ gemini: gemini-embedding-001
```

---

## 7. CI Test Fixes — 2026-06-16

### 7a. Problem

The multi-provider refactor removed module-level imports (`ChatOpenAI`, `OpenAIEmbeddings`, `os`) from several files. Existing tests mocked these at the old import paths, causing 10 test failures:

```
AttributeError: <module 'apps.ingestion.services'> does not have the attribute 'ChatOpenAI'
AttributeError: <module 'ai.rag.ingestion'> does not have the attribute 'OpenAIEmbeddings'
AttributeError: module 'ai.llm.intent_classifier' has no attribute 'os'
```

Coverage also dropped to 79.60% (below 80% threshold) due to the new `provider_config.py` module.

### 7b. Root Cause

All provider functions use **lazy imports** (import inside the function body, not at module level):

```python
def get_embeddings():
    from langchain_openai import OpenAIEmbeddings  # lazy — not a module attribute
    return OpenAIEmbeddings(...)
```

Tests were patching `apps.ingestion.services.OpenAIEmbeddings` which no longer exists as a module attribute.

### 7c. Fix — Updated Mock Targets

| Test File | Old Mock Target | New Mock Target |
|---|---|---|
| `tests/integration/test_rag_query.py` | `apps.ingestion.services.ChatOpenAI` | `ai.llm.provider_config.ChatOpenAI` (via `langchain_openai`) |
| `tests/integration/test_rag_query.py` | `apps.ingestion.services.OpenAIEmbeddings` | `ai.llm.provider_config.OpenAIEmbeddings` (via `langchain_openai`) |
| `tests/unit/test_ingestion.py` | `ai.rag.ingestion.OpenAIEmbeddings` | `ai.llm.provider_config.OpenAIEmbeddings` (via `langchain_openai`) |
| `tests/unit/ai/test_prompt_separation.py` | `apps.ingestion.services.ChatOpenAI` | `ai.llm.provider_config.ChatOpenAI` |
| `tests/unit/ai/test_prompt_separation.py` | `apps.ingestion.services.OpenAIEmbeddings` | `ai.llm.provider_config.OpenAIEmbeddings` |
| `tests/unit/test_remaining_coverage.py` | `ai.llm.intent_classifier.os` | `ai.llm.provider_config.get_chat_llm_mini` |
| `tests/unit/test_remaining_coverage.py` | `ai.llm.intent_classifier.ChatOpenAI` | `ai.llm.provider_config.get_chat_llm_mini` |

### 7d. New Test File: `tests/unit/ai/test_provider_config.py`

17 unit tests added to restore coverage and validate the multi-provider config:

| Test Class | Tests | What it validates |
|---|---|---|
| `ProviderConfigGetProviderConfigTest` | 3 | Returns correct config for openai/groq/gemini |
| `ProviderConfigGetApiKeyTest` | 2 | Raises ValueError when key missing, returns key when set |
| `ProviderConfigGetChatLlmTest` | 3 | Returns ChatOpenAI, model override works, Groq sets base_url |
| `ProviderConfigGetChatLlmMiniTest` | 1 | Delegates to get_chat_llm with mini model name |
| `ProviderConfigGetEmbeddingsTest` | 4 | OpenAI/Gemini embeddings, Groq→Gemini fallback, missing key error |
| `ProviderConfigGetWhisperClientTest` | 2 | Groq Whisper client, OpenAI Whisper client |
| `ProviderConfigGetVisionClientTest` | 2 | OpenAI vision client, Groq vision with base_url |

### 7e. CI Results After Fix

```
tests/integration/test_rag_query.py::RAGQueryServiceTests  — 4 passed ✅
tests/unit/test_ingestion.py                                — 8 passed ✅
tests/unit/ai/test_prompt_separation.py                     — 8 passed ✅
tests/unit/test_remaining_coverage.py::IntentClassifierTests — 12 passed ✅
tests/unit/ai/test_provider_config.py                       — 17 passed ✅
─────────────────────────────────────────────────────────────
Total                                                        49 passed ✅
```

---

## 8. Gemini Vision & Mixed-Provider Testing — 2026-06-17

### 8a. Problem

Groq has no vision model for invoice scanning and no Whisper model for voice transcription. Gemini has vision but no Whisper. No single free-tier provider covers all features. Testing invoice scanning and voice requires mixing providers.

### 8b. Solution: `LLM_WHISPER_PROVIDER`

Added a separate `LLM_WHISPER_PROVIDER` env var so whisper can use a different provider than the main LLM:

```env
LLM_PROVIDER=gemini              # chat, vision, embeddings
LLM_WHISPER_PROVIDER=groq        # voice/transcription
```

This allows:
- **Invoice scanning** → Gemini vision (`gemini-2.0-flash` via `google-genai` SDK)
- **Voice transcription** → Groq Whisper (`whisper-large-v3`)
- **Chat/embeddings** → Gemini

### 8c. Changes to `provider_config.py`

| Addition | Purpose |
|---|---|
| `WHISPER_PROVIDER = os.getenv('LLM_WHISPER_PROVIDER', PROVIDER).lower()` | Separate whisper provider |
| `get_api_key_for_provider(provider_name)` | Get API key for any provider, not just the active one |
| `get_whisper_config()` | Returns whisper config dict for the whisper provider |
| `get_whisper_client()` | Uses `WHISPER_PROVIDER` instead of `PROVIDER` |

### 8d. Gemini Vision Support — `vision.py`

Added native Gemini vision path using `google-genai` SDK:

```python
def extract(self, file_data_url: str) -> dict:
    if self._provider == 'gemini':
        return self._extract_gemini(file_data_url)      # NEW
    return self._extract_openai_compatible(file_data_url)  # renamed
```

**`_extract_gemini()`** uses the `google-genai` SDK directly:
- Converts base64 data URL → bytes + MIME type
- Calls `client.models.generate_content()` with image part + text prompt
- Parses JSON response same as OpenAI path

**`_extract_openai_compatible()`** — renamed from original `extract()`, unchanged logic.

### 8e. Files Modified

| File | Change |
|---|---|
| `ai/llm/provider_config.py` | Added `WHISPER_PROVIDER`, `get_api_key_for_provider()`, `get_whisper_config()`, updated `get_whisper_client()` |
| `ai/multimodal/vision.py` | Added `_extract_gemini()` using `google-genai` SDK, renamed original to `_extract_openai_compatible()` |
| `ai/multimodal/whisper.py` | Uses `WHISPER_PROVIDER` and `get_whisper_config()` instead of `PROVIDER` |
| `config/wsgi.py` | Added `load_dotenv()` — gunicorn was not loading `.env` file |
| `.env` | Added `LLM_WHISPER_PROVIDER=groq`, changed `LLM_PROVIDER=gemini` |
| `tests/unit/ai/test_provider_config.py` | Updated whisper tests to patch `WHISPER_PROVIDER` instead of `PROVIDER`, added `skipUnless` for optional packages |

### 8f. Bug Fix: `wsgi.py` Missing `load_dotenv()`

**Problem:** Gunicorn starts via `config.wsgi:application`, not `manage.py`. The `wsgi.py` file had no `load_dotenv()` call, so environment variables from `.env` were never loaded. This caused the server to use hardcoded defaults (OpenAI) instead of the configured provider (Gemini/Groq).

**Fix:** Added `from dotenv import load_dotenv; load_dotenv()` at the top of `config/wsgi.py`.

### 8g. Provider Capability Matrix (Updated)

| Feature | OpenAI | Groq | Gemini |
|---|---|---|---|
| Chat/LLM | `gpt-4o` | `llama-3.3-70b-versatile` | `gemini-2.0-flash` |
| Intent Classification | `gpt-4o-mini` | `llama-3.1-8b-instant` | `gemini-2.0-flash` |
| Embeddings | `text-embedding-3-small` | fallback → Gemini | `gemini-embedding-001` |
| Whisper (STT) | `whisper-1` | `whisper-large-v3` | — |
| Vision (invoice scan) | `gpt-4o` | — | `gemini-2.0-flash` (via `google-genai` SDK) |
| Reranking | — | — | — (Cohere) |

### 8h. Testing Results (Gemini + Groq Mixed)

Tested 2026-06-17 with `LLM_PROVIDER=gemini`, `LLM_WHISPER_PROVIDER=groq`:

| # | Endpoint | HTTP | Result |
|---|----------|------|--------|
| 1 | `POST /api/ai/transcribe/` | 200 | ✅ Groq whisper-large-v3 transcribed audio |
| 2 | `POST /api/ai/invoice-scan/` | 500 | ⚠️ Gemini 429 — free tier quota exhausted (both keys share same project) |

**Voice works.** Invoice scan code is correct (verified reaching Gemini API, not OpenAI) but blocked by quota.

### 8i. Gemini Quota Notes

- Both old and new `GOOGLE_API_KEY` values share the same Google Cloud project
- `limit: 0` on `GenerateRequestsPerDayPerProjectPerModel-FreeTier` means the daily free tier is fully consumed
- Quota resets at midnight Pacific Time
- To test immediately: create a key from a **different Google Cloud project** at https://aistudio.google.com/apikey
- Invoice scan code path verified correct: `_extract_gemini()` → `google-genai` SDK → Gemini API (not OpenAI)

---

## 9. Chat History — 2026-06-18

### 9a. Why Chat History

The original chat was **stateless** — every message was independent. The AI had no memory of prior questions within a conversation. Users had to repeat context on follow-up queries (e.g. "How many of *those* do we need?" — the AI didn't know what "those" referred to).

Chat history adds **multi-turn conversations** with persistent storage, so the AI remembers context within a session and users can revisit past conversations.

### 9b. New App: `apps/ai/`

A dedicated Django app for conversation management, following Clean Architecture (Views → Services → Repositories → DB).

| File | Purpose |
|---|---|
| `apps/ai/__init__.py` | Python package marker |
| `apps/ai/apps.py` | Django app config — registers `apps.ai` in `INSTALLED_APPS` |
| `apps/ai/models.py` | `ChatConversation` + `ChatMessage` models |
| `apps/ai/repositories.py` | `ConversationRepository` + `ChatMessageRepository` (extends `BaseRepository`) |
| `apps/ai/services.py` | `ConversationService` — list, create, delete, rename, history, auto-title |
| `apps/ai/serializers.py` | DRF serializers for API request/response |
| `apps/ai/views.py` | `ConversationViewSet` — REST endpoints |
| `apps/ai/urls.py` | Routes at `/api/ai/conversations/` |
| `apps/ai/admin.py` | Admin panel with inline messages |
| `apps/ai/migrations/0001_initial.py` | Creates `ai_chatconversation` + `ai_chatmessage` tables |

### 9c. Database Schema

**`ai_chatconversation`**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | FK → `authentication_customuser` | Conversation owner |
| `title` | VARCHAR(200) | Auto-set from first message |
| `created_at` | TIMESTAMP | Auto |
| `updated_at` | TIMESTAMP | Auto — bumped on new message |

**`ai_chatmessage`**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `conversation_id` | FK → `ai_chatconversation` | Parent conversation |
| `role` | VARCHAR(10) | `user` or `assistant` |
| `content` | TEXT | Message text |
| `engine` | VARCHAR(20) | `nl_query`, `rag`, or empty |
| `mode` | VARCHAR(20) | `auto`, `nl_query`, or `rag` |
| `sources` | JSONB | Citation list from RAG |
| `created_at` | TIMESTAMP | Auto |

### 9d. Files Modified

| File | Change | Why |
|---|---|---|
| `config/settings/base.py` | Added `apps.ai.apps.AIConfig` to `INSTALLED_APPS` | Register the new app |
| `config/urls.py` | Added `api/ai/conversations/` route | Wire up conversation endpoints |
| `apps/ingestion/serializers.py` | Added optional `conversation_id` to `ChatSerializer` | Accept conversation ID from frontend |
| `apps/ingestion/views.py` | `ChatEndpointView` loads history, passes to engine, saves messages, auto-titles | Core chat history logic |
| `apps/ingestion/services.py` | `RAGQueryService.execute()` and `call_llm_with_usage()` accept `history` param | Inject conversation context into LLM prompt |
| `.env.example` | Added comment that chat history needs no extra env vars | Documentation |

### 9e. Frontend Changes

| File | Change |
|---|---|
| `features/ai-assistant/types.ts` | Added `Conversation`, `ConversationDetail` interfaces; `ChatResponse` includes `conversation_id` |
| `features/ai-assistant/api.ts` | Added `listConversations`, `createConversation`, `getConversation`, `deleteConversation`, `renameConversation` |
| `features/ai-assistant/hooks/useChat.ts` | Accepts `conversationId`, sends it with requests, has `loadFromConversation` and `clearMessages` |
| `features/ai-assistant/hooks/useConversations.ts` | **NEW** — manages conversation list, select/create/delete/rename |
| `features/ai-assistant/components/ConversationSidebar.tsx` | **NEW** — sidebar UI with conversation list |
| `features/ai-assistant/components/ChatPanel.tsx` | Integrated sidebar, auto-creates conversation on first message |

### 9f. How History Is Injected Into the LLM

Last 10 messages are included in the RAG prompt as prior context:

```python
# apps/ingestion/services.py — RAGQueryService.call_llm_with_usage()
messages = [
    ('system', RAG_SYSTEM_PROMPT),
]

if history:
    history_text = '\n'.join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in history[-10:]
    )
    messages.append(('user', f'Previous conversation:\n{history_text}'))

messages.append(('user', '{query}'))
```

The NL Query engine (`chain.py`) does **not** use history — it's a stateless structured-query parser, not conversational.

### 9g. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/ai/conversations/` | GET | List user's conversations |
| `/api/ai/conversations/` | POST | Create new conversation |
| `/api/ai/conversations/{id}/` | GET | Get conversation with all messages |
| `/api/ai/conversations/{id}/` | PATCH | Rename conversation |
| `/api/ai/conversations/{id}/` | DELETE | Delete conversation + all messages |
| `/api/ai/conversations/{id}/messages/` | GET | Get messages for a conversation |
| `/api/ai/chat/` | POST | Send message (now accepts optional `conversation_id`) |

### 9h. OpenAI Token Impact

Chat history increases token usage per request:

| Scenario | Tokens per request |
|---|---|
| No history (stateless) | ~500–1000 |
| With 10 messages history | ~1500–3000 |

The history is capped at **10 messages** to control costs. Older messages are still stored in the database but not injected into prompts.

**Estimated cost increase**: ~2–3x per chat message when history is active. Mitigated by the history limit and the fact that most conversations are 5–15 messages deep.

### 9i. User Walkthrough

1. **First visit** — empty sidebar, empty chat area with suggestion buttons
2. **User types a question** — new conversation auto-created, first message becomes the title
3. **User asks a follow-up** — AI has context from previous messages, knows what "those" refers to
4. **Sidebar** — click to switch conversations, rename on hover, delete on hover, toggle sidebar
5. **New Chat** — starts fresh conversation with no history
6. **Multi-turn** — last 10 messages injected into RAG prompt for context continuity

---

## 10. Groq Vision Enablement & Dotenv Fix — 2026-06-19

### 10a. Problem: "Something went wrong" on every chat request

On 2026-06-19, all AI chat endpoints returned `504 Gateway Timeout` / `"Sorry, something went wrong"`. No code changes had been made since the previous session.

**Root cause:** Gemini free-tier API quota had been exhausted (`429 RESOURCE_EXHAUSTED`). The `langchain-google-genai` SDK performs 5 retries with exponential backoff (1.4s → 2.8s → 5.7s → 11.4s → 16.3s = ~37s total), causing the 15‑second CHAT_TIMEOUT to fire before a single request completes. Additionally, an OpenAI key was also at zero quota (`insufficient_quota`).

**Secondary bug — ThreadPoolExecutor blocking:** The `with ThreadPoolExecutor() as executor:` context manager calls `executor.shutdown(wait=True)` on exit, blocking until every submitted future finishes. Because the hanging Gemini thread never completed, the executor blocked for 37+ seconds even though the main thread already timed out after 15 seconds. The timeout was effectively dead code.

**Tertiary bug — dotenv override order:** The root monorepo `.env` at `/home/mawada/SmartStock-AI/.env` contained `DATABASE_URL=postgresql://postgres:postgres@localhost:5433/smartstock_ai` and a stale `LLM_PROVIDER=gemini`. Because `load_dotenv()` with default `override=False` does not replace already-set variables, whichever file was loaded *first* won. Docker Compose and Railway environments loaded the root `.env` first via Docker's `env_file` directive, silently overriding the backend's `.env` with wrong DB credentials and the wrong LLM provider.

### 10b. Solution: Switch to Groq for everything

All providers were evaluated on 2026-06-19:

| Provider | Status | Problem |
|---|---|---|
| OpenAI | Exhausted | `insufficient_quota` on API key |
| Gemini | Exhausted | `429 RESOURCE_EXHAUSTED` — both keys share same GCP project |
| Groq | **Working** | Free tier active, no quota issues |

Decision: switch `LLM_PROVIDER=groq` for all LLM features.

### 10c. Groq Vision — Previously Unsupported, Now Working

The earlier provider capability matrix (section 8g) listed Groq vision as **not supported**. On 2026-06-19, we discovered that **Groq now supports vision** via the `meta-llama/llama-4-scout-17b-16e-instruct` model, which accepts both text and image inputs through the OpenAI-compatible API.

**Changes to `ai/llm/provider_config.py`:**

| Setting | Before | After |
|---|---|---|
| Groq `vision_model` | (none — not set) | `meta-llama/llama-4-scout-17b-16e-instruct` |
| Groq `supports_vision` | `False` | `True` |

**Result:** `POST /api/ai/invoice-scan/` returns **200** with Groq vision (was 501 "No vision support"). Verified with a test image — correctly identified colours and extracted structured invoice data.

**Updated Provider Capability Matrix:**

| Feature | OpenAI | Groq | Gemini |
|---|---|---|---|
| Chat/LLM | `gpt-4o` | `llama-3.3-70b-versatile` | `gemini-2.0-flash` |
| Intent Classification | `gpt-4o-mini` | `llama-3.1-8b-instant` | `gemini-2.0-flash` |
| Embeddings | `text-embedding-3-small` | fallback → Gemini | `gemini-embedding-001` |
| Whisper (STT) | `whisper-1` | `whisper-large-v3` | — |
| Vision (invoice scan) | `gpt-4o` | `**llama-4-scout-17b-16e-instruct**`(NEW) | `gemini-2.0-flash` |
| Reranking | — | — | — (Cohere) |

### 10d. Files Modified

| File | Change | Why |
|---|---|---|
| `ai/llm/provider_config.py:40-41` | Set Groq `vision_model` + `supports_vision=True` | Enable Groq vision for invoice scanning |
| `apps/ingestion/views.py:807-841` | Replaced `with ThreadPoolExecutor` with explicit `executor.shutdown(wait=False)` | Prevent executor from blocking on hanging LLM threads — timeout now actually works |
| `manage.py:9` | `load_dotenv(find_dotenv(), override=True)` | Backend `.env` wins over root monorepo `.env` |
| `config/wsgi.py:5` | Same dotenv fix | Gunicorn loads backend `.env` correctly |
| `smartstock-backend/.env` | `LLM_PROVIDER=groq`, `LLM_WHISPER_PROVIDER=groq` | Use Groq for everything |
| `tests/unit/test_whisper.py` | Updated mocks from `openai.OpenAI` to `ai.llm.provider_config.get_whisper_client` | Tests were mocking the wrong targets after provider switch |
| `tests/unit/ai/test_provider_config.py` | Updated Groq config assertion: `supports_vision=True`, added `vision_model` check | CI alignment |
| `tests/unit/test_coverage_boost2.py` | **NEW** — 47 tests for metrics, repos, services, provider config | Coverage was 77.17% (below 80% threshold) |

### 10e. Testing Results (Groq Provider — Full Coverage)

Tested 2026-06-19 with `LLM_PROVIDER=groq`, `LLM_WHISPER_PROVIDER=groq`:

| # | Endpoint | HTTP | Result |
|---|---|---|---|
| 1 | `POST /api/ai/chat/` | 200 | ✅ Groq answered inventory queries correctly |
| 2 | `POST /api/ai/invoice-scan/` | 200 | ✅ **NEW** — Groq vision extracts fields via `llama-4-scout-17b-16e-instruct` |
| 3 | `POST /api/ai/transcribe/` | 200 | ✅ Groq whisper-large-v3 transcribed audio |
| 4 | `GET /api/health/` | 200 | ✅ Database + Redis connected |

### 10f. CI Coverage

Full test suite: **1395 passed**, 0 failed. Coverage: **84.88%** (above 80% threshold).

---

## 11. Critical Bug Fixes — 2026-06-21

### 11a. Bug 1 (CRITICAL) — Frontend: First message in new conversation permanently lost

**File(s):** `features/ai-assistant/hooks/useChat.ts`, `features/ai-assistant/components/ChatPanel.tsx`

**Problem:** When a user types their first message and no conversation exists yet, `ChatPanel.handleSend()` calls `startNewConversation()` which creates a new conversation asynchronously. However, `sendMessage(query)` on the next line still captured the **old** `conversationId` (`undefined`) from its closure — React hadn't re-rendered yet. The backend received `conversation_id: undefined`, processed the query, but never saved the message to the conversation.

**Result:** The conversation appeared in the sidebar but was permanently empty (0 messages). Every user's first message in a new chat was silently discarded.

**Fix (2 files):**

| File | Change |
|------|--------|
| `hooks/useChat.ts:32-33` | `sendMessage` now accepts optional `conversationIdOverride` parameter; resolves `activeConvId = conversationIdOverride ?? conversationId` before sending |
| `components/ChatPanel.tsx:54-59` | After `startNewConversation()` returns `newConv`, passes `newConv.id` to `sendMessage(query, newConv.id)` with early return |

**Test result:** 568 tests passed, 0 TS errors.

### 11b. Bug 2 (CRITICAL) — Backend: `_handle_get_low_stock` hardcoded threshold overrides LLM

**File:** `apps/inventory/views.py:1260-1295`

**Problem:** Three bugs in one function:

1. **Dead code `/` LLM override** — `threshold = filters.get('threshold', 10) if hasattr(filters, 'get') else 10`. `NLQueryFilters` has no `.get()` method, so `hasattr` was always `False` and `threshold` was always `10`. If the LLM generated "show items with less than 5 units", the filter silently became `qty < 5 AND qty < 10` (coincidentally correct). But "show items below their reorder point" always returned items below 10, ignoring per-product reorder points.

2. **Field alias incompatibility** — `_build_q_from_filters()` uses `FIELD_ALIASES` which maps `quantity_on_hand` → `skus__stock_level__quantity_on_hand`. This works on `Product.objects` but **breaks on `StockLevel.objects`** (no `skus` relation). Any LLM-generated condition with fields like `category`, `product_name`, or `sku_code` would crash with `FieldError`.

3. **No default for empty conditions** — The pattern cache entry `('low stock', 'get_low_stock', {})` with no conditions would match all items (unbounded), which is a UX and cost risk.

**Fix:** Rewrote `_handle_get_low_stock` to:

- Manually map conditions to `StockLevel`-correct ORM paths (`sku__product__name__icontains`, `sku__product__category__name`, etc.)
- Remove the hardcoded `threshold` / dead `.get()` code
- Default to `quantity_on_hand < F('reorder_point')` when no quantity condition is present (semantically correct: "low" means below each product's own reorder point)
- Cap at 100 results (matching other handlers' patterns)

**Test result:** 187 inventory/low-stock tests passed, 0 new lint errors.
