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
