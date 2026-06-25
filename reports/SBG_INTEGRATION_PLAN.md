# SBG Integration Plan — SmartStock AI

**Date:** 2026-06-25
**Author:** AI-generated
**Status:** Approved — implementation ready

---

## Overview

Integrate ITI Student Bedrock Gateway (SBG) as the primary LLM provider, with Groq and Gemini as limited fallbacks. SBG provides free access to AWS Bedrock models via `http://apiaccess.iti.net.eg/api/v1/student/`.

---

## A. Model Mapping (Calibrated from Test Results)

All models tested live against the actual SBG gateway on 2026-06-25.

| Feature | SBG Model | Latency | Status | Fallback |
|---------|-----------|---------|--------|----------|
| **Chat / RAG** | `openai.gpt-oss-120b-1:0` | 1.7s | ✅ | Groq `llama-3.3-70b-versatile` |
| **Classifier** | `openai.gpt-oss-safeguard-20b` | 2s | ✅ | Groq `llama-3.1-8b-instant` |
| **NL Query** | `deepseek.r1-v1:0` | 1.7s | ✅ | Groq `llama-3.3-70b-versatile` |
| **Formatter** | `openai.gpt-oss-120b-1:0` | 1.7s | ✅ | Groq `llama-3.3-70b-versatile` |
| **Vision** | `qwen.qwen3-vl-235b-a22b` | 3.7s | ✅ | Groq `meta-llama/llama-4-scout-17b-16e-instruct` |
| **Embeddings** | _(all region-blocked)_ | — | ❌ | Gemini `gemini-embedding-001` |
| **Whisper** | _(no audio model)_ | — | ❌ | Groq `whisper-large-v3` |

### Models that failed testing

| Model | Error | Root Cause |
|-------|-------|------------|
| All `anthropic.claude-*` | `BEDROCK_ERROR` | Needs AWS use-case approval on AWS side |
| All `amazon.nova-*` | `REGION_NOT_ALLOWED` | ITI region access not configured |
| All `stability.*` | `REGION_NOT_ALLOWED` | ITI region access not configured |
| All `amazon.titan-*`, `cohere.embed-*` | `REGION_NOT_ALLOWED` | ITI region access not configured |

---

## B. Implementation Steps

### Step 1: Create `ai/llm/sbg_client.py`

LangChain-compatible wrapper for SBG chat and vision endpoints.

**Wire format translation — Chat:**

```
LangChain input:
  [SystemMessage("You are a teacher"),
   HumanMessage("Explain binary search")]

SBG request (POST /api/v1/student/chat):
{
  "model_id": "openai.gpt-oss-120b-1:0",
  "messages": [
    {"role": "user", "content": "Explain binary search"}
  ],
  "system_prompt": "You are a teacher",
  "max_tokens": 2048
}

SBG response → LangChain AIMessage:
  AIMessage(content="Binary search is...")
```

**Wire format translation — Vision:**

```
SBG request (POST /api/v1/student/multimodal-chat):
{
  "model_id": "qwen.qwen3-vl-235b-a22b",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Extract invoice data..."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
      ]
    }
  ],
  "system_prompt": "You extract structured data...",
  "max_tokens": 4096
}

SBG response → raw content string (same as chat)
```

**Key design decisions:**
- `bind_tools()` returns `self` (no-op) — SBG doesn't support tool calling. See Risk #1 below.
- `stream()` buffers full response then yields once — no SSE support from SBG. Acceptable for MVP.
- Error mapping: `REGION_NOT_ALLOWED` → `ValueError`, `BEDROCK_ERROR` → `ConnectionError`
- `SBGClient` must expose `invoke()`, `stream()`, `bind_tools()`, and `with_structured_output()` to satisfy LangChain's `BaseChatModel` interface

### Step 2: Modify `ai/llm/provider_config.py`

- Add `sbg` entry to `_PROVIDERS` dict with `embedding_model: None` (triggers existing Cohere/Gemini fallback chain — no separate embeddings class needed)
- Modify `get_chat_llm()` → returns `SBGClient` when `PROVIDER=sbg`
- Modify `get_embeddings()` → SBG entry has `embedding_model: None`, existing fallback to Cohere then Gemini handles it automatically
- Modify `get_vision_client()` → returns `SBGClient(vision_model)` when `PROVIDER=sbg`
- Modify `get_whisper_client()` → logs info, falls through to Groq when `PROVIDER=sbg`
- Update module docstring to mention SBG

### Step 3: Modify `ai/llm/chain.py`

- `NLQueryChain.__init__()`: detect if LLM supports `bind_tools()` by checking `PROVIDER == 'sbg'`. If SBG, skip `bind_tools()` call and store raw LLM reference.
- `_parse_tool_call()`: when SBG, route to `_parse_sbg_response()` instead of checking `tool_calls`
- `_parse_sbg_response()`: strip markdown fences, parse JSON, validate against `NLQueryToolSchema` fields, extract `action`/`filters`, fall back to `_keyword_fallback()` on failure
- **Validation layer**: after parsing JSON, verify `action` is a valid `NLQueryAction` value and `filters` matches expected structure. Invalid → log warning + keyword fallback.

