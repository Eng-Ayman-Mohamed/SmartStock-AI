# isort: skip_file
from .development import *  # noqa: F403

DEBUG = True

REST_FRAMEWORK = REST_FRAMEWORK.copy()  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/min',
    'user': '10000/min',
    'login': '10000/min',
    'ai': '10000/min',
}
