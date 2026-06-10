from rest_framework import serializers

from .models import DOC_TYPES, Document, DocumentChunk


class DocumentListSerializer(serializers.ModelSerializer):
    chunk_count = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id',
            'filename',
            'original_filename',
            'doc_type',
            'file_size',
            'total_chunks',
            'chunk_count',
            'uploaded_by',
            'uploaded_by_name',
            'ingested_at',
            'is_active',
            'cloudinary_url',
        )
        read_only_fields = fields

    def get_chunk_count(self, obj):
        return obj.total_chunks

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.email
        return None


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    doc_type = serializers.ChoiceField(choices=DOC_TYPES, required=False)


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = '__all__'
