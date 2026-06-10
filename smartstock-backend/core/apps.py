import os

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        if os.environ.get('CI'):
            return

        from config.validators import validate_required_env_vars

        validate_required_env_vars()
