import json
import logging
import os
from dataclasses import dataclass

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ai.observability.langfuse import invoke_with_langfuse

logger = logging.getLogger(__name__)

_ClassifierLLM = None


def _get_classifier_llm():
    global _ClassifierLLM
    if _ClassifierLLM is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY is missing.')
        _ClassifierLLM = ChatOpenAI(model='gpt-4o-mini', temperature=0, api_key=api_key)
    return _ClassifierLLM


CLASSIFIER_SYSTEM_PROMPT = (
    'You are an intent classifier for a warehouse management system. '
    'Classify the user query into exactly one category:\n'
    '- "nl_query": The query asks about live inventory data — stock levels, products, '
    'suppliers, sales, forecasts, reorder status, or any operational database query.\n'
    '- "rag": The query asks about documents, policies, procedures, guidelines, '
    'manuals, or requires searching uploaded files.\n'
    '- "out_of_scope": The query is unrelated to inventory, warehouse operations, '
    'or the business domain.\n\n'
    'Respond with ONLY a JSON object: {"intent": "<category>", "confidence": <0.0-1.0>}'
)

_classifier_prompt = ChatPromptTemplate.from_messages(
    [
        ('system', CLASSIFIER_SYSTEM_PROMPT),
        ('user', '{query}'),
    ]
)


@dataclass
class ClassificationResult:
    intent: str
    confidence: float


def classify_intent(query: str) -> ClassificationResult:
    """
    Classify a user query into nl_query, rag, or out_of_scope using GPT-4o-mini.
    Returns a ClassificationResult with intent and confidence.
    On failure, defaults to nl_query with 0.5 confidence (safer for operational queries).
    """
    llm = _get_classifier_llm()
    chain = _classifier_prompt | llm | StrOutputParser()

    try:
        raw = invoke_with_langfuse(chain, {'query': query})
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
    except Exception as exc:
        logger.exception('Intent classifier failed')
        return ClassificationResult(intent='nl_query', confidence=0.5)
