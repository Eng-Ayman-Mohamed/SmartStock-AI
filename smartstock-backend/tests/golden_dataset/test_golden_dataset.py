import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_DATASET_PATH = Path(__file__).parent / 'nl_queries.jsonl'


def _load_dataset() -> list[dict]:
    return [json.loads(line) for line in _DATASET_PATH.read_text().splitlines() if line.strip()]


_dataset = _load_dataset()


def _build_mock_response(expected_action: str, expected_filters: dict) -> MagicMock:
    """Build a mock AIMessage-like object matching the tool_call format.

    The chain reads sort/sort_order/limit/offset from args (top level),
    and conditions from args['filters']['conditions'].  We split them
    accordingly so the chain constructs the correct NLQueryFilters.
    """
    conditions = expected_filters.get('conditions', [])
    args = {
        'action': expected_action,
        'filters': {'conditions': conditions} if conditions else {},
        'sort': expected_filters.get('sort'),
        'sort_order': expected_filters.get('sort_order'),
        'limit': expected_filters.get('limit'),
        'offset': expected_filters.get('offset'),
    }
    mock_msg = MagicMock()
    mock_msg.content = json.dumps(args)
    mock_msg.tool_calls = [
        {
            'name': 'nl_query',
            'args': args,
            'id': 'call_golden',
            'type': 'tool_call',
        }
    ]
    return mock_msg


@pytest.mark.parametrize(
    'case',
    _dataset,
    ids=[c['id'] for c in _dataset],
)
@patch('ai.llm.chain.invoke_with_langfuse')
def test_golden_dataset_entry(mock_invoke, case):
    """Each golden dataset entry must map NL input to the correct action and filters."""
    mock_invoke.return_value = _build_mock_response(
        case['expected_action'], case['expected_filters']
    )

    from ai.llm.chain import NLQueryChain

    chain = NLQueryChain.__new__(NLQueryChain)
    chain._chain = MagicMock()

    result = chain.run(case['nl_input'])

    assert result.action.value == case['expected_action'], (
        f"[{case['id']}] Expected action '{case['expected_action']}', "
        f"got '{result.action.value}' for query: {case['nl_input']!r}"
    )
    assert result.filters.to_dict() == case['expected_filters'], (
        f'[{case["id"]}] Filters mismatch for query: {case["nl_input"]!r}\n'
        f'  Expected: {case["expected_filters"]}\n'
        f'  Got:      {result.filters.to_dict()}'
    )
