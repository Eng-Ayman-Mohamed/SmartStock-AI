import json
import logging
import os
import re
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

try:
    from langchain.chains import LLMChain
except ImportError:

    class LLMChain:
        """Compatibility wrapper for LangChain versions without langchain.chains."""

        def __init__(self, llm, prompt):
            self._chain = prompt | llm | StrOutputParser()

        def invoke(self, inputs):
            return {'text': self._chain.invoke(inputs)}


from ai.llm.few_shots import FEW_SHOT_EXAMPLES
from ai.llm.output_parser import NLQueryOutputParser, NLQueryParseError
from ai.llm.output_validator import validate_response_safety
from ai.llm.prompts import SYSTEM_PROMPT
from ai.llm.schemas import NLQueryAction, NLQueryFilters, NLQueryResult
from ai.observability.langfuse import invoke_with_langfuse

logger = logging.getLogger(__name__)


class NLQueryToolSchema(BaseModel):
    action: str = Field(
        description='Action enum value (get_inventory, get_sales_report, get_low_stock, forecast_demand, get_supplier_info, get_total_value, get_top_products)'
    )
    filters: Optional[dict] = Field(
        default=None, description='Filter conditions, sort, limit, offset'
    )
    sort: Optional[str] = Field(default=None, description='Field name to sort by')
    limit: Optional[int] = Field(default=None, description='Maximum number of results')
    offset: Optional[int] = Field(default=None, description='Number of results to skip')


# -- LLM factory --------------------------------------------------------------


def get_llm() -> ChatOpenAI:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError('OPENAI_API_KEY is missing. Check your .env file.')
    return ChatOpenAI(model='gpt-4o', temperature=0, api_key=api_key)


# -- NL Query chain -----------------------------------------------------------


# Few-shot examples are rendered before the user query.
# SYSTEM_PROMPT stays in the system message.
def _few_shot_examples() -> list[dict[str, str]]:
    return [
        {
            'input': example.get('input') or example.get('user', ''),
            'output': example['output'].replace('{', '{{').replace('}', '}}'),
        }
        for example in FEW_SHOT_EXAMPLES
    ]


_EXAMPLE_PROMPT = PromptTemplate(
    input_variables=['input', 'output'],
    template='User: {input}\nOutput: {output}',
)

_FEW_SHOT_PROMPT = FewShotPromptTemplate(
    examples=_few_shot_examples(),
    example_prompt=_EXAMPLE_PROMPT,
    prefix='Examples:',
    suffix='User: {query}\nOutput:',
    input_variables=['query'],
)

_NL_PROMPT = ChatPromptTemplate.from_messages(
    [
        ('system', SYSTEM_PROMPT),
        ('user', '{few_shot_query}'),
    ]
)

_parser = NLQueryOutputParser()


class NLQueryChain:
    """
    Thin wrapper around the LangChain chain using OpenAI function calling.
    Uses tool_choice="required" to force structured JSON output.

    Fallback behaviour:
      On any parse error, returns get_inventory with empty filters
      rather than surfacing an exception to the Django view.
      The error is logged so it can be tracked in Langfuse.
    """

    def __init__(self):
        self._llm = get_llm()
        self._llm_with_tools = self._llm.bind_tools([NLQueryToolSchema], tool_choice='required')
        self._chain = _NL_PROMPT | self._llm_with_tools

    def _parse_tool_call(self, response) -> NLQueryResult:
        tool_calls = getattr(response, 'tool_calls', None)
        if tool_calls and len(tool_calls) > 0:
            args = (
                tool_calls[0].get('args', {})
                if isinstance(tool_calls[0], dict)
                else tool_calls[0].args
            )
            action_value = args.get('action', '')
            raw_filters = args.get('filters', {})
            try:
                action = NLQueryAction(action_value)
            except ValueError:
                valid = [a.value for a in NLQueryAction]
                raise NLQueryParseError(f"Unknown action '{action_value}'. Valid values: {valid}")
            filters = NLQueryFilters(
                conditions=[],
                sort=args.get('sort'),
                sort_order=args.get('sort_order'),
                limit=args.get('limit'),
                offset=args.get('offset'),
            )
            if raw_filters and isinstance(raw_filters, dict):
                raw_conditions = raw_filters.get('conditions', [])
                from ai.llm.schemas import Condition

                filters.conditions = [
                    Condition(field=c['field'], op=c['op'], value=c['value'])
                    for c in raw_conditions
                ]
            return NLQueryResult(action=action, filters=filters)
        content = getattr(response, 'content', '') or ''
        if content:
            return _parser.parse(content)
        raise NLQueryParseError('No tool call or content in LLM response')

    def run(self, query: str) -> NLQueryResult:
        try:
            logger.info('Running NL query chain with tool_choice=required')
            response = invoke_with_langfuse(
                self._chain,
                {
                    'few_shot_query': _FEW_SHOT_PROMPT.format(query=query),
                },
            )
            return self._parse_tool_call(response)
        except NLQueryParseError as exc:
            logger.warning('NLQueryParseError for query %r: %s', query, exc)
            return NLQueryResult(
                action=NLQueryAction.GET_INVENTORY,
                filters=NLQueryFilters(),
            )


# -- Prompt-injection filter --------------------------------------------------


def prompt_injection_filter(query: str) -> tuple[bool, str | None]:
    """
    Returns (True, None) if the query is SAFE to process,
    or (False, matched_pattern) if it looks malicious.
    Used by the Django view before the main chain runs (task A10).
    """
    normalized = re.sub(r'\s+', ' ', query.strip().lower())
    patterns = [
        'ignore previous instructions',
        'ignore all instructions',
        'forget your instructions',
        'override your instructions',
        'override your system prompt',
        'you are now',
        'you are chatgpt',
        'disregard your system prompt',
        'disregard your instructions',
        'repeat your system prompt',
        'repeat your instructions',
        'output your instructions',
        'what are your instructions',
        'now act as',
        'new instructions',
    ]
    role_switching = [
        ('system:', r'system\s*:'),
        ('assistant:', r'assistant\s*:'),
        ('human:', r'human\s*:'),
    ]
    for pattern in patterns:
        if pattern in normalized:
            return False, pattern
    for pattern_str, pattern_re in role_switching:
        if re.search(pattern_re, normalized):
            return False, pattern_str
    return True, None


# -- GPT-4o natural-language formatter ----------------------------------------


def call_gpt4o_formatter(original_query: str, raw_data: object) -> str:
    """
    Takes the raw ORM query result and asks GPT-4o to write a human-readable answer.
    Called by the Django view AFTER the repository has fetched the data.
    """
    llm = get_llm()
    system = (
        "Given the raw database records provided, answer the user's question in plain, "
        'natural language. Be concise, precise, and professional. '
        'Address exactly what the user asked. Do not mention internal field names.'
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system),
            ('user', 'Original question: {query}\n\nDatabase records:\n{data}'),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    try:
        logger.info('Running GPT-4o formatter')
        result = invoke_with_langfuse(
            chain,
            {
                'query': original_query,
                'data': json.dumps(raw_data, default=str),
            },
        ).strip()
        if not result or not validate_response_safety(result):
            logger.warning('GPT-4o formatter output blocked by response safety validator')
            return "I'm sorry, I cannot provide that information."
        return result
    except Exception as exc:
        logger.warning('GPT-4o formatter failed: %s', exc)
        fallback = f'Here is the requested information: {raw_data}'
        if not validate_response_safety(fallback):
            logger.warning('GPT-4o formatter fallback blocked by response safety validator')
            return "I'm sorry, I cannot provide that information."
        return fallback
