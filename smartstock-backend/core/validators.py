import re


def validate_sku_code(code: str) -> bool:
    return bool(re.match(r'^[A-Z0-9-]+$', code))
