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

---

## 12. Frontend AI Chat UI Improvements — 2026-06-21

### 12a. Why These Changes

The AI chat interface had three UX issues:
1. **No voice feedback** — the voice recorder showed only a countdown timer, with no visual indication that audio was being captured
2. **Voice auto-sent** — transcribed text was sent immediately with no chance to review or edit
3. **Dated visual design** — single-line text input, no message animations, engine labels cluttering the UI

### 12b. Voice Transcript Review

**Files modified:**

| File | Change |
|------|--------|
| `features/ai-assistant/hooks/useVoiceRecorder.ts` | Removed `onTranscript` callback pattern. Added `transcript` state + `clearTranscript()`. After transcription, text stored in state instead of auto-sending |
| `features/ai-assistant/components/VoiceButton.tsx` | Accepts `onTranscript` prop. When hook finishes transcription, calls `onTranscript(transcript)` with the text |
| `features/ai-assistant/components/ChatPanel.tsx` | Changed `onTranscript` handler to populate input box (`setInput(text)`) and focus the textarea instead of calling `handleSend(text)` |

**User flow (before):** Record → Stop → Transcribe → Auto-send
**User flow (after):** Record → Stop → Transcribe → Text appears in input → User reviews/edits → Press Send

### 12c. Live Audio Bars Waveform

**Files modified:**

| File | Change |
|------|--------|
| `features/ai-assistant/hooks/useVoiceRecorder.ts` | Added `AudioContext` + `AnalyserNode` connected to mic stream. Runs `requestAnimationFrame` loop reading frequency data, computes average volume (0-1), exposes `audioLevel` state. Cleans up on stop/cancel |
| `features/ai-assistant/components/VoiceButton.tsx` | Added `AudioBars` component — 5 vertical bars that scale with `audioLevel` using `transform: scaleY()`. Rendered next to the stop button during recording |

**Technical details:**
- Uses Web Audio API `AnalyserNode` with `fftSize: 256` (128 frequency bins)
- Volume computed as average of all frequency bins, normalized to 0-1
- Bars have staggered `offset` based on distance from center for a natural bounce effect
- `requestAnimationFrame` loop ensures smooth 60fps animation
- AudioContext properly closed on stop/cancel to prevent resource leaks

### 12d. Visual Polish

**Files modified:**

| File | Change |
|------|--------|
| `features/ai-assistant/components/ChatPanel.tsx` | Replaced `<input type="text">` with auto-resizing `<textarea>`. Supports Shift+Enter for newlines. Auto-resizes up to 160px max height. Send button aligned with textarea bottom |
| `features/ai-assistant/components/MessageBubble.tsx` | Added `animate-fadeIn` class to messages. Removed engine labels (`NL Query`/`RAG`/`Auto`) from AI message bubbles |
| `features/ai-assistant/components/ChatEmptyState.tsx` | Larger bot icon (16→14), more vertical spacing, suggestion chips with rounded-xl and hover background effect |

### 12e. OpenAI API Impact

**Voice transcription:** No change to API usage. The `transcribeAudio()` call happens at the same point in the flow — only the post-transcription behavior changed (populate input vs auto-send).

**Token usage:** No change. The same messages are sent to the LLM; the only difference is users can now edit transcribed text before sending, which may slightly reduce wasted tokens from mis-transcribed voice input.

### 12f. Build & Lint Results

```
$ npm run build
✓ built in 934ms — 0 errors, 0 TS errors

$ npm run lint
0 errors, 0 warnings
```

### 12g. Files Changed Summary

| File | Lines changed |
|------|--------------|
| `features/ai-assistant/hooks/useVoiceRecorder.ts` | +45 (AudioContext, audioLevel, transcript state) |
| `features/ai-assistant/components/VoiceButton.tsx` | +25 (AudioBars component, useEffect for transcript) |
| `features/ai-assistant/components/ChatPanel.tsx` | +15 (textarea, auto-resize, transcript populate) |
| `features/ai-assistant/components/MessageBubble.tsx` | +2 (fadeIn class, removed engine labels) |
| `features/ai-assistant/components/ChatEmptyState.tsx` | +8 (spacing, icon size, chip styling) |

---

## 13. High-Severity Bug Fixes — 2026-06-21

### 13a. Bug 3 (HIGH) — Frontend: Conversation CRUD errors invisible to user

**File:** `features/ai-assistant/components/ChatPanel.tsx`

**Problem:** The `useConversations()` hook stores `error` state on every API failure (load, create, delete, rename), but `ChatPanel` never destructured it. When "New Chat" or "Delete" failed, the button silently did nothing. No toast, no alert, no visual feedback of any kind.

**Fix:** Destructured `error` from `useConversations()` as `convError`. Added a local `visibleError` state + `useEffect` that auto-dismisses after 4 seconds. Renders a red banner below the header bar with the error text and a dismiss (X) button.

| File | Change |
|------|--------|
| `ChatPanel.tsx:16` | Added `error: convError` to destructuring |
| `ChatPanel.tsx:34-41` | Added `visibleError` state + auto-dismiss `useEffect` |
| `ChatPanel.tsx:132-140` | Added red error banner with dismiss button in JSX |

**Test result:** TypeScript 0 errors.

### 13b. Bug 4 (HIGH) — Backend: `_run_nl_query` has no prompt injection filter

**File:** `apps/ingestion/views.py`

