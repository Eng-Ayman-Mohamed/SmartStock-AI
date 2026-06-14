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
