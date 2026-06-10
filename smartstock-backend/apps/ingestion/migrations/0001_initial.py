import django.contrib.postgres.indexes
import django.contrib.postgres.search
import pgvector.django
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;",
        ),
        migrations.CreateModel(
            name='DocumentChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_text', models.TextField()),
                ('embedding', pgvector.django.VectorField(dimensions=1536, null=True, blank=True)),
                ('tsvector', django.contrib.postgres.search.SearchVectorField(null=True, blank=True)),
                ('source_document', models.CharField(max_length=500)),
                ('page_number', models.IntegerField(null=True, blank=True)),
                ('metadata', models.JSONField(default=dict)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['source_document'], name='ingestion_so_docume_idx'),
                    django.contrib.postgres.indexes.GinIndex(fields=['tsvector'], name='document_chunk_gin_idx'),
                ],
            },
        ),
    ]
