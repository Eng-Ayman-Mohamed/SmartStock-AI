"""
output_parser.py — Task MQ3
Validates and converts the raw JSON string returned by GPT-4o
into a typed NLQueryResult (action enum + filters object).

Error contract:
  - Returns NLQueryResult on success.
  - Raises NLQueryParseError with a descriptive message on any failure.
  - Never returns a result with an action value outside NLQueryAction.
"""

import json
from ai.llm.schemas import NLQueryAction, NLQueryFilters, NLQueryResult


class NLQueryParseError(ValueError):
    """Raised when the LLM response cannot be parsed into a valid NLQueryResult."""
    pass


class NLQueryOutputParser:
    """
    Parses the raw string output from GPT-4o into a NLQueryResult.

    Usage:
        parser = NLQueryOutputParser()
        result = parser.parse(raw_llm_output)
        # result.action  → NLQueryAction enum member
        # result.filters → NLQueryFilters instance
    """

    def parse(self, text: str) -> NLQueryResult:
        """
        Steps:
          1. Strip whitespace and any accidental markdown code fences.
          2. JSON-decode the string.
          3. Validate "action" is in NLQueryAction.
          4. Build NLQueryFilters from the optional "filters" sub-object.
          5. Return NLQueryResult.
        """
        cleaned = self._strip_fences(text.strip())

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise NLQueryParseError(
                f"LLM returned invalid JSON: {exc}\nRaw output: {text!r}"
            ) from exc

        # Out-of-scope signal from the LLM
        if "error" in data:
            raise NLQueryParseError(f"LLM reported out-of-scope: {data['error']}")

        # Validate action
        raw_action = data.get("action")
        if not raw_action:
            raise NLQueryParseError(
                f"LLM response missing required 'action' key. Got: {data}"
            )

        try:
            action = NLQueryAction(raw_action)
        except ValueError:
            valid = [a.value for a in NLQueryAction]
            raise NLQueryParseError(
                f"Unknown action '{raw_action}'. Valid values: {valid}"
            )

        # Build filters (all keys are optional)
        raw_filters = data.get("filters", {})
        if not isinstance(raw_filters, dict):
            raise NLQueryParseError(
                f"'filters' must be an object, got {type(raw_filters).__name__}"
            )

        filters = NLQueryFilters.from_dict(raw_filters)
        return NLQueryResult(action=action, filters=filters)

    # ── private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _strip_fences(text: str) -> str:
        """
        Remove leading ```json / ``` fences that GPT-4o sometimes adds
        despite being instructed not to.
        """
        if text.startswith("```"):
            lines = text.split("\n")
            # Drop first line (```json or ```) and last line (```)
            inner = lines[1:] if lines[-1].strip() == "```" else lines[1:]
            text = "\n".join(inner).rstrip("`").strip()
        return text