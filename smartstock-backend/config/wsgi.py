import os

from dotenv import find_dotenv, load_dotenv

_dotenv_path = find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path, override=True)

from django.core.wsgi import get_wsgi_application  # noqa: E402

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_wsgi_application()
