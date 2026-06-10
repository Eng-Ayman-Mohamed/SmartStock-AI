from ai.llm.schemas import NLQueryAction

# ── Raw example pairs ─────────────────────────────────────────────────────────
# Stored as dicts so they can be unit-tested independently (see test_nlquery.py).

FEW_SHOT_EXAMPLES = [
    # 1. get_inventory — ask for stock level of a specific SKU
    {
        "action":  NLQueryAction.GET_INVENTORY,
        "user":    "How many units of SKU ABC-001 do we have?",
        "output":  '{"action": "get_inventory", "filters": {"conditions": [{"field": "sku_code", "op": "eq", "value": "ABC-001"}]}}',
    },

    # 2. get_sales_report — ask for historical sales in a date range
    {
        "action":  NLQueryAction.GET_SALES_REPORT,
        "user":    "Show me the sales report from January 1 to January 15",
        "output":  '{"action": "get_sales_report", "filters": {"conditions": [{"field": "date_from", "op": "gte", "value": "2026-01-01"}, {"field": "date_to", "op": "lte", "value": "2026-01-15"}]}}',
    },

    # 3. get_low_stock — ask for items below a quantity threshold
    {
        "action":  NLQueryAction.GET_LOW_STOCK,
        "user":    "Show items with stock below 5",
        "output":  '{"action": "get_low_stock", "filters": {"conditions": [{"field": "quantity_on_hand", "op": "lt", "value": 5}]}}',
    },

    # 4. forecast_demand — ask for a demand prediction for a product
    {
        "action":  NLQueryAction.FORECAST_DEMAND,
        "user":    "Forecast demand for Product X next month",
        "output":  '{"action": "forecast_demand", "filters": {"conditions": [{"field": "product_name", "op": "eq", "value": "Product X"}]}}',
    },

    # 5. get_supplier_info — ask who supplies a product
    {
        "action":  NLQueryAction.GET_SUPPLIER_INFO,
        "user":    "Who is the supplier for Product Y?",
        "output":  '{"action": "get_supplier_info", "filters": {"conditions": [{"field": "supplier_name", "op": "contains", "value": "Product Y"}]}}',
    },

    # 6. get_total_value — ask for total inventory value
    {
        "action":  NLQueryAction.GET_TOTAL_VALUE,
        "user":    "What is the total value of our electronics inventory?",
        "output":  '{"action": "get_total_value", "filters": {"conditions": [{"field": "category", "op": "eq", "value": "electronics"}]}}',
    },

    # 7. get_top_products — ask for top-selling products
    {
        "action":  NLQueryAction.GET_TOP_PRODUCTS,
        "user":    "Show me the top 10 best-selling products this month",
        "output":  '{"action": "get_top_products", "filters": {"conditions": [{"field": "date_from", "op": "gte", "value": "2026-06-01"}, {"field": "date_to", "op": "lte", "value": "2026-06-30"}], "sort": "quantity_sold", "sort_order": "desc", "limit": 10}}',
    },
]


def build_few_shot_block() -> str:
    """
    Render all examples as a formatted string block
    that is embedded verbatim inside the system prompt.

    Output:
        Example 1:
        User: How many units of SKU ABC-001 do we have?
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