### Step 4: Modify `ai/multimodal/vision.py`

- `VisionExtractor.extract()`: dispatch to `_extract_sbg()` when provider is SBG
- `_extract_sbg()`: sends image as data URL to `POST /api/v1/student/multimodal-chat` with `{role, text, images}` format
- Reuse existing `_parse_json()` for response parsing (markdown fence stripping + JSON parse)

### Step 5: Update `.env.example`

- Add `SBG_API_KEY=` with comment: `# Required for SBG provider (LLM_PROVIDER=sbg)`
- Note: `XAI_API_KEY` is also missing from `.env.example` — add it for consistency

### Step 6: Tests

| File | What it tests |
|------|---------------|
| `tests/unit/ai/test_sbg_client.py` | Message translation (system prompt extraction), invoke, stream buffering, error mapping, bind_tools no-op |
| `tests/unit/ai/test_provider_config.py` | SBG config values, chat/vision/whisper resolution, embeddings fallback to Cohere/Gemini |
| `tests/unit/ai/test_sbg_nlq_chain.py` | NLQ without tool calling, JSON parsing, validation layer, keyword fallback, 10-sample accuracy baseline |

### Step 7: Integration verification

Run full NLQ pipeline with SBG provider to verify end-to-end:
1. `IntentClassifier` with `openai.gpt-oss-safeguard-20b`
2. `NLQueryChain` with `deepseek.r1-v1:0`
3. `call_gpt4o_formatter` with `openai.gpt-oss-120b-1:0`
4. `VisionExtractor` with `qwen.qwen3-vl-235b-a22b`

---

## C. Risk Register

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| 1 | **NLQ accuracy drops without tool calling.** Prompt-based JSON extraction is inherently less reliable than structured tool output. | Medium | Add validation layer (Step 3). Run 10-sample accuracy test. If <80%, add regex post-processor or fallback to Groq for NLQ only. |
| 2 | **`chain.py` hard-imports `ChatOpenAI` at module level (line 13).** If `langchain-openai` isn't installed, import fails even for SBG. | Low | `langchain-openai` is already in `requirements.txt`. SBGClient returns `AIMessage` which is `langchain-core` (always installed). No change needed. |
| 3 | **SBG endpoint availability.** ITI gateway may have uptime limits or rate limits not yet characterized. | Low | Fallback chain (Groq → Gemini) handles outages. Add health check ping in `SBGClient.__init__()`. |

---

## D. Files That Need NO Changes (Work Transparently)

| File | Rationale |
|------|-----------|
| `apps/ingestion/chat_pipeline.py` | Calls `provider_config.get_chat_llm()` indirectly |
| `apps/ingestion/views.py` | `_run_engine`, `_run_rag`, `_run_nl_query` all go through `get_llm()` |
| `apps/ingestion/services.py` | `RAGQueryService` uses `get_chat_llm()` + `get_embeddings()` |
| `apps/inventory/views.py` | Uses `call_gpt4o_formatter()` |
| `ai/llm/intent_classifier.py` | Uses `get_chat_llm_mini()` |
| `config/validators.py` | `SBG_API_KEY` is optional |

---

## E. Resolved Questions

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| 1 | NLQ accuracy without tool calling | **Accept with mitigation.** Add JSON validation layer + keyword fallback. Run accuracy baseline test. If <80%, consider Groq-only for NLQ. | Tool calling is preferred but prompt-based extraction with validation is acceptable for MVP. The existing `_keyword_fallback()` provides a safety net. |
| 2 | Streaming behavior | **Accept for MVP.** Buffer then yield. | SBG has no SSE. True streaming can be added later if SBG adds support. Document as known limitation. |
| 3 | Classifier model | **Use `openai.gpt-oss-safeguard-20b`.** 4x latency reduction (2s vs 8s) for a classifier that runs on every query. | Safeguard is purpose-built for classification. Test accuracy on 20 samples — if within 5% of the 20b model, use safeguard. |
| 4 | System prompt placement | **Extract to separate `system_prompt` field.** | SBG supports a dedicated `system_prompt` field. Merging into user message would break the carefully structured `SYSTEM_PROMPT`. |

---

## F. Implementation Order (Dependency-Aware)

```
1. sbg_client.py          (no deps)
2. provider_config.py      (depends on 1)
3. chain.py                (depends on 2)
4. vision.py               (depends on 1)
5. .env.example            (no deps)
6. test_sbg_client.py      (depends on 1)
7. test_provider_config.py (depends on 2)
8. test_sbg_nlq_chain.py   (depends on 3)
9. Integration verification (depends on all above)
```

---

## G. Classifier Model Change

The original plan used `openai.gpt-oss-20b-1:0` (8.2s) for the classifier. Updated to `openai.gpt-oss-safeguard-20b` (2s) based on latency analysis. This requires:

- Testing accuracy of safeguard model on 20 classification samples
- If accuracy is within 5% of the 20b model, finalize the change
- If accuracy drops significantly, revert to 20b model and accept the 8s latency

**Test script:** Run `IntentClassifier.classify()` on 20 sample queries with both models, compare results against hand-labeled ground truth.
