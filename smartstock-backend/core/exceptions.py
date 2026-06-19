class StockNotFoundException(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class DuplicatePOError(Exception):
    pass


class ForecastingModelError(Exception):
    pass


class SupplierNotFoundException(Exception):
    pass


class IllegalPOTransitionError(Exception):
    pass


class LLMQuotaExhaustedError(Exception):
    """Raised when the LLM provider quota or rate limit is exceeded."""
    pass


# Keywords that indicate an LLM quota / rate-limit error across providers.
_QUOTA_KEYWORDS = (
    'insufficient_quota',
    'rate_limit_reached',
    'quota_exceeded',
    'too many requests',
    'requests per minute',
    'tokens per minute',
    'tpm',
    'rpm',
    'billing',
    'exceeded your current quota',
    'payment',
)


def is_llm_quota_error(exc: Exception) -> bool:
    """Return True if *exc* looks like an LLM provider quota / rate-limit error."""
    msg = str(exc).lower()
    return any(kw in msg for kw in _QUOTA_KEYWORDS)


def sanitize_llm_error(exc: Exception) -> str:
    """Return a short, user-friendly message for LLM errors."""
    if is_llm_quota_error(exc):
        return (
            'AI service quota has been reached. '
            'Please try again shortly or contact your admin to increase the limit.'
        )
    return 'An unexpected error occurred while processing your request.'
