from ai.llm.schemas import NLQueryAction

# ── Raw example pairs ─────────────────────────────────────────────────────────
# Stored as dicts so they can be unit-tested independently (see test_nlquery.py).
#
# Rule: exactly ONE example per action that is tested end-to-end.
# The 5 required action types are:
#   1. get_inventory
#   2. get_sales_report
#   3. get_low_stock
#   4. forecast_demand
#   5. get_supplier_info
#
# get_total_value and get_top_products are valid actions in the enum but are
# NOT required to have a few-shot example in MQ3 — add them later when their
# repository methods are implemented.

FEW_SHOT_EXAMPLES = [
    # 1. get_inventory — multi-condition: specific category + active only,
    #    sorted by available quantity descending, paginated.
    {
        "action": NLQueryAction.GET_INVENTORY,
        "user":   (
            "Show me all active products in the Electronics category "
            "sorted by available quantity, lowest first, page 2 (10 per page)"
        ),
        "output": (
            '{"action": "get_inventory", "filters": {'
            '"conditions": ['
            '{"field": "category", "op": "eq", "value": "Electronics"}, '
            '{"field": "is_active", "op": "eq", "value": true}'
            '], '
            '"sort": "quantity_available", "sort_order": "asc", '
            '"limit": 10, "offset": 10}}'
        ),
    },

    # 2. get_sales_report — date range + product filter + sort by quantity sold
    {
        "action": NLQueryAction.GET_SALES_REPORT,
        "user":   (
            "Give me the sales report for SKU WGT-500 "
            "between March 1 and March 31, ordered by quantity sold descending"
        ),
        "output": (
            '{"action": "get_sales_report", "filters": {'
            '"conditions": ['
            '{"field": "sku_code", "op": "eq", "value": "WGT-500"}, '
            '{"field": "date_from", "op": "gte", "value": "2026-03-01"}, '
            '{"field": "date_to", "op": "lte", "value": "2026-03-31"}'
            '], '
            '"sort": "quantity_sold", "sort_order": "desc"}}'
        ),
    },

    # 3. get_low_stock — category filter + threshold + reorder point check
    {
        "action": NLQueryAction.GET_LOW_STOCK,
        "user":   (
            "Which Furniture items have fewer than 10 units on hand "
            "and are below their reorder point?"
        ),
        "output": (
            '{"action": "get_low_stock", "filters": {'
            '"conditions": ['
            '{"field": "category", "op": "eq", "value": "Furniture"}, '
            '{"field": "quantity_on_hand", "op": "lt", "value": 10}, '
            '{"field": "reorder_point", "op": "gt", "value": 0}'
            ']}}'
        ),
    },

    # 4. forecast_demand — specific SKU (more precise than product_name)
    {
        "action": NLQueryAction.FORECAST_DEMAND,
        "user":   "What is the 30-day demand forecast for SKU CHAIR-PRO-2?",
        "output": (
            '{"action": "forecast_demand", "filters": {'
            '"conditions": ['
            '{"field": "sku_code", "op": "eq", "value": "CHAIR-PRO-2"}'
            ']}}'
        ),
    },

    # 5. get_supplier_info — partial name match + active-only filter
    {
        "action": NLQueryAction.GET_SUPPLIER_INFO,
        "user":   "Find all active suppliers whose name starts with 'Tech'",
        "output": (
            '{"action": "get_supplier_info", "filters": {'
            '"conditions": ['
            '{"field": "supplier_name", "op": "starts_with", "value": "Tech"}, '
            '{"field": "is_active", "op": "eq", "value": true}'
            ']}}'
        ),
    },
]


def build_few_shot_block() -> str:
    """
    Render all examples as a formatted string block
    that is embedded verbatim inside the system prompt.

    Output:
        Example 1:
        User: Show me all active products in the Electronics category ...
        Output: {"action": "get_inventory", ...}

        Example 2:
        ...
    """
    lines = []
    for i, ex in enumerate(FEW_SHOT_EXAMPLES, start=1):
        escaped = (
            ex["output"]
            .replace("{", "{{")
            .replace("}", "}}")
        )
        lines.append(f"Example {i}:")
        lines.append(f'User: {ex["user"]}')
        lines.append(f'Output: {escaped}')
        lines.append("")          # blank line between examples
    return "\n".join(lines).rstrip()