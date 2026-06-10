"""
tests/unit/test_nlquery.py — MQ3 milestone

Covers:
  1. Schema integrity  (NLQueryAction enum, NLQueryFilters, NL_QUERY_JSON_SCHEMA)
  2. Output parser     (happy-path + all error branches)
  3. Few-shot examples (parsability + coverage)
  4. End-to-end        (5 NL query types with complex multi-condition inputs, mocked LLM)
  5. Out-of-scope      (parser + system-prompt)
"""

import json
import pytest
from unittest.mock import MagicMock

from ai.llm.schemas import (
    NLQueryAction,
    NLQueryFilters,
    NLQueryResult,
    NL_QUERY_JSON_SCHEMA,
    ACTION_ALLOWED_FIELDS,
    VALID_OPERATORS,
    Condition,
)
from ai.llm.few_shots import FEW_SHOT_EXAMPLES, build_few_shot_block
from ai.llm.output_parser import NLQueryOutputParser, NLQueryParseError
from ai.llm.prompts import SYSTEM_PROMPT


# ══════════════════════════════════════════════════════════════════════════════
# 1. Schema integrity
# ══════════════════════════════════════════════════════════════════════════════

class TestNLQueryAction:
    def test_all_seven_actions_exist(self):
        """schemas.py must declare all 7 action values."""
        values = {a.value for a in NLQueryAction}
        assert values == {
            "get_inventory",
            "get_sales_report",
            "get_low_stock",
            "forecast_demand",
            "get_supplier_info",
            "get_total_value",
            "get_top_products",
        }

    def test_action_is_string_enum(self):
        """NLQueryAction members must behave as strings for JSON serialisation."""
        assert NLQueryAction.GET_INVENTORY == "get_inventory"
        assert isinstance(NLQueryAction.GET_LOW_STOCK.value, str)

    def test_json_schema_enum_matches_action_class(self):
        schema_values = set(NL_QUERY_JSON_SCHEMA["properties"]["action"]["enum"])
        class_values  = {a.value for a in NLQueryAction}
        assert schema_values == class_values, (
            "NL_QUERY_JSON_SCHEMA enum out of sync with NLQueryAction"
        )

    def test_json_schema_action_is_required(self):
        assert "action" in NL_QUERY_JSON_SCHEMA["required"]

    def test_action_allowed_fields_covers_all_actions(self):
        """Every action in the enum must have an entry in ACTION_ALLOWED_FIELDS."""
        for action in NLQueryAction:
            assert action.value in ACTION_ALLOWED_FIELDS, (
                f"ACTION_ALLOWED_FIELDS missing entry for '{action.value}'"
            )

    def test_action_allowed_fields_are_non_empty(self):
        for action_val, fields in ACTION_ALLOWED_FIELDS.items():
            assert len(fields) > 0, f"Empty field list for action '{action_val}'"

    def test_valid_operators_non_empty(self):
        assert len(VALID_OPERATORS) > 0


class TestNLQueryFilters:
    def test_empty_filters_serialize_to_empty_dict(self):
        f = NLQueryFilters()
        assert f.to_dict() == {}

    def test_conditions_round_trip(self):
        c = Condition(field="sku_code", op="eq", value="ABC-001")
        f = NLQueryFilters(conditions=[c])
        d = f.to_dict()
        assert d == {"conditions": [{"field": "sku_code", "op": "eq", "value": "ABC-001"}]}

    def test_from_dict_with_conditions(self):
        raw = {
            "conditions": [
                {"field": "category", "op": "eq", "value": "Electronics"},
                {"field": "is_active", "op": "eq", "value": True},
            ],
            "sort": "quantity_available",
            "sort_order": "asc",
            "limit": 10,
            "offset": 10,
        }
        f = NLQueryFilters.from_dict(raw)
        assert len(f.conditions) == 2
        assert f.conditions[0].field == "category"
        assert f.conditions[0].value == "Electronics"
        assert f.conditions[1].field == "is_active"
        assert f.sort == "quantity_available"
        assert f.sort_order == "asc"
        assert f.limit == 10
        assert f.offset == 10

    def test_to_dict_omits_empty_conditions(self):
        f = NLQueryFilters(sort="quantity_on_hand", sort_order="desc")
        d = f.to_dict()
        assert "conditions" not in d
        assert d["sort"] == "quantity_on_hand"
        assert d["sort_order"] == "desc"

    def test_condition_to_dict(self):
        c = Condition(field="quantity_on_hand", op="lt", value=5)
        assert c.to_dict() == {"field": "quantity_on_hand", "op": "lt", "value": 5}

    def test_condition_from_dict(self):
        c = Condition.from_dict({"field": "category", "op": "eq", "value": "Furniture"})
        assert c.field == "category"
        assert c.op == "eq"
        assert c.value == "Furniture"