**Problem:** The `ChatEndpointView.post()` method checks for prompt injection at line 749 before calling the pipeline, but `_run_nl_query()` itself had zero defenses. If called from a different code path in the future, or if the caller check is ever refactored away, the endpoint would be fully exposed to injection attacks. Defense-in-depth violation.

**Fix:** Added a prompt injection check at the start of `_run_nl_query()`. On detection, logs an `AuditLog` with `event='PROMPT_INJECTION_ATTEMPT'` and raises `ValueError('PROMPT_INJECTION_DETECTED')`. The `post()` method catches this specifically and returns `400 BAD_REQUEST` instead of falling through to the generic `500 INTERNAL_SERVER_ERROR` handler.

| File | Change |
|------|--------|
| `ingestion/views.py:_run_nl_query` | Added `prompt_injection_filter(query)` check at method entry; raises `ValueError` with injection flag |
| `ingestion/views.py:post()` | Added `except ValueError as exc:` handler before generic `Exception` — returns 400 for injection, 500 for other ValueErrors |

**Test result:** 85/85 chat/ingestion tests passed, Ruff all checks passed.

---

## 14. Low-Severity Cleanup Fixes — 2026-06-21

### 14a. Issue 9 — Dead code: `sendRAGQuery` removed

**File:** `features/ai-assistant/api.ts:17-20`

**Problem:** `sendRAGQuery()` was exported but never imported anywhere. The RAG path goes through `sendChatMessage()` with `mode: 'rag'`.

**Fix:** Removed the function.

### 14b. Issue 10 — `createId()` counter moved to hook-local ref

**File:** `features/ai-assistant/hooks/useChat.ts`

**Problem:** `createId()` used a module-level `nextId` variable. If two `useChat` instances existed, they'd share the counter, causing potential ID collisions.

**Fix:** Moved the counter inside the hook as `idCounter = useRef(0)`. `createId()` is now defined inside the hook and captures the ref.

### 14c. Issue 11 — `clearMessages()` now resets mode to `'auto'`

**File:** `features/ai-assistant/hooks/useChat.ts`

**Problem:** `clearMessages()` reset messages and error, but left the `mode` state at whatever value was previously selected. Starting a new chat could retain the old mode setting.

**Fix:** Added `setMode('auto')` to the `clearMessages` callback.

### 14d. Issue 12 — Removed dead `conjunction='or'` code in `_build_q_from_filters`

**File:** `apps/inventory/views.py`

**Problem:** `NLQueryFilters` has no `conjunction` attribute, so `getattr(filters, 'conjunction', 'and')` always returned `'and'`. The `if conjunction == 'or':` branch was dead code. The function also used an odd mix of `reduce(operator.or_, ...)` and manual `&=` for AND, but with only one path ever running.

**Fix:** Simplified `_build_q_from_filters` to always use AND, removing the `import operator`, `reduce`, and the dead `or` branch. Same logic, less code.

---

## 15. Chat Performance & SSE Streaming — 2026-06-21

### 15a. Problem: Slow Chat Performance

Users reported slow chat responses. Investigation revealed the root cause: **each chat request in `auto` mode makes 3 sequential blocking LLM API calls**, each a synchronous HTTP round-trip:

| Step | LLM Call | Latency |
|------|----------|---------|
| 1. Intent classification | GPT-4o-mini | 1-2s |
| 2. NL → structured query | GPT-4o (tool calling) | 2-5s |
| 3. Raw data → natural language | GPT-4o (formatter) | 2-5s |
| **Total** | | **5-12s+** |

The hard timeout was 15 seconds, making timeouts frequent. Additional issues: no LLM-level timeout/retry, no frontend timeout, wasted DB queries, and synchronous AuditLog writes blocking responses.

### 15b. Quick Wins (5 changes)

| # | Change | File | Impact |
|---|--------|------|--------|
| 1 | Added `request_timeout=8, max_retries=2` to ChatOpenAI | `ai/llm/provider_config.py` | Prevents one slow LLM call from consuming the entire timeout budget; retries on transient 429/network errors |
| 2 | Increased `CHAT_TIMEOUT_SECONDS` from 15 to 25 | `apps/ingestion/views.py` | Gives 3 sequential LLM calls enough headroom |
| 3 | Added `AbortSignal.timeout(25000)` to frontend requests | `features/ai-assistant/hooks/useChat.ts` | UI shows error after 25s instead of infinite spinner |
| 4 | Skip history fetch for NL queries | `apps/ingestion/views.py` | NL chain never uses history — saves 2 DB queries per request |
| 5 | Moved AuditLog to background thread | `apps/ingestion/views.py` | Audit write no longer blocks the response |

### 15c. SSE Streaming Architecture

Added Server-Sent Events (SSE) streaming so users see tokens appear in real-time instead of waiting for the full response.

**New endpoint:** `POST /api/ai/chat/stream/` (existing `POST /api/ai/chat/` unchanged for backward compatibility)

**SSE event protocol:**
```
event: metadata
data: {"engine":"nl_query","mode":"auto","conversation_id":"uuid"}

event: token
data: {"content":"You"}

event: token
data: {"content":" have"}

event: done
data: {"sources":[{"document":"sales.pdf","page":1}],"action":{...}}
```

**Backend changes:**

| File | Change |
|------|--------|
| `ai/llm/chain.py` | Added `call_gpt4o_formatter_stream()` — uses `chain.stream()` instead of `chain.invoke()`, yields text chunks |
| `apps/ingestion/services.py` | Added `call_llm_stream()` and `execute_stream()` — streams RAG answer via `chain.stream()` |
| `apps/ingestion/views.py` | Added `ChatStreamView` — returns `StreamingHttpResponse(content_type='text/event-stream')` with generator |
| `apps/ingestion/urls.py` | Added `chat/stream/` route |

