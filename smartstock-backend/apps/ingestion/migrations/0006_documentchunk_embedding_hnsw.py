from django.db import migrations


def apply_hnsw_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(
            """
            CREATE INDEX IF NOT EXISTS document_chunk_embedding_hnsw
            ON ingestion_documentchunk
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """
        )


def reverse_hnsw_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute('DROP INDEX IF EXISTS document_chunk_embedding_hnsw;')


class Migration(migrations.Migration):
    """Add HNSW index for vector similarity search on DocumentChunk embeddings."""

    dependencies = [
        (
            'ingestion',
            '0005_rename_ingestion_i_uploade_bda6d0_idx_ingestion_i_uploade_300c12_idx_and_more',
        ),
    ]

    operations = [
        migrations.RunPython(apply_hnsw_index, reverse_hnsw_index),
    ]