# ══════════════════════════════════════════════════════════════════════════════
# 2. Output parser
# ══════════════════════════════════════════════════════════════════════════════

class TestNLQueryOutputParser:
    def setup_method(self):
        self.parser = NLQueryOutputParser()

    def test_parses_single_condition(self):
        raw = '{"action": "get_inventory", "filters": {"conditions": [{"field": "sku_code", "op": "eq", "value": "ABC-001"}]}}'
        result = self.parser.parse(raw)
        assert result.action == NLQueryAction.GET_INVENTORY
        assert len(result.filters.conditions) == 1
        assert result.filters.conditions[0].field == "sku_code"
        assert result.filters.conditions[0].value == "ABC-001"

    def test_parses_multi_condition_with_sort_and_pagination(self):
        raw = json.dumps({
            "action": "get_inventory",
            "filters": {
                "conditions": [
                    {"field": "category", "op": "eq", "value": "Electronics"},
                    {"field": "is_active", "op": "eq", "value": True},
                ],
                "sort": "quantity_available",
                "sort_order": "asc",
                "limit": 10,
                "offset": 10,
            }
        })
        result = self.parser.parse(raw)
        assert result.action == NLQueryAction.GET_INVENTORY
        assert len(result.filters.conditions) == 2
        assert result.filters.sort == "quantity_available"
        assert result.filters.limit == 10
        assert result.filters.offset == 10

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
        raw = '```\n{"action": "forecast_demand", "filters": {"conditions": [{"field": "product_name", "op": "eq", "value": "X"}]}}\n```'
        result = self.parser.parse(raw)
        assert result.action == NLQueryAction.FORECAST_DEMAND

    def test_raises_on_invalid_json(self):
        with pytest.raises(NLQueryParseError, match="invalid JSON"):
            self.parser.parse("not json at all")

    def test_raises_on_unknown_action(self):
        raw = '{"action": "delete_everything", "filters": {}}'
        with pytest.raises(NLQueryParseError, match="Unknown action"):
            self.parser.parse(raw)

    def test_raises_on_missing_action(self):
        raw = '{"filters": {"conditions": []}}'
        with pytest.raises(NLQueryParseError, match="missing required 'action'"):
            self.parser.parse(raw)

    def test_raises_on_out_of_scope_signal(self):
        raw = '{"error": "Out of scope request"}'
        with pytest.raises(NLQueryParseError, match="out-of-scope"):
            self.parser.parse(raw)

    def test_raises_when_filters_not_dict(self):
        raw = '{"action": "get_inventory", "filters": "bad"}'
        with pytest.raises(NLQueryParseError, match="must be an object"):
            self.parser.parse(raw)

    def test_raises_on_invalid_operator(self):
        raw = json.dumps({
            "action": "get_inventory",
            "filters": {
                "conditions": [{"field": "sku_code", "op": "LIKE", "value": "A%"}]
            }
        })
        with pytest.raises(NLQueryParseError, match="Invalid operator"):
            self.parser.parse(raw)

    def test_raises_on_disallowed_field_for_action(self):
        # contact_email is only allowed for get_supplier_info, not get_inventory
        raw = json.dumps({
            "action": "get_inventory",
            "filters": {
                "conditions": [{"field": "contact_email", "op": "eq", "value": "x@y.com"}]
            }
        })
        with pytest.raises(NLQueryParseError, match="not allowed for action"):
            self.parser.parse(raw)

    def test_raises_on_conditions_not_list(self):
        raw = json.dumps({
            "action": "get_inventory",
            "filters": {"conditions": "sku_code=ABC"}
        })
        with pytest.raises(NLQueryParseError, match="must be an array"):
            self.parser.parse(raw)

    def test_raises_on_invalid_sort_order(self):
        raw = json.dumps({
            "action": "get_inventory",
            "filters": {
                "conditions": [{"field": "category", "op": "eq", "value": "Electronics"}],
                "sort": "quantity_on_hand",
                "sort_order": "random",
            }
        })
        with pytest.raises(NLQueryParseError, match="Invalid sort_order"):
            self.parser.parse(raw)

    def test_raises_on_negative_limit(self):
        raw = json.dumps({
            "action": "get_inventory",
            "filters": {
                "conditions": [],
                "limit": -5,
            }
        })
        with pytest.raises(NLQueryParseError, match="non-negative integer"):
            self.parser.parse(raw)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Few-shot examples
