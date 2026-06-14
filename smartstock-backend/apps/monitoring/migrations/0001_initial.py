import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('name', models.CharField(max_length=200, unique=True)),
                ('description', models.TextField(blank=True)),
                (
                    'severity',
                    models.CharField(
                        choices=[
                            ('info', 'Info'),
                            ('warning', 'Warning'),
                            ('critical', 'Critical'),
                        ],
                        default='warning',
                        max_length=20,
                    ),
                ),
                ('metric_name', models.CharField(max_length=200)),
                ('threshold', models.FloatField()),
                ('evaluation_window_minutes', models.IntegerField(default=5)),
                ('enabled', models.BooleanField(default=True)),
                ('cooldown_minutes', models.IntegerField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='AlertEvent',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('pending', 'Pending'),
                            ('firing', 'Firing'),
                            ('resolved', 'Resolved'),
                        ],
                        default='pending',
                        max_length=20,
                    ),
                ),
                ('triggered_value', models.FloatField(blank=True, null=True)),
                ('message', models.TextField(blank=True)),
                ('email_sent', models.BooleanField(default=False)),
                ('dashboard_notified', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'rule',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='events',
                        to='monitoring.alertrule',
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DashboardBanner',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                (
                    'level',
                    models.CharField(
                        choices=[('info', 'Info'), ('warning', 'Warning'), ('error', 'Error')],
                        default='info',
                        max_length=20,
                    ),
                ),
                ('dismissed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                (
                    'alert_event',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='banners',
                        to='monitoring.alertevent',
                    ),
                ),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TokenUsageLog',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('total_tokens', models.IntegerField(default=0)),
                ('input_tokens', models.IntegerField(default=0)),
                ('output_tokens', models.IntegerField(default=0)),
                ('daily_total', models.IntegerField(default=0)),
                ('logged_at', models.DateField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AgentRunLog',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('agent_name', models.CharField(max_length=100)),
                (
                    'outcome',
                    models.CharField(
                        choices=[('success', 'Success'), ('failure', 'Failure')], max_length=20
                    ),
                ),
                ('duration_ms', models.IntegerField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='alertevent',
            index=models.Index(fields=['rule', 'status'], name='monitoring__rule_st_idx'),
        ),
        migrations.AddIndex(
            model_name='alertevent',
            index=models.Index(fields=['created_at'], name='monitoring__created_idx'),
        ),
        migrations.AddIndex(
            model_name='dashboardbanner',
            index=models.Index(fields=['dismissed', 'level'], name='monitoring__dismiss_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenusagelog',
            index=models.Index(fields=['logged_at'], name='monitoring__logged_idx'),
        ),
        migrations.AddIndex(
            model_name='agentrunlog',
            index=models.Index(fields=['agent_name', 'outcome'], name='monitoring__agent_idx'),
        ),
        migrations.AddIndex(
            model_name='agentrunlog',
            index=models.Index(fields=['created_at'], name='monitoring__arun_c_idx'),
        ),
    ]
