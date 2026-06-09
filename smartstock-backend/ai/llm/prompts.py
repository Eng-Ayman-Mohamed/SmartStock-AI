"""
prompts.py — Task MQ3
Builds the final system prompt that is sent to GPT-4o on every NL query request.
The few-shot block (all 5 examples) is embedded at build time, not injected per call.
"""

from ai.llm.few_shots import build_few_shot_block
from ai.llm.schemas import NLQueryAction


def build_system_prompt() -> str:
    """
    Returns the complete system prompt string.

    Structure:
      1. Role declaration
      2. Strict behavioural rules (scope + output format)
      3. JSON schema description (inline, not the full JSON object)
      4. All 5 few-shot examples
      5. Out-of-scope error instruction
    """
    allowed_actions = ", ".join(f'"{a.value}"' for a in NLQueryAction)
    few_shots = build_few_shot_block()

    return f"""You are SmartStock AI, a warehouse inventory analytics assistant.

Your role:
- Translate user natural language queries into structured database queries.
- Only operate within inventory, suppliers, sales, and purchase orders.
- Never generate free-form SQL.
- Always respond using the provided JSON schema.

Output rules:
- Respond with ONLY valid JSON. No preamble, no explanation, no markdown code fences.
- The JSON must have exactly two keys: "action" and "filters".
- "action" must be one of: {allowed_actions}
- "filters" is an object containing only these optional keys:
    product_name  (string)   — full or partial product name
    sku_code      (string)   — exact SKU code, e.g. "ABC-001"
    date_from     (string)   — ISO-8601 date "YYYY-MM-DD"
    date_to       (string)   — ISO-8601 date "YYYY-MM-DD"
    stock_below   (number)   — quantity threshold
    supplier_name (string)   — supplier company name
- Omit any filter key the user did not specify.
- If the request is outside inventory scope, respond with:
  {{"error": "Out of scope request"}}

{few_shots}"""


# Module-level constant — built once at import time, reused on every request.
SYSTEM_PROMPT: str = build_system_prompt()