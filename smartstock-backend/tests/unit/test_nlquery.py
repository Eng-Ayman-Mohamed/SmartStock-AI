from unittest.mock import MagicMock

import json

import pytest

from ai.llm.few_shots import FEW_SHOT_EXAMPLES, build_few_shot_block
from ai.llm.output_parser import NLQueryOutputParser, NLQueryParseError
from ai.llm.prompts import SYSTEM_PROMPT
from ai.llm.schemas import NL_QUERY_JSON_SCHEMA, NLQueryAction, NLQueryFilters, NLQueryResult

# ══════════════════════════════════════════════════════════════════════════════
# 1. Schema integrity
# ══════════════════════════════════════════════════════════════════════════════


class TestNLQueryAction:
    def test_required_actions_exist(self):
        values = {a.value for a in NLQueryAction}
        assert 'get_inventory' in values
        assert 'get_sales_report' in values
        assert 'get_low_stock' in values
        assert 'forecast_demand' in values
        assert 'get_supplier_info' in values

    def test_action_is_string_enum(self):
        """NLQueryAction members must behave as strings for JSON serialisation."""
        assert NLQueryAction.GET_INVENTORY == 'get_inventory'
        assert isinstance(NLQueryAction.GET_LOW_STOCK.value, str)

    def test_json_schema_enum_matches_action_class(self):
        schema_values = set(NL_QUERY_JSON_SCHEMA['properties']['action']['enum'])
        class_values = {a.value for a in NLQueryAction}
        assert schema_values == class_values, 'NL_QUERY_JSON_SCHEMA enum out of sync with NLQueryAction'

    def test_json_schema_action_is_required(self):
        assert 'action' in NL_QUERY_JSON_SCHEMA['required']


class TestNLQueryFilters:
    def test_all_fields_optional(self):
        f = NLQueryFilters()
        assert f.to_dict() == {}

    def test_from_dict_partial(self):
        f = NLQueryFilters.from_dict({
            'conditions': [{'field': 'sku_code', 'op': 'eq', 'value': 'ABC-001'}]
        })
        assert len(f.conditions) == 1
        assert f.conditions[0].field == 'sku_code'
        assert f.conditions[0].op == 'eq'
        assert f.conditions[0].value == 'ABC-001'

    def test_from_dict_full(self):
        raw = {
            'conditions': [
                {'field': 'product_name', 'op': 'eq', 'value': 'Widget'},
                {'field': 'stock_below', 'op': 'lt', 'value': 10},
            ],
            'sort': 'date_from',
            'sort_order': 'desc',
            'limit': 20,
            'offset': 0,
        }
        f = NLQueryFilters.from_dict(raw)
        assert f.to_dict() == raw

    def test_to_dict_excludes_nones(self):
        f = NLQueryFilters()
        d = f.to_dict()
        assert d == {}

    def test_sort_defaults_to_asc(self):
        f = NLQueryFilters.from_dict({'sort': 'name'})
        assert f.sort_order == 'asc'


# ══════════════════════════════════════════════════════════════════════════════
# 2. Output parser
# ══════════════════════════════════════════════════════════════════════════════


