from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from pgvector.django import VectorField


class DocumentChunk(models.Model):
    chunk_text = models.TextField()
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    tsvector = SearchVectorField(null=True, blank=True)
    source_document = models.CharField(max_length=500)
    page_number = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=['source_document']),
            GinIndex(fields=['tsvector'], name='document_chunk_gin_idx'),
        ]

    def __str__(self):
        return f"{self.source_document} (page {self.page_number})"