# ══════════════════════════════════════════════════════════════════════════════

class TestFewShotExamples:
    def setup_method(self):
        self.parser = NLQueryOutputParser()

    def test_exactly_five_examples_defined(self):
        assert len(FEW_SHOT_EXAMPLES) == 5, (
            f"Expected 5 few-shot examples (one per required action type), "
            f"got {len(FEW_SHOT_EXAMPLES)}"
        )

    def test_covers_the_five_required_action_types(self):
        """
        The 5 examples must cover the 5 action types tested end-to-end.
        get_total_value and get_top_products are valid enum members but are
        not required in the MQ3 few-shot set.
        """
        required = {
            NLQueryAction.GET_INVENTORY,
            NLQueryAction.GET_SALES_REPORT,
            NLQueryAction.GET_LOW_STOCK,
            NLQueryAction.FORECAST_DEMAND,
            NLQueryAction.GET_SUPPLIER_INFO,
        }
        actions = {ex["action"] for ex in FEW_SHOT_EXAMPLES}
        assert actions == required, (
            f"Few-shot examples cover {actions}, expected {required}"
        )

    @pytest.mark.parametrize("example", FEW_SHOT_EXAMPLES)
    def test_each_output_is_parseable(self, example):
        """Every 'output' string must parse cleanly through the output parser."""
        result = self.parser.parse(example["output"])
        assert result.action == example["action"]

    @pytest.mark.parametrize("example", FEW_SHOT_EXAMPLES)
    def test_each_example_uses_conditions_array(self, example):
        """All examples must use the conditions-based format (not legacy flat keys)."""
        data = json.loads(example["output"])
        filters = data.get("filters", {})
        # Either no filters at all, or filters contains a conditions array
        if filters:
            assert "conditions" in filters, (
                f"Example for action '{example['action']}' uses legacy flat filters. "
                "All examples must use the conditions array format."
            )

    def test_build_few_shot_block_contains_all_five(self):
        block = build_few_shot_block()
        for i in range(1, 6):
            assert f"Example {i}:" in block, f"build_few_shot_block missing 'Example {i}:'"

    def test_few_shot_block_embedded_in_system_prompt(self):
        assert "Example 1:" in SYSTEM_PROMPT
        assert "Example 5:" in SYSTEM_PROMPT

    def test_system_prompt_contains_all_action_values(self):
        for action in NLQueryAction:
            assert action.value in SYSTEM_PROMPT, (
                f"Action '{action.value}' missing from system prompt"
            )

    def test_system_prompt_contains_all_valid_operators(self):
        for op in VALID_OPERATORS:
            assert op in SYSTEM_PROMPT, (
                f"Operator '{op}' missing from system prompt"
            )


# ══════════════════════════════════════════════════════════════════════════════
# 4. End-to-end — 5 NL query types (mocked LLM, complex inputs)
# ══════════════════════════════════════════════════════════════════════════════
#
# Each test case uses a realistic multi-condition NL query that is more complex
# than the simple few-shot examples, verifying the full chain:
#   NLQueryChain.run() → _parser.parse() → NLQueryResult with typed conditions.
#
# The LLM is mocked so these run without an OpenAI API key in CI.

