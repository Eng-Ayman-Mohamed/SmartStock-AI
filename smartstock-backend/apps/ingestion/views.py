import logging
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

import cloudinary.uploader
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ai.llm.chain import prompt_injection_filter
from ai.rag.ingestion import ingest_pdf
from apps.audit.models import AuditLog
from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer, RAGQuerySerializer

logger = logging.getLogger(__name__)


class RAGServiceUnavailable(Exception):
    """Raised when an upstream RAG service (e.g. Cohere) is unavailable."""

    def __init__(self, message: str = 'Service unavailable'):
        self.message = message
        super().__init__(self.message)


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


# ---------------------------------------------------------------------------
# RAG Query Endpoint  — POST /api/ai/rag-query/
# ---------------------------------------------------------------------------

_langfuse_client = None


def _get_langfuse():
    global _langfuse_client
    if _langfuse_client is None:
        try:
            from django.conf import settings
            from langfuse import Langfuse

            public_key = getattr(settings, 'LANGFUSE_PUBLIC_KEY', None)
            secret_key = getattr(settings, 'LANGFUSE_SECRET_KEY', None)
            if public_key and secret_key:
                _langfuse_client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=getattr(settings, 'LANGFUSE_HOST', 'https://cloud.langfuse.com'),
                )
        except Exception:
            _langfuse_client = None
    return _langfuse_client


class RAGQueryView(APIView):
    """
    POST /api/ai/rag-query/
    Accepts { "query": "string" } and returns an LLM-generated answer
    grounded in internal documents, with mandatory source citations.
    """

    permission_classes = [IsManagerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    RAG_TIMEOUT_SECONDS = 8

    @extend_schema(
        request=RAGQuerySerializer,
        responses={
            200: inline_serializer(
                'RAGQueryResponse',
                {
                    'status': serializers.CharField(),
                    'data': inline_serializer(
                        'RAGQueryData',
                        {
                            'answer': serializers.CharField(),
                            'sources': serializers.ListField(child=serializers.DictField()),
                        },
                    ),
                },
            ),
            400: None,
            503: None,
            504: None,
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = RAGQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        query = serializer.validated_data['query']

        # --- Prompt injection check (Task A10) ---
        try:
            is_safe = prompt_injection_filter(query)
        except Exception:
            logger.exception('Prompt injection filter failed')
            is_safe = True

        if not is_safe:
            AuditLog.objects.create(
                user=request.user,
                event='PROMPT_INJECTION_ATTEMPT',
                data_snapshot={'query': query[:200]},
            )
            return Response(
                {'status': 'error', 'error': 'InvalidQueryError', 'message': 'Query contains disallowed content.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Execute RAG pipeline with timeout ---
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_pipeline, query, request.user)
                result = future.result(timeout=self.RAG_TIMEOUT_SECONDS)
        except FuturesTimeout:
            return Response(
                {'status': 'error', 'message': 'Request timed out. Please try a simpler question.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except RAGServiceUnavailable as e:
            return Response(
                {'status': 'error', 'message': e.message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.exception('RAG pipeline failed')
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)

    def _run_pipeline(self, query: str, user) -> dict:
        from .services import RAGQueryService

        pipeline_start = time.time()
        service = RAGQueryService()

        try:
            result = service.execute(query, user=user)
        except ConnectionError as e:
            if 'COHERE' in str(e).upper():
                raise RAGServiceUnavailable('Cohere reranking service is unavailable. Please try again later.')
            raise ValueError(f'Service unavailable: {e}')
        except Exception as e:
            raise ValueError(f'Pipeline error: {e}')

        # --- Langfuse tracing ---
        latency_ms = round((time.time() - pipeline_start) * 1000)
        self._trace_rag_query(user, query, result, latency_ms)

        return {
            'answer': result['answer'],
            'sources': result['sources'],
        }

    def _trace_rag_query(self, user, query: str, result: dict, latency_ms: int):
        trace_data = {
            'query': query,
            'chunks_retrieved': result.get('chunks_retrieved', 0),
            'chunks_reranked': result.get('chunks_reranked', 0),
            'retrieved_chunks': result.get('retrieved_chunks', []),
            'sources': result.get('sources', []),
            'latency_ms': latency_ms,
            'answer_length': len(result.get('answer', '')),
            'token_usage': result.get('token_usage', {}),
        }

        # Audit log (always available)
        try:
            AuditLog.objects.create(
                user=user,
                event='AI_RAG_QUERY',
                data_snapshot=trace_data,
            )
        except Exception as e:
            logger.debug('Audit log failed: %s', e)

        # Langfuse tracing (optional — only if configured)
        try:
            lf = _get_langfuse()
            if lf is not None:
                trace = lf.trace(
                    name='rag_query',
                    user_id=str(user.id) if user else 'anonymous',
                    metadata={'latency_ms': latency_ms},
                )
                trace.span(
                    name='retrieval',
                    input={'query': query},
                    output={
                        'chunks_retrieved': result.get('chunks_retrieved', 0),
                        'chunks_reranked': result.get('chunks_reranked', 0),
                        'retrieved_chunks': result.get('retrieved_chunks', []),
                    },
                )
                trace.span(
                    name='generation',
                    input={'query': query},
                    output={
                        'answer': result.get('answer', ''),
                        'sources': result.get('sources', []),
                        'token_usage': result.get('token_usage', {}),
                    },
                )
                lf.flush()
        except Exception as lf_err:
            logger.debug('Langfuse trace skipped: %s', lf_err)
