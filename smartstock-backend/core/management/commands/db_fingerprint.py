import hashlib
from collections import OrderedDict

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection

IGNORE_TABLES = {
    'django_session',
    'django_admin_log',
    'django_migrations',
    'django_content_type',
    'django_flatpage',
    'django_redirect',
    'auth_permission',
    'auth_group',
    'auth_group_permissions',
    'celery_taskmeta',
    'celery_tasksetmeta',
    'django_celery_beat_*',
    'django_celery_results_*',
}

APP_LABELS = [
    'authentication',
    'inventory',
    'forecasting',
    'purchasing',
    'ingestion',
    'audit',
]


class Command(BaseCommand):
    help = 'Print a deterministic fingerprint of the current database state'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detail',
            action='store_true',
            default=False,
            help='Include full migration list and model row counts',
        )
        parser.add_argument(
            '--tables',
            type=str,
            default='',
            help='Comma-separated table names to hash (default: all app tables)',
        )

    def handle(self, *args, **options):
        detail = options.get('detail', False)
        tables_filter = options.get('tables', '').strip()

        with connection.cursor() as cursor:
            # ---- 1. Migration count ----
            cursor.execute('SELECT COUNT(*) FROM django_migrations')
            migration_count = cursor.fetchone()[0]

            # ---- 2. Migration list ----
            cursor.execute('SELECT app, name FROM django_migrations ORDER BY app, applied')
            migrations = cursor.fetchall()

            # ---- 3. Model row counts ----
            table_rows = OrderedDict()
            all_models = []
            for label in APP_LABELS:
                try:
                    app_config = apps.get_app_config(label)
                    all_models.extend(app_config.get_models())
                except LookupError:
                    pass

            for model in all_models:
                table = model._meta.db_table
                if any(table.startswith(p.strip()) for p in IGNORE_TABLES):
                    continue
                count = model.objects.count()
                table_rows[table] = count

            # ---- 4. Latest record timestamps ----
            latest_entries = OrderedDict()
            ts_models = [m for m in all_models if hasattr(m, '_meta')]
            for model in ts_models:
                table = model._meta.db_table
                for field in model._meta.fields:
                    if field.name in ('created_at', 'timestamp', 'date', 'applied'):
                        try:
                            latest = (
                                model.objects.order_by(f'-{field.column}')
                                .values_list(field.column, flat=True)
                                .first()
                            )
                            if latest:
                                latest_entries[table] = str(latest)[:19]
                        except Exception:
                            pass
                        break

            # ---- 5. SHA-256 fingerprint ----
            hash_input_parts = [f'migrations:{migration_count}']
            hash_input_parts.extend(f'{app}:{name}' for app, name in migrations)
            hash_input_parts.extend(f'{table}:{count}' for table, count in table_rows.items())
            hash_input_parts.extend(f'{table}:{ts}' for table, ts in latest_entries.items())

            # Optionally include actual data from specified tables
            if tables_filter:
                for tbl in tables_filter.split(','):
                    tbl = tbl.strip()
                    try:
                        cursor.execute(
                            f"SELECT md5(string_agg(t::text, ',' ORDER BY t)) FROM (SELECT t FROM {tbl} t LIMIT 1000) sub"
                        )
                        row = cursor.fetchone()
                        if row and row[0]:
                            hash_input_parts.append(f'{tbl}:{row[0]}')
                    except Exception:
                        hash_input_parts.append(f'{tbl}:ERROR')

            raw = '|'.join(hash_input_parts)
            fingerprint = hashlib.sha256(raw.encode()).hexdigest()

        # ---- Output ----
        self.stdout.write('=' * 60)
        self.stdout.write('  SmartStock DB Fingerprint')
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Host:          {connection.settings_dict.get("HOST", "?")}')
        self.stdout.write(f'  Database:      {connection.settings_dict.get("NAME", "?")}')
        self.stdout.write(f'  Migrations:    {migration_count}')
        self.stdout.write(f'  App tables:    {len(table_rows)}')
        self.stdout.write(f'  Fingerprint:   {fingerprint}')
        self.stdout.write('=' * 60)

        if detail:
            self.stdout.write()
            self.stdout.write('--- Migrations ---')
            current_app = ''
            for app, name in migrations:
                label = f'  {app}' if app != current_app else '  ' + ' ' * len(app)
                self.stdout.write(f'{label}  {name}')
                current_app = app

            self.stdout.write()
            self.stdout.write('--- Row Counts ---')
            for table, count in table_rows.items():
                self.stdout.write(f'  {table:<35} {count:>8}')

            self.stdout.write()
            self.stdout.write('--- Latest Timestamps ---')
            for table, ts in latest_entries.items():
                self.stdout.write(f'  {table:<35} {ts}')
