import logging
import tempfile

import cloudinary.uploader
from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai.rag.ingestion import ingest_pdf
from apps.authentication.permissions import IsAdminOnly, IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer, ValidationErrorResponseSerializer

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: DocumentSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['ai'],
    ),
    retrieve=extend_schema(
        responses={
            200: DocumentSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Document not found'),
        },
        tags=['ai'],
    ),
    create=extend_schema(
        request=DocumentUploadSerializer,
        responses={
            201: DocumentSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Viewer or above only'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Invalid file or metadata'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
            500: OpenApiResponse(response=ErrorResponseSerializer, description='Upload or ingestion failed'),
        },
        examples=[
            OpenApiExample(
                'Upload PDF Document',
                value={
                    'file': '(binary PDF file)',
                    'doc_type': 'invoice',
                },
                request_only=True,
            ),
        ],
        tags=['ai'],
    ),
    update=extend_schema(
        request=DocumentUploadSerializer,
        responses={
            200: DocumentSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Document not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Invalid file or metadata'),
        },
        tags=['ai'],
    ),
    partial_update=extend_schema(
        request=DocumentUploadSerializer,
        responses={
            200: DocumentSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Document not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Invalid file or metadata'),
        },
        tags=['ai'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Document not found'),
        },
        tags=['ai'],
    ),
)
class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for RAG documents.

    - Viewer+: list, retrieve
    - Manager+: upload (create)
    - Admin: soft-delete
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer
    queryset = Document.objects.filter(is_active=True).order_by('-created_at')
    search_fields = ['original_filename', 'doc_type']
    ordering_fields = ['created_at', 'doc_type', 'original_filename']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action == 'create':
            return [IsViewerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsViewerOrAbove()]

    def get_queryset(self):
        if self.action == 'list':
            return Document.objects.filter(is_active=True).order_by('-created_at')
        return Document.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        doc_type = serializer.validated_data['doc_type']

        try:
            upload_result = cloudinary.uploader.upload(
                file,
                resource_type='raw',
                folder='smartstock/documents',
            )
            cloudinary_url = upload_result.get('secure_url', upload_result.get('url', ''))

            document = Document.objects.create(
                filename=upload_result.get('original_filename', file.name),
                original_filename=file.name,
                doc_type=doc_type,
                file_size=file.size,
                cloudinary_url=cloudinary_url,
                uploaded_by=request.user,
            )

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                result = ingest_pdf(tmp_path, document_id=document.id)
                document.total_chunks = result['chunks']
                document.ingested_at = timezone.now()
                document.save(update_fields=['total_chunks', 'ingested_at'])
            finally:
                import os

                os.unlink(tmp_path)

            out = DocumentSerializer(document, context={'request': request})
            return Response(out.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.exception('Document upload/ingestion failed')
            return Response(
                {'detail': f'Upload or ingestion failed: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
