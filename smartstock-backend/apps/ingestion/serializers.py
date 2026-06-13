from rest_framework import serializers

from .models import Document, DocumentChunk, InvoiceScan
from .services import INVOICE_REQUIRED_FIELDS


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(
        source='uploaded_by.username',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Document
        fields = [
            'id',
            'filename',
            'original_filename',
            'doc_type',
            'file_size',
            'cloudinary_url',
            'uploaded_by',
            'uploaded_by_username',
            'ingested_at',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'uploaded_by', 'ingested_at', 'created_at', 'updated_at']


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    doc_type = serializers.ChoiceField(choices=Document.DocType.choices)

    def validate_file(self, file):
        if not file.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('Only PDF files are accepted.')

        content_type = getattr(file, 'content_type', None)
        if content_type and content_type != 'application/pdf':
            raise serializers.ValidationError('File content type must be application/pdf.')

        header = file.read(5)
        file.seek(0)
        if not header.startswith(b'%PDF'):
            raise serializers.ValidationError('File is not a valid PDF (bad magic bytes).')

        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('File size must be less than 10 MB.')

        return file


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = [
            'id',
            'chunk_text',
            'source_document',
            'page_number',
            'metadata',
            'document',
        ]
        read_only_fields = ['id']


class RAGQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=True, max_length=500)

    def validate_query(self, value):
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise serializers.ValidationError('Query must be at least 3 characters long.')
        return cleaned


class ChatSerializer(serializers.Serializer):
    query = serializers.CharField(required=True, min_length=1, max_length=2000)
    mode = serializers.ChoiceField(
        choices=['auto', 'nl', 'rag'],
        default='auto',
        required=False,
    )

    def validate_query(self, value):
        cleaned = value.strip()
        if len(cleaned) < 1:
            raise serializers.ValidationError('Query must not be empty.')
        return cleaned


class TranscriptionSerializer(serializers.Serializer):
    audio = serializers.FileField()

    def validate_audio(self, file):
        if file.size > 25 * 1024 * 1024:
            raise serializers.ValidationError('Audio file must be less than 25 MB.')
        return file


class InvoiceScanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceScan
        fields = [
            'id',
            'original_filename',
            'content_type',
            'file_size',
            'status',
            'extracted_data',
            'confidence',
            'missing_fields',
            'failure_reason',
            'confirmed_data',
            'is_confirmed',
            'confirmed_at',
            'rejected_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class InvoiceScanUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, file):
        allowed_content_types = {
            'image/jpeg',
            'image/png',
            'application/pdf',
        }
        content_type = getattr(file, 'content_type', None)
        if content_type not in allowed_content_types:
            raise serializers.ValidationError('Accepted invoice formats are JPEG, PNG, and PDF.')
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('File size must be 5 MB or less.')
        return file


class InvoiceScanConfirmSerializer(serializers.Serializer):
    scan_id = serializers.IntegerField()
    confirmed_data = serializers.DictField()

    def validate_confirmed_data(self, value):
        missing = [field for field in INVOICE_REQUIRED_FIELDS if not value.get(field)]
        if missing:
            raise serializers.ValidationError(f'Missing required fields: {", ".join(missing)}')
        return value
