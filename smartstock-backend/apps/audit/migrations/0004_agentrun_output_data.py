from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('audit', '0003_alter_agentrun_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentrun',
            name='output_data',
            field=models.JSONField(null=True, blank=True),
        ),
    ]
