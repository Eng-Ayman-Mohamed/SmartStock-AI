import os
import unittest
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured


REQUIRED_VARS = [
    'OPENAI_API_KEY',
    'LANGFUSE_PUBLIC_KEY',
    'LANGFUSE_SECRET_KEY',
    'COHERE_API_KEY',
    'DJANGO_SECRET_KEY',
    'DATABASE_URL',
    'REDIS_URL',
]

ALL_ENV = {var: f'test-{var.lower()}' for var in REQUIRED_VARS}


class TestValidateRequiredEnvVars(unittest.TestCase):
    def _import(self):
        import importlib
        import config.validators
        importlib.reload(config.validators)
        return config.validators.validate_required_env_vars

    @patch.dict(os.environ, {**ALL_ENV}, clear=True)
    def test_all_present_passes(self):
        validate = self._import()
        validate()

    @patch.dict(os.environ, {**ALL_ENV, 'LANGFUSE_HOST': 'https://custom.langfuse.com'}, clear=True)
    def test_optional_langfuse_host_used(self):
        validate = self._import()
        validate()

    @patch.dict(os.environ, ALL_ENV, clear=True)
    @patch.dict(os.environ, {}, clear=False)
    def test_missing_single_raises(self):
        for var in REQUIRED_VARS:
            env = {k: v for k, v in ALL_ENV.items() if k != var}
            with patch.dict(os.environ, env, clear=True):
                validate = self._import()
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    validate()
                self.assertIn(var, str(ctx.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_all_raises(self):
        validate = self._import()
        with self.assertRaises(ImproperlyConfigured) as ctx:
            validate()
        msg = str(ctx.exception)
        for var in REQUIRED_VARS:
            self.assertIn(var, msg)

    @patch.dict(os.environ, {**ALL_ENV}, clear=True)
    def test_masked_logging(self):
        validate = self._import()
        with patch('config.validators.logger') as mock_logger:
            validate()
            config_calls = [
                call for call in mock_logger.info.call_args_list
                if call[0][0].startswith('[CONFIG]')
            ]
            self.assertEqual(len(config_calls), len(REQUIRED_VARS) + 3)


class TestMaskValue(unittest.TestCase):
    def _import(self):
        import importlib
        import config.validators
        importlib.reload(config.validators)
        return config.validators._mask_value

    def test_short_value(self):
        mask = self._import()
        self.assertEqual(mask('abc'), '***')

    def test_long_value(self):
        mask = self._import()
        self.assertEqual(mask('sk-1234567890abcdef'), 'sk***ef')

    def test_exactly_four_chars(self):
        mask = self._import()
        self.assertEqual(mask('abcd'), '***')

    def test_five_chars(self):
        mask = self._import()
        self.assertEqual(mask('abcde'), 'ab***de')


if __name__ == '__main__':
    unittest.main()