END_TO_END_CASES = [
    # 1. get_inventory — multi-condition: supplier + category + active flag + pagination
    (
        "get_inventory",
        (
            "List all active widgets supplied by Acme Corp in the Hardware "
            "category, 20 per page, second page"
        ),
        json.dumps({
            "action": "get_inventory",
            "filters": {
                "conditions": [
                    {"field": "supplier_name", "op": "eq",  "value": "Acme Corp"},
                    {"field": "category",      "op": "eq",  "value": "Hardware"},
                    {"field": "is_active",     "op": "eq",  "value": True},
                ],
                "sort": "product_name",
                "sort_order": "asc",
                "limit": 20,
                "offset": 20,
            },
        }),
        NLQueryAction.GET_INVENTORY,
        # verify first condition
        lambda r: (
            r.filters.conditions[0].field == "supplier_name"
            and r.filters.conditions[0].value == "Acme Corp"
            and len(r.filters.conditions) == 3
            and r.filters.limit == 20
            and r.filters.offset == 20
        ),
        "supplier_name='Acme Corp', 3 conditions, limit=20, offset=20",
    ),

    # 2. get_sales_report — date range + specific SKU + sort by qty sold desc
    (
        "get_sales_report",
        (
            "Show Q1 2026 sales for SKU WGT-500, sorted by quantity sold "
            "from highest to lowest"
        ),
        json.dumps({
            "action": "get_sales_report",
            "filters": {
                "conditions": [
                    {"field": "sku_code",   "op": "eq",  "value": "WGT-500"},
                    {"field": "date_from",  "op": "gte", "value": "2026-01-01"},
                    {"field": "date_to",    "op": "lte", "value": "2026-03-31"},
                ],
                "sort": "quantity_sold",
                "sort_order": "desc",
            },
        }),
        NLQueryAction.GET_SALES_REPORT,
        lambda r: (
            r.filters.conditions[0].field == "sku_code"
            and r.filters.conditions[0].value == "WGT-500"
            and r.filters.conditions[1].op == "gte"
            and r.filters.conditions[2].value == "2026-03-31"
            and r.filters.sort == "quantity_sold"
            and r.filters.sort_order == "desc"
        ),
        "sku=WGT-500, date range Q1 2026, sort qty_sold desc",
    ),

    # 3. get_low_stock — category + quantity threshold + reorder_point check
    (
        "get_low_stock",
        (
            "Which Furniture items have fewer than 10 units on hand "
            "and are below their reorder point?"
        ),
        json.dumps({
            "action": "get_low_stock",
            "filters": {
                "conditions": [
                    {"field": "category",        "op": "eq",  "value": "Furniture"},
                    {"field": "quantity_on_hand", "op": "lt",  "value": 10},
                    {"field": "reorder_point",    "op": "gt",  "value": 0},
                ],
            },
        }),
        NLQueryAction.GET_LOW_STOCK,
        lambda r: (
            len(r.filters.conditions) == 3
            and r.filters.conditions[0].value == "Furniture"
            and r.filters.conditions[1].op == "lt"
            and r.filters.conditions[1].value == 10
            and r.filters.conditions[2].field == "reorder_point"
        ),
        "Furniture + qty<10 + reorder_point>0, 3 conditions",
    ),

    # 4. forecast_demand — by SKU (more precise than product_name)
    (
        "forecast_demand",
        "What is the 30-day demand forecast for SKU CHAIR-PRO-2?",
        json.dumps({
            "action": "forecast_demand",
            "filters": {
                "conditions": [
                    {"field": "sku_code", "op": "eq", "value": "CHAIR-PRO-2"},
                ],
            },
        }),
        NLQueryAction.FORECAST_DEMAND,
        lambda r: (
            len(r.filters.conditions) == 1
            and r.filters.conditions[0].field == "sku_code"
            and r.filters.conditions[0].value == "CHAIR-PRO-2"
        ),
        "sku_code=CHAIR-PRO-2",
    ),

    # 5. get_supplier_info — starts_with + active flag, 2 conditions
    (
        "get_supplier_info",
        "Find all active suppliers whose name starts with 'Tech'",
        json.dumps({
            "action": "get_supplier_info",
            "filters": {
                "conditions": [
                    {"field": "supplier_name", "op": "starts_with", "value": "Tech"},
                    {"field": "is_active",     "op": "eq",          "value": True},
                ],
            },
        }),
        NLQueryAction.GET_SUPPLIER_INFO,
        lambda r: (
            len(r.filters.conditions) == 2
            and r.filters.conditions[0].op == "starts_with"
            and r.filters.conditions[0].value == "Tech"
            and r.filters.conditions[1].field == "is_active"
            and r.filters.conditions[1].value is True
        ),
        "supplier starts_with 'Tech' AND is_active=True",
    ),
]


