from rest_framework import serializers

from .models import Document, DocumentChunk


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
