import json
import logging
from dataclasses import dataclass

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ai.observability.langfuse import invoke_with_langfuse

logger = logging.getLogger(__name__)

_ClassifierLLM = None


def _get_classifier_llm():
    global _ClassifierLLM
    if _ClassifierLLM is None:
        from ai.llm.provider_config import get_chat_llm_mini

        _ClassifierLLM = get_chat_llm_mini()
    return _ClassifierLLM


CLASSIFIER_SYSTEM_PROMPT = (
    'You are an intent classifier for a warehouse management system. '
    'Classify the user query into exactly one category:\n'
    '- "nl_query": The query asks about live inventory data that can be looked up in a database — '
    'current stock levels, product lists, supplier contacts, individual sales records, '
    'low stock alerts, reorder status, or forecasts for specific SKUs.\n'
    '- "rag": The query asks about business reports, financial summaries, company policies, '
    'procedures, guidelines, manuals, historical trends, quarterly performance, revenue, '
    'profit, MAPE accuracy, warehouse operations, return rates, or anything that would '
    'be found in an uploaded document or report rather than a live database query.\n'
    '- "out_of_scope": The query is unrelated to inventory, warehouse operations, '
    'or the business domain.\n\n'
    'IMPORTANT: Questions about revenue, profit, quarterly results, business metrics, '
    'MAPE, return rates, shrinkage, supplier reliability scores, warehouse capacity, '
    'hiring plans, CapEx, insurance, or company policies are ALWAYS "rag" because '
    'this data lives in reports and documents, not in the inventory database.\n\n'
    'FOLLOW-UP CONTEXT: If conversation history is provided, use it to understand '
    'follow-up questions. For example, "why can\'t you?" after a RAG answer means '
    'the user is asking about the same topic (RAG). "tell me more" after an inventory '
    'query means the user wants more inventory details (nl_query). '
    'Follow-up questions inherit the intent of the previous exchange unless they '
    'clearly shift to a different topic.\n\n'
    'Respond with ONLY a JSON object: {{"intent": "<category>", "confidence": <0.0-1.0>}}'
)

_classifier_prompt = ChatPromptTemplate.from_messages(
    [
        ('system', CLASSIFIER_SYSTEM_PROMPT),
        ('human', '{context}{query}'),
    ]
)


@dataclass
class ClassificationResult:
    intent: str
    confidence: float


_KEYWORD_MAP = {
    'rag': [
        'policy',
        'procedure',
        'manual',
        'document',
        'guideline',
        'how to',
        'rules',
        'return policy',
        'revenue',
        'profit',
        'quarterly',
        'q2',
        'q3',
        'q1',
        'q4',
        'report',
        'business',
        'metrics',
        'performance',
        'mape',
        'reliability',
        'shrinkage',
        'insurance',
        'capex',
        'hiring',
        'outlook',
        'warehouse location',
        'department',
        'contact',
        'utilization',
        'capacity',
        'throughput',
        'warehouse',
        'austin',
        'atlanta',
        'chicago',
        'region',
        'sq ft',
        'square feet',
        'cold storage',
    ],
    'nl_query': [
        'stock',
        'inventory',
        'product',
        'supplier',
        'sales',
        'forecast',
        'reorder',
        'low stock',
        'how many',
        'total value',
    ],
}


def classify_intent_fast(query: str) -> ClassificationResult | None:
    """Fast keyword-based pre-classification. Returns None if uncertain."""
    lower = query.lower()
    for intent, keywords in _KEYWORD_MAP.items():
        if any(kw in lower for kw in keywords):
            return ClassificationResult(intent=intent, confidence=0.85)
    return None


def classify_intent(query: str, history: list | None = None) -> ClassificationResult:
    """
    Classify a user query into nl_query, rag, or out_of_scope using GPT-4o-mini.
    Accepts optional conversation history for follow-up context.
    Returns a ClassificationResult with intent and confidence.
    On failure, defaults to nl_query with 0.5 confidence (safer for operational queries).
    """
    llm = _get_classifier_llm()
    chain = _classifier_prompt | llm | StrOutputParser()

    # Build context from conversation history
    context = ''
    if history:
        recent = history[-4:]  # Last 2 exchanges max
        lines = ['Conversation so far:']
        for msg in recent:
            role = msg.get('role', 'user')
            content = msg.get('content', '')[:150]
            lines.append(f'{role}: {content}')
        context = '\n'.join(lines) + '\n\n'

    try:
        raw = invoke_with_langfuse(chain, {'query': query, 'context': context})
        parsed = json.loads(raw.strip())
        intent = parsed.get('intent', 'nl_query')
        confidence = float(parsed.get('confidence', 0.5))

        if intent not in ('nl_query', 'rag', 'out_of_scope'):
            logger.warning('Classifier returned unknown intent: %s', intent)
            return ClassificationResult(intent='nl_query', confidence=0.5)

        return ClassificationResult(intent=intent, confidence=confidence)

    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning('Classifier parse failed: %s — defaulting to nl_query', exc)
        return ClassificationResult(intent='nl_query', confidence=0.5)
    except Exception:
        logger.exception('Intent classifier failed')
        return ClassificationResult(intent='nl_query', confidence=0.5)