class TestNLQueryOutputParser:
    def setup_method(self):
        self.parser = NLQueryOutputParser()

    def test_parses_valid_json(self):
        raw = '{"action": "get_inventory", "filters": {"conditions": [{"field": "sku_code", "op": "eq", "value": "ABC-001"}]}}'
        result = self.parser.parse(raw)
        assert result.action == NLQueryAction.GET_INVENTORY
        assert result.filters.conditions[0].field == 'sku_code'
        assert result.filters.conditions[0].value == 'ABC-001'

    def test_parses_no_filters(self):
        raw = '{"action": "get_low_stock"}'
        result = self.parser.parse(raw)
        assert result.action == NLQueryAction.GET_LOW_STOCK
        assert result.filters.to_dict() == {}

    def test_strips_json_code_fence(self):
        raw = '```json\n{"action": "get_sales_report", "filters": {}}\n```'
        result = self.parser.parse(raw)
        assert result.action == NLQueryAction.GET_SALES_REPORT

    def test_strips_plain_code_fence(self):
        raw = '```\n{"action": "forecast_demand", "filters": {"product_name": "X"}}\n```'
        result = self.parser.parse(raw)
        assert result.action == NLQueryAction.FORECAST_DEMAND

    def test_raises_on_invalid_json(self):
        with pytest.raises(NLQueryParseError, match='invalid JSON'):
            self.parser.parse('not json at all')

    def test_raises_on_unknown_action(self):
        raw = '{"action": "delete_everything", "filters": {}}'
        with pytest.raises(NLQueryParseError, match='Unknown action'):
            self.parser.parse(raw)

    def test_raises_on_missing_action(self):
        raw = '{"filters": {"conditions": [{"field": "sku_code", "op": "eq", "value": "X"}]}}'
        with pytest.raises(NLQueryParseError, match="missing required 'action'"):
            self.parser.parse(raw)

    def test_raises_on_out_of_scope_signal(self):
        raw = '{"error": "Out of scope request"}'
        with pytest.raises(NLQueryParseError, match='out-of-scope'):
            self.parser.parse(raw)

    def test_raises_when_filters_not_dict(self):
        raw = '{"action": "get_inventory", "filters": "bad"}'
        with pytest.raises(NLQueryParseError, match='must be an object'):
            self.parser.parse(raw)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Few-shot examples
# ══════════════════════════════════════════════════════════════════════════════


class TestFewShotExamples:
    def setup_method(self):
        self.parser = NLQueryOutputParser()

    def test_five_examples_defined(self):
        assert len(FEW_SHOT_EXAMPLES) >= 5

    def test_each_example_covers_distinct_action(self):
        actions = {ex['action'] for ex in FEW_SHOT_EXAMPLES}
        assert actions == set(NLQueryAction)

    @pytest.mark.parametrize('example', FEW_SHOT_EXAMPLES)
    def test_each_output_is_valid_parseable_json(self, example):
        """The 'output' string in every few-shot must parse cleanly."""
        result = self.parser.parse(example['output'])
        assert result.action == example['action']

    def test_build_few_shot_block_contains_all_five(self):
        block = build_few_shot_block()
        for i in range(1, len(FEW_SHOT_EXAMPLES) + 1):
            assert f'Example {i}:' in block

    def test_few_shot_block_embedded_in_system_prompt(self):
        assert 'Example 1:' in SYSTEM_PROMPT
        assert f'Example {len(FEW_SHOT_EXAMPLES)}:' in SYSTEM_PROMPT

    def test_system_prompt_contains_all_action_values(self):
        for action in NLQueryAction:
            assert action.value in SYSTEM_PROMPT, f"Action '{action.value}' missing from system prompt"


# ══════════════════════════════════════════════════════════════════════════════
# 4. End-to-end — all 5 NL query types (mocked LLM)
# ══════════════════════════════════════════════════════════════════════════════
#
# We mock the LangChain chain's .invoke() so these tests run without an
# OpenAI API key in CI. The mocked return value is the JSON the real LLM
# would produce for each query type.

END_TO_END_CASES = [
    # (query_type, user_input, mocked_llm_output, expected_action, conditions)
    (
        'get_inventory',
        'How many units of SKU ABC-001 do we have?',
        '{"action": "get_inventory", "filters": {"conditions": [{"field": "sku_code", "op": "eq", "value": "ABC-001"}]}}',
        NLQueryAction.GET_INVENTORY,
        [('sku_code', 'eq', 'ABC-001')],
    ),
    (
        'get_sales_report',
        'Sales report from Jan 1 to Jan 15',
        '{"action": "get_sales_report", "filters": {"conditions": [{"field": "date_from", "op": "eq", "value": "2026-01-01"}, {"field": "date_to", "op": "eq", "value": "2026-01-15"}]}}',
        NLQueryAction.GET_SALES_REPORT,
        [('date_from', 'eq', '2026-01-01'), ('date_to', 'eq', '2026-01-15')],
    ),
    (
        'get_low_stock',
        'Show items with stock below 5',
        '{"action": "get_low_stock", "filters": {"conditions": [{"field": "stock_below", "op": "lt", "value": 5}]}}',
        NLQueryAction.GET_LOW_STOCK,
        [('stock_below', 'lt', 5)],
    ),
    (
        'forecast_demand',
        'Forecast demand for Product X next month',
        '{"action": "forecast_demand", "filters": {"conditions": [{"field": "product_name", "op": "eq", "value": "Product X"}]}}',
        NLQueryAction.FORECAST_DEMAND,
        [('product_name', 'eq', 'Product X')],
    ),
    (
        'get_supplier_info',
        'Who is the supplier for Product Y?',
        '{"action": "get_supplier_info", "filters": {"conditions": [{"field": "product_name", "op": "eq", "value": "Product Y"}]}}',
        NLQueryAction.GET_SUPPLIER_INFO,
        [('product_name', 'eq', 'Product Y')],
    ),
]


