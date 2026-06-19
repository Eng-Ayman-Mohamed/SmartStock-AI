from django.test import SimpleTestCase

from core.validators import validate_sku_code


class ValidateSkuCodeTest(SimpleTestCase):
    """Unit tests for core.validators.validate_sku_code (previously untested)."""

    def test_accepts_uppercase_alphanumeric_and_hyphen(self):
        self.assertTrue(validate_sku_code('ABC-123'))
        self.assertTrue(validate_sku_code('SKU001'))
        self.assertTrue(validate_sku_code('A-B-C-9'))

    def test_rejects_lowercase(self):
        self.assertFalse(validate_sku_code('abc-123'))

    def test_rejects_spaces_and_invalid_symbols(self):
        self.assertFalse(validate_sku_code('ABC 123'))
        self.assertFalse(validate_sku_code('ABC_123'))
        self.assertFalse(validate_sku_code('ABC@123'))

    def test_rejects_empty_string(self):
        self.assertFalse(validate_sku_code(''))
