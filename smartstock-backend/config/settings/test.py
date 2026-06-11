# isort: skip_file
from .development import *  # noqa: F403

import logging

from django.contrib.postgres.indexes import GinIndex
from django.db import models

logger = logging.getLogger(__name__)

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ---------------------------------------------------------------------------
# Monkey-patches to make PostgreSQL-only features work on SQLite during tests
# ---------------------------------------------------------------------------

# Patch VectorField to store as TEXT on SQLite
try:
    from pgvector.django import VectorField

    _orig_vector_db_type = VectorField.db_type

    def _test_vector_db_type(self, connection):
        if connection.vendor == 'sqlite':
            return 'text'
        return _orig_vector_db_type(self, connection)

    VectorField.db_type = _test_vector_db_type
except ImportError:
    logger.warning('pgvector not installed; VectorField mock skipped')

# Patch GinIndex to degrade to a plain Index on SQLite
_orig_gin_create_sql = GinIndex.create_sql

def _test_gin_create_sql(self, model, schema_editor, **kwargs):
    if schema_editor.connection.vendor == 'sqlite':
        return models.Index(fields=self.fields, name=self.name).create_sql(
            model, schema_editor, **kwargs
        )
    return _orig_gin_create_sql(self, model, schema_editor, **kwargs)

GinIndex.create_sql = _test_gin_create_sql

# Patch CreateExtension to skip on non-PostgreSQL
from django.contrib.postgres.operations import CreateExtension  # noqa: E402
from django.db.migrations.operations.special import RunSQL  # noqa: E402

_orig_create_extension_database_forwards = CreateExtension.database_forwards

def _test_create_extension_database_forwards(self, app_label, schema_editor, from_state, to_state):
    if schema_editor.connection.vendor != 'postgresql':
        logger.info('Skipping CreateExtension(%s) on %s', self.name, schema_editor.connection.vendor)
        return
    return _orig_create_extension_database_forwards(self, app_label, schema_editor, from_state, to_state)

CreateExtension.database_forwards = _test_create_extension_database_forwards

_old_runsql_database_forwards = RunSQL.database_forwards

def _test_runsql_database_forwards(self, app_label, schema_editor, from_state, to_state):
    sql = self.sql
    if isinstance(sql, str) and 'CREATE EXTENSION' in sql.upper():
        if schema_editor.connection.vendor != 'postgresql':
            logger.info('Skipping RunSQL(%s) on %s', sql[:60], schema_editor.connection.vendor)
            return
    return _old_runsql_database_forwards(self, app_label, schema_editor, from_state, to_state)

RunSQL.database_forwards = _test_runsql_database_forwards

REST_FRAMEWORK = REST_FRAMEWORK.copy()  # noqa: F405
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/min',
    'user': '10000/min',
    'login': '10000/min',
    'ai': '10000/min',
}

# Disable Cloudinary for tests
import cloudinary  # noqa: E402, F811
cloudinary.config(cloudinary_url='')

# Disable Redis cache for tests — use LocMem with a no-op delete_pattern
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# DummyCache does not support delete_pattern used by inventory cache invalidation
import django.core.cache.backends.locmem  # noqa: E402

_orig_delete_pattern = getattr(django.core.cache.backends.locmem.LocMemCache, 'delete_pattern', None)
if _orig_delete_pattern is None:
    django.core.cache.backends.locmem.LocMemCache.delete_pattern = lambda self, pattern, version=None: None

# In-memory email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