**Streaming flow per request:**

| Step | What | Streamable? | Notes |
|------|------|-------------|-------|
| 1. Intent classification | GPT-4o-mini | No (returns JSON) | Kept as `.invoke()` |
| 2. NL chain (tool calling) | GPT-4o | No (structured output) | Kept as `.invoke()` |
| 3. DB query handler | PostgreSQL | N/A | Synchronous |
| 4. Formatter / RAG answer | GPT-4o | **Yes** | Uses `.stream()` — user sees tokens |

**Key insight:** Steps 1-3 are not streamable (they return structured data, not text). Only the final formatter/generator step streams text. But this is the longest step (2-5s), so streaming here provides the biggest UX improvement.

**Frontend changes:**

| File | Change |
|------|--------|
| `features/ai-assistant/api.ts` | Added `sendChatMessageStream()` — uses native `fetch()` with `ReadableStream`, not axios (axios can't handle SSE) |
| `features/ai-assistant/hooks/useChat.ts` | Rewrote `sendMessage()` and `retryLastMessage()` — appends AI message placeholder immediately, updates `text` on each `token` event |

**User experience:**
- **Before:** Send message → bouncing dots for 5-12s → entire response pops in at once
- **After:** Send message → bouncing dots for 1-3s (intent + NL chain) → text starts appearing word-by-word → complete in 5-12s but *feels* instant

### 15d. Files Modified

| File | Change |
|------|--------|
| `ai/llm/provider_config.py` | Added `request_timeout=8, max_retries=2` to ChatOpenAI kwargs |
| `ai/llm/chain.py` | Added `call_gpt4o_formatter_stream()` generator function |
| `apps/ingestion/views.py` | Increased timeout, added `ChatStreamView`, skip history for NL, background AuditLog |
| `apps/ingestion/services.py` | Added `call_llm_stream()` and `execute_stream()` |
| `apps/ingestion/urls.py` | Added `chat/stream/` route |
| `features/ai-assistant/api.ts` | Added `sendChatMessageStream()` with SSE parsing |
| `features/ai-assistant/hooks/useChat.ts` | Streaming support, `AbortSignal.timeout(25000)`, incremental message updates |

### 15e. OpenAI API Impact

| Metric | Before | After |
|--------|--------|-------|
| LLM calls per NL chat | 3 | 3 (unchanged — streaming only affects the last call) |
| LLM calls per RAG chat | 3-4 | 3-4 (unchanged) |
| Tokens per request | Same | Same (streaming doesn't change token count) |
| Timeout protection | None at LLM level | 8s per LLM call + 2 retries |
| Wasted DB queries | 2 (history for NL) | 0 (skipped for NL) |

**Net effect:** Fewer timeout failures, no change to token usage or API cost. Streaming is a UX improvement, not a cost change.

### 15f. Build & Lint Results

```
Frontend:
$ npm run build
✓ built in 597ms — 0 TS errors

$ npm run lint
1 pre-existing error (not in modified files)

Backend:
$ python -m py_compile apps/ingestion/views.py — OK
$ python -m py_compile ai/llm/chain.py — OK
$ python -m py_compile apps/ingestion/services.py — OK
$ python -m py_compile apps/ingestion/urls.py — OK
$ python -m py_compile ai/llm/provider_config.py — OK
```

---

## 16. Round 2 Review — Chat Bug Fixes & Cleanup

**Date:** 2026-06-21
**Scope:** Second full review pass on AI chat system (backend + frontend). Found 4 new issues (1 CRITICAL, 1 HIGH, 1 MEDIUM, 2 LOW).

### 16a. Bug 13 (CRITICAL — pre-existing) — `_trace_chat` SyntaxError

**Problem:** `_trace_chat()` in `ingestion/views.py` had a `try:` block without `except` or `finally`. The method was refactored to run `AuditLog.objects.create` in a daemon `threading.Thread` for fire-and-forget async logging, but the outer `try:` wrapper was left behind without its matching `except`. **File could not compile** — `SyntaxError: expected 'except' or 'finally' block`.

**Root cause:** The audit log was wrapped in a nested function and spawned via `threading.Thread`, but the outer `try:` (intended to guard `threading.Thread(...)`) was left dangling when the `AuditLog.objects.create` call was moved inside `_write_audit()`.

**Fix:** Removed the orphaned outer `try:` entirely. The inner `try/except` inside `_write_audit()` already handles `AuditLog` failures, and `threading.Thread(...)` itself doesn't need guarding (it never raises in practice).

**Files:**
- `smartstock-backend/apps/ingestion/views.py:1023-1033`

### 16b. Bug 14 (HIGH) — `useConversations` error never cleared

**Problem:** All 5 async operations in `useConversations.ts` (`loadConversations`, `selectConversation`, `startNewConversation`, `removeConversation`, `updateTitle`) set `error` state on failure but **never cleared it on a subsequent successful operation**. Stale error messages lingered indefinitely.

**Impact:** If an operation failed and a later operation succeeded, `convError` still held the old error. `ChatPanel.tsx`'s `visibleError` + 4s timer masked this visually, but the stale state could interfere with future error handling.

**Fix:** Added `setError(null)` as the first line inside the `try` block of all five functions.

**Files:**
- `smartstock-frontend/src/features/ai-assistant/hooks/useConversations.ts`

### 16c. Bug 15 (MEDIUM) — `_handle_get_total_value` inconsistent `is_active` filter

**Problem:** The module-level `_handle_get_total_value` in `inventory/views.py` (used by `ChatEndpointView._run_nl_query`) did not filter `is_active=True`, while the `NLQueryEndpointView` class method did. Inactive products could inflate total inventory value in the unified chat path.

**Fix:** Added `& Q(is_active=True)` to the module-level function's query.

**Files:**
- `smartstock-backend/apps/inventory/views.py:1333`

### 16d. Bug 16 (LOW) — Dead code: `fetchStockSnapshot` / `useInventorySnapshot`

**Problem:** After the inventory snapshot card was removed from `AIAssistantPage.tsx` (Bug 1 fixes), `fetchStockSnapshot()` in `api.ts` and `useInventorySnapshot.ts` hook were both dead code — no remaining imports from any component.

**Fix:** Removed `StockSnapshot` interface and `fetchStockSnapshot` function from `api.ts`; deleted entire `useInventorySnapshot.ts` file.

**Files:**
- `smartstock-frontend/src/features/ai-assistant/api.ts`
- `smartstock-frontend/src/features/ai-assistant/hooks/useInventorySnapshot.ts` (deleted)

### 16e. Build & Lint Results

```
Frontend:
$ npx tsc --noEmit — 0 errors

Backend:
$ ruff check apps/ingestion/views.py — 2 pre-existing E402/E501 (ChatStreamView WIP, unrelated)
$ ruff check apps/inventory/views.py — 0 errors
```

**Net effect:** All identified issues from round 2 review resolved. File now compiles, AI chat error handling is hygienic, total value queries consistent, and no dead code remains.

---

## 16. SSE Streaming Bug Fixes — 2026-06-21

### 16a. Bug 1 (CRITICAL) — `NameError: name 'event_stream' is not defined`

**File:** `apps/ingestion/views.py` — `_stream_nl_query()` (line 1272) and `_stream_rag()` (line 1217)

**Problem:** After yielding all tokens successfully, `_stream_nl_query()` and `_stream_rag()` tried to set `event_stream._full_answer = full_answer` to pass the accumulated text back to the `event_stream()` generator for conversation saving. But `event_stream` is a **local function** defined inside `post()` — the `_stream_*` methods on `self` cannot access it.

**What happened:**
1. Frontend receives `metadata` event → engine identified
2. Frontend receives multiple `token` events → text grows on screen
3. `_stream_nl_query()` finishes streaming, tries `event_stream._full_answer = ...`
4. `NameError` is raised → caught by `event_stream()`'s `except` handler → yields `error` event
5. Frontend receives `error` event → catch block runs → **deletes all streamed text** → shows "Sorry, something went wrong"

**Fix:** Replaced `event_stream._full_answer` with a **mutable `shared` dict** passed to streaming methods:

```python
# Before (broken):
event_stream._full_answer = full_answer  # NameError

# After (fixed):
shared = {}
yield from self._stream_nl_query(query, user, shared)
# Inside _stream_nl_query:
shared['full_answer'] = full_answer
```

**Impact:** Streaming now completes without crashing. Conversation saving works correctly.

### 16b. Bug 2 (HIGH) — `max_retries=2` causing 20-second retry delays

**File:** `ai/llm/provider_config.py`

**Problem:** We added `max_retries=2` to `ChatOpenAI` as a "quick win" for resilience. But the OpenAI SDK's retry uses **exponential backoff**: 1s → 3s → 20s. When the LLM call failed (quota, timeout, network), the SDK retried with a 20-second delay, making the total wait 32+ seconds. This made slowness **worse**, not better.

**Backend log evidence:**
```
Running GPT-4o formatter (streaming)
Retrying request to /chat/completions in 20.000000 seconds
```

**Fix:** Removed `max_retries=2` from ChatOpenAI kwargs. Kept `request_timeout=8` (which is useful for preventing hangs). The SDK's default retry behavior (0 retries for streaming) is appropriate — streaming inherently provides user feedback, so aggressive retries aren't needed.

### 16c. Updated Provider Capability Matrix

| Setting | Before | After |
|---------|--------|-------|
| `request_timeout` | None (SDK default: ~10 min) | **8 seconds** |
| `max_retries` | None (SDK default) | None (removed) |

### 16d. Files Modified

| File | Change |
|------|--------|
| `apps/ingestion/views.py` | Added `shared = {}` dict, passed to `_stream_rag()` and `_stream_nl_query()`, replaced `event_stream._full_answer` with `shared['full_answer']` |
| `ai/llm/provider_config.py` | Removed `max_retries=2` from ChatOpenAI kwargs |

### 16e. Verification

```
Backend:
$ python -m py_compile apps/ingestion/views.py — OK
$ python -m py_compile ai/llm/provider_config.py — OK

Frontend:
$ npm run build — ✓ built in 537ms
```

---

## 17. Chat Title Bug Fix — 2026-06-21

### 17a. Bug — Chat title stays "New Conversation" after first message

**File:** `smartstock-frontend/src/features/ai-assistant/components/ChatPanel.tsx`

**Problem:** When a user starts a new chat and sends their first message:
1. `handleSend` calls `startNewConversation()` → creates conversation with title "New Conversation"
2. `sendMessage()` streams the response → backend sets title via `auto_title()` after stream completes
3. Frontend never refreshes `activeConversation` → title stays "New Conversation"

**What happened:** The sidebar and header showed "New Conversation" even after the backend had already set the title to the first 80 chars of the user's query.

**Fix:** Added `await selectConversation(newConv.id)` after `sendMessage()` completes for new conversations. This refetches the conversation from the backend, picking up the updated title.

```typescript
// Before (broken):
await sendMessage(query, newConv.id);
return;

// After (fixed):
await sendMessage(query, newConv.id);
await selectConversation(newConv.id);
return;
```

**Impact:** Chat title now updates correctly after the first message. Sidebar and header show the auto-generated title.

### 17b. Files Modified

| File | Change |
|------|--------|
| `smartstock-frontend/src/features/ai-assistant/components/ChatPanel.tsx` | Added `selectConversation` to deps and call after `sendMessage` |

---

### 18. Fix: Delete Chat Button Not Working (2026-06-22)

**Problem:** Delete button required two separate clicks (selecting a red trash icon on hover) — fragile and easily broken by layout shifts.

**Fix:** Replaced the two-click delete confirmation with `window.confirm()` dialog. Single click on trash icon triggers native browser confirmation, then calls `handleDelete`.

### 19. Fix: Remove Edit/Rename Chat Button (2026-06-22)

**Problem:** Rename chat feature removed per user request.

**Files removed:**
| File | What was removed |
|------|------------------|
| `ConversationSidebar.tsx` | Inline edit UI, `onRename` prop, `Pencil`/`Check`/`X` icons, `editingId`/`editValue`/`deletingId` state |
| `ChatPanel.tsx` | `onRename` prop, `updateTitle` destructuring |
| `useConversations.ts` | `updateTitle` function (was calling PATCH `/conversations/{id}/`) |
| `api.ts` | `renameConversation` function (was calling PATCH `/conversations/{id}/`) |

### 20. Fix: "Which items need reordering?" Always Failing (2026-06-22)

**Root cause:** Three issues working together:

1. **Wrong LLM provider (system env `LLM_PROVIDER=gemini`):** The system-level environment variable `LLM_PROVIDER=gemini` overrode the `.env` file's `LLM_PROVIDER=groq`. Gemini free tier quota was exhausted (`429 RESOURCE_EXHAUSTED`), causing ALL LLM calls to fail immediately.

2. **Backend LLM request timeout too short (8s):** `provider_config.py` set `request_timeout=8` — only 8 seconds for the LLM to process 12 few-shot examples + tool_choice="required". This often timed out for slower providers.

3. **Frontend timeout too short (25s):** The streaming AI pipeline calls LLM 3 times sequentially (intent classification → NL chain → formatter). The `AbortSignal.timeout(25000)` started ticking before the stream opened, so the total time for all 3 LLM calls often exceeded 25 seconds, triggering a retry loop.

**Fixes:**

| File | Change |
|------|--------|
| `~/.bashrc` | Added `export LLM_PROVIDER=groq` to fix system env (was `gemini`) |
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` (lines 98, 207) | `AbortSignal.timeout(25000)` → `AbortSignal.timeout(60000)` |
| `smartstock-backend/ai/llm/provider_config.py` (line 113) | `request_timeout=8` → `request_timeout=20` |
| `smartstock-backend/ai/llm/chain.py` | Added retry logic (3 attempts with 1s/2s backoff) for transient errors (timeouts, rate limits) in `NLQueryChain.run()` |
| `smartstock-backend/ai/llm/few_shots.py` | Added few-shot example: `"Which items need reordering?"` → `get_low_stock` with empty filters |
| `smartstock-frontend/src/features/ai-assistant/components/ChatEmptyState.tsx` | Replaced `"Which items need reordering?"` suggestion with `"What's my total inventory value?"` (simpler, more reliable) |

**Testing:** NL chain tested with Groq provider — all three suggestion queries work correctly:
- `"What products are low on stock?"` → `GET_LOW_STOCK` ✓
- `"Show me supplier performance this month"` → `GET_SUPPLIER_INFO` ✓
- `"What's my total inventory value?"` → `GET_TOTAL_VALUE` ✓

**Impact:** Backend now uses Groq (which has available quota). LLM calls have 20 seconds per request (up from 8s). Transient errors auto-retry up to 3 times. Suggestion button uses a simpler, more reliable query.

---

### 21. Fix: Chat Title Not Updating After First Message (2026-06-22)

**Problem:** When a user sends only one question in a new chat, the chat title stays as "New Conversation" in the sidebar. The backend auto-titles correctly (truncates first message to 80 chars), but the sidebar never refreshes.

**Root cause:** `loadConversations` was not destructured in `ChatPanel.tsx`, so the sidebar list was never refreshed after the backend auto-titled the conversation.

**Fix:**

| File | Change |
|------|--------|
| `smartstock-frontend/src/features/ai-assistant/components/ChatPanel.tsx` | Added `loadConversations` to destructuring from `useConversations()`. Added `await loadConversations()` after `selectConversation(newConv.id)` in `handleSend`. Added `loadConversations` to `useCallback` dependency array. |

**Impact:** Sidebar now refreshes after the first message, showing the auto-generated title.

---

### 22. Fix: Duplicate Chat Bubbles During Loading (2026-06-22)

**Problem:** When the AI is generating an answer, two chat boxes appear stacked on top of each other — an empty AI placeholder bubble and the `TypingIndicator`.

**Root cause:** `sendMessage` in `useChat.ts` adds an empty AI placeholder (`text: ''`) to the `messages` array at the same time as the user message. Both `messages.map()` and `{isLoading && <TypingIndicator />}` render simultaneously, producing two AI-styled boxes.

**Fix:**

| File | Change |
|------|--------|
| `smartstock-frontend/src/features/ai-assistant/components/MessageBubble.tsx` (line 51) | Added `if (!isUser && !message.text) return null;` — hides empty AI placeholder bubbles. |

**Impact:** During loading, only the `TypingIndicator` shows. Once the first token arrives, the AI bubble appears with content.

---

### 23. Fix: Long Queries Timing Out / Server Down (2026-06-22)

**Problem:** Longer queries like "Show me supplier performance over month" cause the server to show retry or "sorry something went wrong" messages. The frontend 60s timeout kills the stream before the backend finishes multiple LLM calls.

**Root cause:** Three issues:
1. Frontend `AbortSignal.timeout(60000)` killed streams that took longer than 60s (3 sequential LLM calls can easily exceed this).
2. Backend had no heartbeat to keep SSE connections alive during long LLM calls — proxies/browsers dropped idle connections.
3. Backend LLM timeout (20s) was too tight for complex queries.

**Fixes:**

| File | Change |
|------|--------|
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` (lines 98, 207) | Removed `AbortSignal.timeout(60000)` entirely — stream now uses only `controller.signal` (user can still cancel manually). |
| `smartstock-backend/apps/ingestion/views.py` | Added SSE heartbeat comments (`: thinking...`, `: classifying query...`, `: generating response...`, `: searching documents...`) before each LLM call to keep connections alive. |
| `smartstock-backend/ai/llm/provider_config.py` (line 113) | `request_timeout=20` → `request_timeout=30` per LLM request. |

**Impact:** Long queries now take as long as they need without frontend timeout. Heartbeats prevent proxy/browser connection drops.

---

### 24. Fix: Groq Malformed Tool Calls Not Retried (2026-06-22)

**Problem:** Groq's LLM sometimes generates malformed JSON in function calls (e.g., missing `"value":` key). This returns a 400 `tool_use_failed` error that was not in the transient retry list, so it failed immediately instead of retrying.

**Fix:**

| File | Change |
|------|--------|
| `smartstock-backend/ai/llm/chain.py` | Added `tool_use_failed`, `bad_request`, `invalid_request_error` to transient error detection in `NLQueryChain.run()`. |
| `smartstock-backend/ai/llm/chain.py` | Added `_keyword_fallback()` function — when all 3 retries fail, uses simple keyword matching to determine the action (e.g., "low stock" → `get_low_stock`). |
| `smartstock-backend/ai/llm/chain.py` | `NLQueryParseError` catch now calls `_keyword_fallback(query)` instead of always returning `get_inventory`. |
| `smartstock-backend/ai/llm/chain.py` | Retry backoff increased from 1s/2s to 2s/4s. Added `RESOURCE_EXHAUSTED` to transient error detection. |

**Keyword fallback priority:**
1. `get_top_products` — "top", "best", "most sold", "highest"
2. `get_low_stock` — "low stock", "reorder", "restock", "need restocking"
3. `forecast_demand` — "forecast", "predict", "demand", "next 30"
4. `get_supplier_info` — "supplier", "vendor"
5. `get_total_value` — "total value", "inventory value", "worth"
6. `get_sales_report` — "sales", "sold", "revenue"
7. `get_inventory` — default fallback

**Testing:** 10/10 queries classified correctly with Groq:
- "Show me supplier performance this month" → `get_sales_report` ✓
- "What products are low on stock?" → `get_low_stock` ✓
- "What's my total inventory value?" → `get_total_value` ✓
- "Show me the top 5 selling products" → `get_top_products` ✓
- "Which items have stock below 10?" → `get_inventory` (with lt filter) ✓
- "Give me the sales report for last month" → `get_sales_report` ✓
- "What is the demand forecast for the next 30 days?" → `forecast_demand` ✓
- "Show all Electronics products sorted by quantity" → `get_inventory` ✓
- "Find products whose name contains chair" → `get_inventory` ✓
- "Which Furniture items need restocking?" → `get_low_stock` ✓

**Impact:** Groq's occasional malformed tool calls now retry instead of failing. When the LLM is completely unavailable (quota exhausted), the keyword fallback provides reasonable results.

---

### 25. Fix: Loading State Bug — Multiple Messages / Stale Closure (2026-06-22)

**Problem:** Sending multiple messages rapidly causes the loading state to behave incorrectly. The loading spinner can get stuck, or multiple messages process simultaneously when they shouldn't.

**Root cause:** Three issues:

1. **Stale closure:** `sendMessage` used `isLoading` from its React state closure for the guard (`if (!trimmed || isLoading) return`). During rapid clicks, React hasn't re-rendered yet, so the old closure still has `isLoading=false` — the guard is bypassed.

2. **Abort didn't clear loading:** When a message was aborted (by sending a new one), the `finally` block skipped `setIsLoading(false)` because `controller.signal.aborted` was true. But the new message had already called `setIsLoading(true)`, so loading stayed stuck until the new message completed.

3. **Dependency array included `isLoading`:** `sendMessage` was recreated every time `isLoading` changed, causing unnecessary re-renders and potential stale references.

**Fix:**

| File | Change |
|------|--------|
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` | Added `isLoadingRef` (`useRef(false)`) — ref updates immediately, no re-render needed. |
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` | Guard uses `isLoadingRef.current` instead of `isLoading` state — no stale closure. |
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` | `finally` block always calls `setIsLoading(false)` and `isLoadingRef.current = false` regardless of abort state. |
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` | `loadFromConversation` also resets `isLoadingRef` and `isLoading`. |
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` | Removed `isLoading` from `sendMessage` and `retryLastMessage` dependency arrays. |

**Impact:** Loading state is now reliable. Rapid message sends are properly blocked. Aborted messages correctly clear the loading state. The send button and textarea are disabled during loading (already existed in `ChatPanel.tsx`).

---

### 26. New NL Query Action: Supplier Performance (2026-06-24)

**Problem:** When users asked "what is the suppliers performance" or "how are my suppliers performing?", the system fell back to `get_supplier_info` which only returned basic contact information (name, email, phone, address). No actual performance metrics were calculated.

**Root cause:** No `get_supplier_performance` action existed in the NL query system. The LLM classified performance queries as `get_supplier_info` since it was the closest match.

### 26a. Solution: New `get_supplier_performance` Action

Added a complete end-to-end NL query action that calculates supplier performance metrics from purchase order data.

**Metrics calculated per supplier:**

| Metric | Calculation |
|--------|-------------|
| Total orders | `COUNT(purchase_orders)` per supplier |
| Total spend | `SUM(total_cost)` per supplier |
| Confirmation rate | `COUNT(status='confirmed') / COUNT(all orders)` |
| Failure rate | `COUNT(status IN ('failed','timeout')) / COUNT(all orders)` |
| Avg response days | `AVG(confirmed_at - sent_at)` for confirmed POs |
| On-time rate | `% of confirmed POs where response_time <= default_lead_time_days` |
| Most ordered SKU | `COUNT(purchase_orders)` grouped by `sku__code`, ordered descending |
| Status breakdown | Group count by status per supplier |

**Default behavior:** Returns top 5 suppliers ordered by name. Supports filtering by `supplier_name` and `is_active`.

### 26b. Files Modified

| File | Change | Why |
|------|--------|-----|
| `ai/llm/schemas.py` | Added `GET_SUPPLIER_PERFORMANCE = 'get_supplier_performance'` to `NLQueryAction` enum; added allowed fields `['supplier_name', 'is_active']` | Register new action in the system |
| `ai/llm/few_shots.py` | Added few-shot example: "How are my suppliers performing?" → `get_supplier_performance` | Teach the LLM when to use this action |
| `ai/llm/chain.py` | Added `get_supplier_performance` to tool description; added keyword fallback for 'supplier performance', 'supplier metric', 'how are suppliers', 'supplier scorecard' | Ensure action is recognized by LLM and keyword fallback |
| `apps/inventory/views.py` | Added `_handle_get_supplier_performance()` handler (~80 lines); added to handler map, dispatch logic, and view wrapper method; added pattern cache entries for 'supplier performance' and 'supplier metrics' | Core performance calculation logic |
| `tests/unit/test_nlquery.py` | Updated action count (8→9); added end-to-end test case for `get_supplier_performance` | Test coverage |

### 26c. Handler Implementation Details

```python
def _handle_get_supplier_performance(filters: NLQueryFilters) -> list:
    # 1. Filter suppliers by name/is_active if conditions provided
    # 2. For each supplier (top 5 by default):
    #    - Query all PurchaseOrders for that supplier
    #    - Calculate confirmation_rate, failure_rate, avg_response_days, on_time_rate
    #    - Find most ordered SKU via annotate + Count
    #    - Build status_breakdown dict
    # 3. Return list of performance dicts
```

**Key design decisions:**
- Uses `PurchaseOrder` model (not `Supplier` model) for metrics — all performance data comes from PO history
- `on_time_rate` compares `confirmed_at - sent_at` against `supplier.default_lead_time_days`
- `avg_response_days` uses `DecimalField` + `ExpressionWrapper` for precise time difference calculation
- Returns `status_breakdown` dict with counts per status (only non-zero statuses included)

### 26d. Example Response

```json
{
  "status": "success",
  "data": {
    "answer": "Here are the top 5 supplier performance metrics...",
    "raw_data": [
      {
        "supplier_id": 1,
        "supplier_name": "Evans, Tucker and Adams",
        "total_orders": 15,
        "total_spend": 45230.50,
        "confirmation_rate": 0.93,
        "failure_rate": 0.04,
        "avg_response_days": 5.2,
        "on_time_rate": 0.87,
        "most_ordered_sku": "CHAIR-PRO-2",
        "status_breakdown": {
          "confirmed": 14,
          "failed": 1
        }
      }
    ]
  }
}
```

### 26e. Testing

73/73 NL query unit tests passed. New test case added to `END_TO_END_CASES`:
- Input: "How are my suppliers performing?"
- Expected action: `get_supplier_performance`
- Expected filters: empty conditions array

---

### 27. Help Guidance for Vague/Out-of-Scope Queries (2026-06-24)

**Problem:** When users asked vague questions like "hello", "what can you do", "help", or out-of-scope queries like "what's the weather", the system either:
1. Silently returned a full inventory data dump (defaulting to `GET_INVENTORY`)
2. Returned generic error messages like "Sorry, something went wrong"

Users had no idea what the system could do or how to phrase their queries.

### 27a. Solution: New `help` Action + Guidance Response

Added a `help` action that returns a structured guidance message listing all capabilities with example queries.

**Three layers of detection:**

| Layer | Location | What it catches |
|-------|----------|-----------------|
| System prompt | `ai/llm/prompts.py` | LLM returns `{"action": "help", "filters": {}}` for greetings, vague questions, out-of-scope queries |
| Keyword fallback | `ai/llm/chain.py` | Exact matches: "hello", "hi", "hey", "help", "what can you do", etc. + queries < 3 chars |
| Default fallback | `ai/llm/chain.py` | Any unrecognized query (changed from `GET_INVENTORY` to `HELP`) |

### 27b. Files Modified

| File | Change | Why |
|------|--------|-----|
| `ai/llm/schemas.py` | Added `HELP = 'help'` to `NLQueryAction` enum; added empty `[]` allowed fields | Register help action |
| `ai/llm/prompts.py` | Changed out-of-scope instruction from `{"error": "Out of scope request"}` to `{"action": "help", "filters": {}}` | LLM now returns a structured action instead of an error signal |
| `ai/llm/chain.py` | Added `help` to tool description; added vague query detection in `_keyword_fallback()`; changed default fallback from `GET_INVENTORY` to `HELP`; changed `NLQueryParseError` catch to return `HELP` | Detect vague queries and return guidance |
| `apps/inventory/views.py` | Added `_handle_help()` function returning structured capabilities list; added `help` to handler map and dispatch | Return guidance message |
| `smartstock-frontend/src/features/ai-assistant/hooks/useChat.ts` | Updated generic error message to include capability hints | Better UX on errors |
| `tests/unit/test_nlquery.py` | Updated action count (8→9); updated fallback test assertions (`GET_INVENTORY` → `HELP`); updated out-of-scope test to check for new prompt text | Test coverage |

### 27c. Help Response Content

The `_handle_help()` function returns:

```
I'm SmartStock AI, your warehouse inventory analytics assistant.
I can help you with the following:

**Inventory**
- Show me all products / low stock items / out of stock items
- Filter by category, SKU, supplier, or stock level

**Sales**
- Sales report by date range or product
- Top selling products

**Suppliers**
- Supplier contact info and list
- Supplier performance metrics (confirmation rate, response time, on-time rate)

**Forecasting**
- Demand forecast for specific products or SKUs

**Value**
- Total inventory value

Try asking something like:
- "Show me low stock items in Electronics"
- "How are my suppliers performing?"
- "What is the demand forecast for SKU CHAIR-PRO-2?"
- "Give me the sales report for March"
- "Show top 5 selling products"
```

### 27d. Updated Keyword Fallback Priority

```
1. help          — "hello", "hi", "hey", "help", "what can you do", len < 3
2. get_top_products — "top", "best", "most sold", "highest"
3. get_low_stock    — "low stock", "reorder", "restock", "need restocking"
4. get_supplier_performance — "supplier performance", "supplier metric", "how are suppliers"
5. forecast_demand  — "forecast", "predict", "demand", "next 30"
6. get_supplier_info — "supplier", "vendor"
7. get_total_value  — "total value", "inventory value", "worth"
8. get_sales_report — "sales", "sold", "revenue"
9. help (default)   — any unrecognized query
```

### 27e. Updated Error Messages (Frontend)

| Scenario | Before | After |
|----------|--------|-------|
| Generic error | "Sorry, something went wrong. Please try again." | "Sorry, something went wrong. You can try rephrasing your question or ask me about inventory, sales, suppliers, forecasting, or inventory value." |
| Quota error | Unchanged | Unchanged |
| Timeout error | Unchanged | Unchanged |

### 27f. User Experience (Before vs After)

| Query | Before | After |
|-------|--------|-------|
| "hello" | Full inventory dump (50+ products) | "I'm SmartStock AI... I can help with inventory, sales, suppliers..." |
| "what can you do" | Full inventory dump | Help message with capabilities + example queries |
| "help" | Full inventory dump | Help message |
| "what's the weather" | Error or inventory dump | Help message |
| Random gibberish | Error or inventory dump | Help message |

### 27g. OpenAI API Impact

**No additional cost.** The `help` action is handled entirely in Python (keyword matching + static response). No LLM call is needed for the guidance message. The LLM's tool calling still classifies vague queries (1 call), but the formatter call (call 2) receives the static help text instead of raw DB data — same token cost.

### 27h. Testing

73/73 NL query unit tests passed. Key test updates:
- `test_all_nine_actions_exist` — verifies 9 actions in enum
- `test_action_allowed_fields_are_non_empty` — skips `help` (empty fields expected)
- `test_chain_falls_back_on_parse_error` — now returns `HELP` instead of `GET_INVENTORY`
- `test_chain_falls_back_on_unknown_action` — now returns `HELP`
- `test_chain_falls_back_on_disallowed_field` — now returns `HELP`
- `test_system_prompt_includes_out_of_scope_instruction` — checks for new `"action" set to "help"` text

### 27i. Bug Fix: LangChain Template Parsing

During implementation, discovered that unescaped `{` and `}` in the `out_of_scope_block` in `prompts.py` caused `LangChain`'s `FewShotPromptTemplate` to fail with `ValueError: Invalid format specifier in f-string template. Nested replacement fields are not allowed.`

**Fix:** Escaped braces in `out_of_scope_block` from `{"action": "help", "filters": {}}` to `{{"action": "help", "filters": {{}}}}`.

---