class TestNLQueryChainEndToEnd:
    @pytest.mark.parametrize(
        'query_type, user_input, mocked_output, expected_action, expected_conditions',
        END_TO_END_CASES,
        ids=[c[0] for c in END_TO_END_CASES],
    )
    def test_query_type_end_to_end(
        self,
        query_type,
        user_input,
        mocked_output,
        expected_action,
        expected_conditions,
    ):
        """
        For each of the 5 query types:
          1. Mock the chain's invoke() to return the expected LLM JSON.
          2. Verify NLQueryChain.run() returns correct action + filter.
        """
        from ai.llm.chain import NLQueryChain

        chain = NLQueryChain.__new__(NLQueryChain)  # skip __init__ (avoids API key check)

        # Mock the LCEL chain to return an AIMessage with a tool_call
        # containing parsed args (bypasses field validation).
        mock_lcel_chain = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = mocked_output
        mock_msg.tool_calls = [
            {'name': 'nl_query', 'args': json.loads(mocked_output), 'id': 'call_1', 'type': 'tool_call'},
        ]
        mock_lcel_chain.invoke.return_value = mock_msg
        chain._chain = mock_lcel_chain

        result: NLQueryResult = chain.run(user_input)

        assert result.action == expected_action, (
            f'[{query_type}] Expected action {expected_action}, got {result.action}'
        )
        assert len(result.filters.conditions) == len(expected_conditions), (
            f'[{query_type}] Expected {len(expected_conditions)} conditions, got {len(result.filters.conditions)}'
        )
        for i, (field, op, value) in enumerate(expected_conditions):
            assert result.filters.conditions[i].field == field
            assert result.filters.conditions[i].op == op
            assert result.filters.conditions[i].value == value

    def test_chain_falls_back_on_parse_error(self):
        """If the LLM returns garbage, run() should fall back to get_inventory."""
        from ai.llm.chain import NLQueryChain
        chain = NLQueryChain.__new__(NLQueryChain)
        mock_lcel_chain = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = 'this is not json'
        mock_msg.tool_calls = []
        mock_lcel_chain.invoke.return_value = mock_msg

        chain._chain = mock_lcel_chain

        result = chain.run('some query')
        assert result.action == NLQueryAction.GET_INVENTORY
        assert result.filters.to_dict() == {}

    def test_chain_falls_back_on_unknown_action(self):
        """If the LLM hallucinates an action, run() falls back gracefully."""
        from ai.llm.chain import NLQueryChain

        chain = NLQueryChain.__new__(NLQueryChain)
        mock_lcel_chain = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = '{"action": "hack_the_planet", "filters": {}}'
        mock_msg.tool_calls = [
            {'name': 'nl_query', 'args': {'action': 'hack_the_planet', 'filters': {}}, 'id': 'call_1', 'type': 'tool_call'},
        ]
        chain._chain = mock_lcel_chain

        result = chain.run('some query')
        assert result.action == NLQueryAction.GET_INVENTORY


# ══════════════════════════════════════════════════════════════════════════════
# 5. Out-of-scope handling
# ══════════════════════════════════════════════════════════════════════════════


class TestOutOfScope:
    def test_parser_raises_on_error_key(self):
        """LLM returning {"error": "..."} must raise NLQueryParseError."""
        parser = NLQueryOutputParser()
        with pytest.raises(NLQueryParseError):
            parser.parse('{"error": "Out of scope request"}')

    def test_system_prompt_includes_out_of_scope_instruction(self):
        """System prompt must tell GPT-4o how to signal out-of-scope queries."""
        assert 'Out of scope request' in SYSTEM_PROMPT
        assert '"error"' in SYSTEM_PROMPT
