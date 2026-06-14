import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Dangerous patterns that should never appear in LLM output destined for
# the repository / response layer.
_DANGEROUS_PATTERNS: list[str] = [
    'INSERT INTO',
    'DELETE FROM',
    'DROP TABLE',
    'ALTER TABLE',
    'TRUNCATE ',
    'EXEC(',
    'OS.SYSTEM',
    'SUBPROCESS.CALL',
    'SUBPROCESS.POPEN',
    'SUBPROCESS.RUN',
    'SUBPROCESS.CHECK',
    'EVAL(',
    '__IMPORT__',
]


def validate_llm_output(output: str, expected_schema: Optional[type] = None) -> bool:
    """
    Validate that *output* is well-formed JSON and, if *expected_schema*
    is provided (a Pydantic BaseModel subclass), validates it against
    that schema.

    Returns True if the output is valid, False otherwise.
    """
    cleaned = output.strip()
    if not cleaned:
        logger.warning('validate_llm_output: empty output')
        return False

    if cleaned.startswith('```'):
        lines = cleaned.split('\n')
        inner = lines[1:]
        inner_text = '\n'.join(inner).strip()
        if inner_text.endswith('```'):
            inner_text = inner_text[:-3]
        cleaned = inner_text.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning('validate_llm_output: invalid JSON — %s', exc)
        return False

    if not isinstance(data, dict):
        logger.warning('validate_llm_output: JSON root is not an object')
        return False

    if expected_schema is not None:
        try:
            expected_schema(**data)
        except Exception as exc:
            logger.warning(
                'validate_llm_output: schema validation failed for %s — %s',
                expected_schema.__name__,
                exc,
            )
            return False

    return True


def validate_response_safety(output: str) -> bool:
    """
    Check that *output* does not contain obviously dangerous content
    (raw SQL, system commands, eval, etc.) before it reaches the
    repository layer.

    Returns True if the output is safe, False otherwise.
    """
    if not output or not output.strip():
        return True

    upper = output.upper()
    for pattern in _DANGEROUS_PATTERNS:
        if pattern in upper:
            logger.warning(
                'validate_response_safety: dangerous pattern %r detected in output', pattern
            )
            return False

    return True