class TestNLQueryChainEndToEnd:
    """
    For each of the 5 required query types, mocks the LLM response and asserts
    that NLQueryChain.run() produces the correct typed NLQueryResult.
    The lambda in each case checks a richer set of conditions than the
    old single-key assertion.
    """

    @pytest.mark.parametrize(
        "query_type, user_input, mocked_output, expected_action, assertions, assertion_desc",
        END_TO_END_CASES,
        ids=[c[0] for c in END_TO_END_CASES],
    )
    def test_query_type_end_to_end(
        self,
        query_type,
        user_input,
        mocked_output,
        expected_action,
        assertions,
        assertion_desc,
    ):
        from ai.llm.chain import NLQueryChain

        chain = NLQueryChain.__new__(NLQueryChain)   # skip __init__ (avoids API key check)
        mock_inner = MagicMock()
        mock_inner.invoke.return_value = mocked_output
        chain._chain = mock_inner

        result: NLQueryResult = chain.run(user_input)

        assert result.action == expected_action, (
            f"[{query_type}] Expected action {expected_action}, got {result.action}"
        )
        assert assertions(result), (
            f"[{query_type}] Assertion failed: {assertion_desc}\n"
            f"Got filters: {result.filters.to_dict()}"
        )

    def test_chain_falls_back_on_parse_error(self):
        """If the LLM returns garbage, run() should fall back to get_inventory."""
        from ai.llm.chain import NLQueryChain

        chain = NLQueryChain.__new__(NLQueryChain)
        mock_inner = MagicMock()
        mock_inner.invoke.return_value = "this is not json"
        chain._chain = mock_inner

        result = chain.run("some query")
        assert result.action == NLQueryAction.GET_INVENTORY
        assert result.filters.to_dict() == {}

    def test_chain_falls_back_on_unknown_action(self):
        """If the LLM hallucinates an action, run() falls back gracefully."""
        from ai.llm.chain import NLQueryChain

        chain = NLQueryChain.__new__(NLQueryChain)
        mock_inner = MagicMock()
        mock_inner.invoke.return_value = '{"action": "hack_the_planet", "filters": {}}'
        chain._chain = mock_inner

        result = chain.run("some query")
        assert result.action == NLQueryAction.GET_INVENTORY

    def test_chain_falls_back_on_disallowed_field(self):
        """If the LLM returns a field that is not allowed for the action, run() falls back."""
        from ai.llm.chain import NLQueryChain

        chain = NLQueryChain.__new__(NLQueryChain)
        mock_inner = MagicMock()
        # contact_email is not in get_inventory's allowed fields
        mock_inner.invoke.return_value = json.dumps({
            "action": "get_inventory",
            "filters": {
                "conditions": [{"field": "contact_email", "op": "eq", "value": "x@y.com"}]
            }
        })
        chain._chain = mock_inner

        result = chain.run("find supplier contact")
        assert result.action == NLQueryAction.GET_INVENTORY
        assert result.filters.to_dict() == {}

    def test_multi_condition_result_round_trips_to_dict(self):
        """NLQueryResult.to_dict() must faithfully reflect all parsed conditions."""
        from ai.llm.chain import NLQueryChain

        payload = json.dumps({
            "action": "get_low_stock",
            "filters": {
                "conditions": [
                    {"field": "category",        "op": "eq",  "value": "Furniture"},
                    {"field": "quantity_on_hand", "op": "lt",  "value": 10},
                    {"field": "reorder_point",    "op": "gt",  "value": 0},
                ],
            },
        })

        chain = NLQueryChain.__new__(NLQueryChain)
        mock_inner = MagicMock()
        mock_inner.invoke.return_value = payload
        chain._chain = mock_inner

        result = chain.run("Furniture items below reorder point")
        d = result.to_dict()

        assert d["action"] == "get_low_stock"
        conds = d["filters"]["conditions"]
        assert len(conds) == 3
        assert conds[1] == {"field": "quantity_on_hand", "op": "lt", "value": 10}


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
        assert "Out of scope request" in SYSTEM_PROMPT
        assert '"error"' in SYSTEM_PROMPT

    def test_system_prompt_restricts_to_inventory_scope(self):
        """System prompt must mention the domain boundary."""
        assert "inventory" in SYSTEM_PROMPT.lower()