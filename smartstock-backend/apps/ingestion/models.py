from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class Document(models.Model):
    class DocType(models.TextChoices):
        POLICY = 'policy', 'Policy'
        CONTRACT = 'contract', 'Contract'
        PROCEDURE = 'procedure', 'Procedure'
        SPECIFICATION = 'specification', 'Specification'

    filename = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=500)
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file_size = models.BigIntegerField()
    total_chunks = models.IntegerField(default=0)
    cloudinary_url = models.URLField(max_length=1000)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents',
    )
    ingested_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.original_filename} ({self.doc_type})"


class DocumentChunk(models.Model):
    chunk_text = models.TextField()
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    tsvector = SearchVectorField(null=True, blank=True)
    source_document = models.CharField(max_length=500)
    page_number = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chunks',
    )

    class Meta:
        indexes = [
            models.Index(fields=['source_document']),
            models.Index(fields=['document']),
            GinIndex(fields=['tsvector'], name='document_chunk_gin_idx'),
        ]

    def __str__(self):
        return f'{self.source_document} (page {self.page_number})'
