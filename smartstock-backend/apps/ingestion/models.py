from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from pgvector.django import VectorField

DOC_TYPES = [
    ('pdf', 'PDF'),
    ('csv', 'CSV'),
    ('xlsx', 'Excel'),
    ('docx', 'Word'),
    ('txt', 'Plain Text'),
]


class Document(models.Model):
    filename = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=500)
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
    file_size = models.IntegerField()
    total_chunks = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    ingested_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    cloudinary_url = models.URLField(max_length=1000)

    def __str__(self):
        return self.original_filename


class DocumentChunk(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='chunks', null=True, blank=True
    )
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
        return f'{self.source_document} (page {self.page_number})'
