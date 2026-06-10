"""
output_parser.py — Task MQ3
Validates and converts the raw JSON string returned by GPT-4o
into a typed NLQueryResult (action enum + conditions-based filters).
into a typed NLQueryResult (action enum + conditions-based filters).

Error contract:
  - Returns NLQueryResult on success.
  - Raises NLQueryParseError with a descriptive message on any failure.
  - Never returns a result with an action value outside NLQueryAction.
"""

import json
from typing import ClassVar

from langchain_core.output_parsers import BaseOutputParser

from ai.llm.schemas import (
    NLQueryAction,
    NLQueryFilters,
    NLQueryResult,
    Condition,
    ACTION_ALLOWED_FIELDS,
    VALID_OPERATORS,
)


class NLQueryParseError(ValueError):
    """Raised when the LLM response cannot be parsed into a valid NLQueryResult."""

    pass


class NLQueryOutputParser(BaseOutputParser[NLQueryResult]):
class NLQueryOutputParser(BaseOutputParser[NLQueryResult]):
    """
    Parses the raw string output from GPT-4o into a NLQueryResult.

    Usage:
        parser = NLQueryOutputParser()
        result = parser.parse(raw_llm_output)
        # result.action  -> NLQueryAction enum member
        # result.filters -> NLQueryFilters instance with conditions
        # result.action  -> NLQueryAction enum member
        # result.filters -> NLQueryFilters instance with conditions
    """

    type: ClassVar[str] = "nl_query_output_parser"

    @property
    def _type(self) -> str:
        return self.type

    def parse(self, text: str) -> NLQueryResult:
        """
        Steps:
          1. Strip whitespace and any accidental markdown code fences.
          2. JSON-decode the string.
          3. Validate "action" is in NLQueryAction.
          4. Validate and build conditions-based NLQueryFilters.
          4. Validate and build conditions-based NLQueryFilters.
          5. Return NLQueryResult.
        """
        cleaned = self._strip_fences(text.strip())

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise NLQueryParseError(f'LLM returned invalid JSON: {exc}\nRaw output: {text!r}') from exc

        # Out-of-scope signal from the LLM
        if 'error' in data:
            raise NLQueryParseError(f'LLM reported out-of-scope: {data["error"]}')

        # Validate action
        raw_action = data.get('action')
        if not raw_action:
            raise NLQueryParseError(f"LLM response missing required 'action' key. Got: {data}")

        try:
            action = NLQueryAction(raw_action)
        except ValueError:
            valid = [a.value for a in NLQueryAction]
            raise NLQueryParseError(f"Unknown action '{raw_action}'. Valid values: {valid}")

        # Build conditions-based filters
        raw_filters = data.get("filters", {})
        if not isinstance(raw_filters, dict):
            raise NLQueryParseError(f"'filters' must be an object, got {type(raw_filters).__name__}")

        filters = self._parse_filters(raw_filters, action)
        filters = self._parse_filters(raw_filters, action)
        return NLQueryResult(action=action, filters=filters)

    def _parse_filters(self, raw: dict, action: NLQueryAction) -> NLQueryFilters:
        """Parse and validate the conditions-based filters object."""
        conditions = []
        raw_conditions = raw.get("conditions", [])

        if not isinstance(raw_conditions, list):
            raise NLQueryParseError(
                f"'conditions' must be an array, got {type(raw_conditions).__name__}"
            )

        allowed = ACTION_ALLOWED_FIELDS.get(action.value, [])

        for i, rc in enumerate(raw_conditions):
            if not isinstance(rc, dict):
                raise NLQueryParseError(
                    f"Condition at index {i} must be an object, got {type(rc).__name__}"
                )

            field = rc.get("field")
            op = rc.get("op")
            value = rc.get("value")

            if not field or not op:
                raise NLQueryParseError(
                    f"Condition at index {i} missing required 'field' or 'op'. Got: {rc}"
                )

            if op not in VALID_OPERATORS:
                raise NLQueryParseError(
                    f"Invalid operator '{op}' at condition {i}. "
                    f"Valid operators: {VALID_OPERATORS}"
                )

            if field not in allowed:
                raise NLQueryParseError(
                    f"Field '{field}' is not allowed for action '{action.value}'. "
                    f"Allowed fields: {allowed}"
                )

            conditions.append(Condition(field=field, op=op, value=value))

        sort = raw.get("sort")
        sort_order = raw.get("sort_order", "asc")
        limit = raw.get("limit")
        offset = raw.get("offset")

        if sort and sort_order not in ("asc", "desc"):
            raise NLQueryParseError(
                f"Invalid sort_order '{sort_order}'. Must be 'asc' or 'desc'."
            )

        if limit is not None and (not isinstance(limit, int) or limit < 0):
            raise NLQueryParseError(
                f"'limit' must be a non-negative integer, got {limit!r}"
            )

        if offset is not None and (not isinstance(offset, int) or offset < 0):
            raise NLQueryParseError(
                f"'offset' must be a non-negative integer, got {offset!r}"
            )

        return NLQueryFilters(
            conditions=conditions,
            sort=sort,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

    # -- private helpers -----------------------------------------------------------

    @staticmethod
    def _strip_fences(text: str) -> str:
        """
        Remove leading ```json / ``` fences that GPT-4o sometimes adds
        despite being instructed not to.
        """
        if text.startswith('```'):
            lines = text.split('\n')
            # Drop first line (```json or ```) and last line (```)
            inner = lines[1:] if lines[-1].strip() == '```' else lines[1:]
            text = '\n'.join(inner).rstrip('`').strip()
        return text
