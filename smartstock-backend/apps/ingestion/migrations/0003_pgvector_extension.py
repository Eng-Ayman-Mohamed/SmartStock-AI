from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('ingestion', '0002_alter_document_options_document_created_at_and_more'),
    ]

    operations = [
        CreateExtension('vector'),
    ]
