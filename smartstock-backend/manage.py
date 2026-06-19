#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

from dotenv import find_dotenv, load_dotenv

# Load backend .env with override so root monorepo .env doesn't take precedence
_dotenv_path = find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path, override=True)


def main():
    """Run administrative tasks."""
    if 'test' in sys.argv:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            'available on your PYTHONPATH environment variable? Did you '
            'forget to activate a virtual environment?'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
