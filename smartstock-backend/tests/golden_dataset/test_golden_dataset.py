import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from ai.llm.chain import NLQueryChain


def _load_dataset():
    path = Path(__file__).parent / 'nl_queries.jsonl'
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _make_mock_response(entry):
    ef = entry['expected_filters']
    args = {'action': entry['expected_action'], 'filters': {'conditions': ef.get('conditions', [])}}
    for key in ('sort', 'sort_order', 'limit', 'offset'):
        if key in ef:
            args[key] = ef[key]
    return AIMessage(
        content='',
        tool_calls=[{
            'name': 'NLQueryToolSchema',
            'args': args,
            'id': f'call_{uuid.uuid4().hex[:8]}',
        }],
    )


DATASET = _load_dataset()


@pytest.mark.parametrize('entry', DATASET, ids=lambda e: e['id'])
@patch('ai.llm.chain.get_llm')
@patch('ai.llm.chain.invoke_with_langfuse')
def test_golden_dataset_entry(mock_invoke_lnf, mock_get_llm, entry):
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = MagicMock()
    mock_get_llm.return_value = mock_llm

    mock_invoke_lnf.return_value = _make_mock_response(entry)

    chain = NLQueryChain()
    result = chain.run(entry['nl_input'])

    assert result.action.value == entry['expected_action']

    ef = entry['expected_filters']
    expected_conditions = ef.get('conditions', [])

    assert len(result.filters.conditions) == len(expected_conditions)
    for actual, expected in zip(result.filters.conditions, expected_conditions):
        assert actual.field == expected['field']
        assert actual.op == expected['op']
        assert actual.value == expected['value']

    assert result.filters.sort == ef.get('sort')
    assert result.filters.sort_order == ef.get('sort_order', 'asc')
    assert result.filters.limit == ef.get('limit')
    assert result.filters.offset == ef.get('offset')
