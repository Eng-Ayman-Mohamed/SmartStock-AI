import django.contrib.postgres.indexes
import pgvector.django.vector
from django.db import migrations


def clear_chunks(apps, schema_editor):
    """Delete all chunks — embedding dimensions are changing and existing data is incompatible."""
    Chunk = apps.get_model('ingestion', 'DocumentChunk')
    deleted, _ = Chunk.objects.all().delete()
    if deleted:
        print(f'Cleared {deleted} document chunks for embedding dimension migration')


def drop_hnsw_index(apps, schema_editor):
    """Drop any HNSW index on the embedding column (max 2000 dims)."""
    schema_editor.execute(
        "DROP INDEX IF EXISTS ingestion_documentchunk_embedding_hnsw_idx"
    )
    # Also try common naming patterns
    schema_editor.execute(
        "DROP INDEX IF EXISTS documentchunk_embedding_idx"
    )


def recreate_hnsw_index(apps, schema_editor):
    """Recreate HNSW index for 768-dimension embeddings."""
    schema_editor.execute(
        "CREATE INDEX IF NOT EXISTS ingestion_documentchunk_embedding_hnsw_idx "
        "ON ingestion_documentchunk USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


class Migration(migrations.Migration):
    dependencies = [
        ('ingestion', '0003_alter_documentchunk_embedding'),
    ]

    operations = [
        migrations.RunPython(clear_chunks, migrations.RunPython.noop),
        migrations.RunPython(drop_hnsw_index, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='documentchunk',
            name='embedding',
            field=pgvector.django.vector.VectorField(blank=True, dimensions=768, null=True),
        ),
        migrations.RunPython(recreate_hnsw_index, migrations.RunPython.noop),
    ]
