import json as _json
import logging
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

import cloudinary.uploader
from django.core.exceptions import ObjectDoesNotExist
from django.http import StreamingHttpResponse
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ai.llm.chain import prompt_injection_filter
from ai.observability.langfuse import get_langfuse_alert_thresholds, get_langfuse_client
from ai.rag.ingestion import ingest_pdf
from apps.ai.services import ConversationService
from apps.audit.models import AuditLog
from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer, ValidationErrorResponseSerializer
from core.exceptions import LLMQuotaExhaustedError, is_llm_quota_error, sanitize_llm_error

from .models import Document, DocumentChunk
from .serializers import (
    ChatSerializer,
    DocumentChunkSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    InvoiceScanConfirmSerializer,
    InvoiceScanUploadSerializer,
    RAGQuerySerializer,
    TranscriptionSerializer,
)
from .services import (
    InvoiceAlreadyConfirmed,
    InvoiceExtractionMalformed,
    InvoiceExtractionTimeout,
    InvoiceScanService,
    RAGQueryService,
)

logger = logging.getLogger(__name__)


class RAGServiceUnavailable(Exception):
    """Raised when an upstream RAG service (e.g. Cohere) is unavailable."""

    def __init__(self, message: str = 'Service unavailable'):
        self.message = message
        super().__init__(self.message)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: DocumentSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['ai'],
    ),
    retrieve=extend_schema(
        responses={
            200: DocumentSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Document not found'
            ),
        },
        tags=['ai'],
    ),
    create=extend_schema(
        request=DocumentUploadSerializer,
        responses={
            201: DocumentSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description='Viewer or above only'
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Invalid file or metadata'
            ),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
            500: OpenApiResponse(
                response=ErrorResponseSerializer, description='Upload or ingestion failed'
            ),
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
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Document not found'
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Invalid file or metadata'
            ),
        },
        tags=['ai'],
    ),
    partial_update=extend_schema(
        request=DocumentUploadSerializer,
        responses={
            200: DocumentSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Bad request'
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Document not found'
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Invalid file or metadata'
            ),
        },
        tags=['ai'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Document not found'
            ),
        },
        tags=['ai'],
    ),
)
class DocumentViewSet(viewsets.ModelViewSet):
    """CRUD for RAG documents.

    - Viewer+: list, retrieve, upload (create)
    - Admin: soft-delete
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer
    queryset = Document.objects.filter(is_active=True).order_by('-created_at')
    search_fields = ['original_filename', 'doc_type']
    ordering_fields = ['created_at', 'doc_type', 'original_filename']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [IsViewerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsViewerOrAbove()]

    def get_queryset(self):
        return Document.objects.filter(is_active=True).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        doc_type = serializer.validated_data['doc_type']

        tmp_path = None
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

            file.seek(0)
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            result = ingest_pdf(tmp_path, document_id=document.id)
            document.total_chunks = result['chunks']
            document.ingested_at = timezone.now()
            document.save(update_fields=['total_chunks', 'ingested_at'])

            out = DocumentSerializer(document, context={'request': request})
            return Response(out.data, status=status.HTTP_201_CREATED)

        except Exception:
            logger.exception('Document upload/ingestion failed')
            return Response(
                {'detail': 'Upload or ingestion failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            200: DocumentChunkSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Document not found'
            ),
        },
        tags=['ai'],
    )
    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        document = self.get_object()
        chunks = DocumentChunk.objects.filter(document=document).order_by('id')
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# RAG Query Endpoint  — POST /api/ai/rag-query/
# ---------------------------------------------------------------------------


def _get_langfuse():
    return get_langfuse_client()


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
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Bad request or prompt injection detected',
            ),
            503: OpenApiResponse(
                response=ErrorResponseSerializer, description='RAG service unavailable'
            ),
            504: OpenApiResponse(response=ErrorResponseSerializer, description='Gateway timeout'),
        },
        examples=[
            OpenApiExample(
                'RAG Query Request',
                value={'query': 'What are our top selling products this month?'},
                request_only=True,
            ),
            OpenApiExample(
                'RAG Query Response',
                value={
                    'status': 'success',
                    'data': {
                        'answer': 'Based on the sales data, your top selling products are...',
                        'sources': [{'document': 'sales_report.pdf', 'page': 1}],
                    },
                },
                response_only=True,
            ),
        ],
        tags=['ai'],
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
            is_safe, matched_pattern = prompt_injection_filter(query)
        except Exception:
            logger.exception('Prompt injection filter failed')
            is_safe, matched_pattern = False, 'filter_error'

        if not is_safe:
            AuditLog.objects.create(
                user=request.user,
                event='PROMPT_INJECTION_ATTEMPT',
                data_snapshot={'query': query[:200], 'matched_pattern': matched_pattern},
            )
            return Response(
                {
                    'status': 'error',
                    'error': 'InvalidQueryError',
                    'message': 'Query contains disallowed content.',
                },
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
        except Exception:
            logger.exception('RAG pipeline failed')
            return Response(
                {
                    'status': 'error',
                    'message': 'An internal error occurred. Please try again later.',
                },
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
                raise RAGServiceUnavailable(
                    'Cohere reranking service is unavailable. Please try again later.'
                )
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
                    metadata={
                        'latency_ms': latency_ms,
                        'alert_thresholds': get_langfuse_alert_thresholds(),
                    },
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


# ---------------------------------------------------------------------------
# Transcription Endpoint  — POST /api/ai/transcribe/
# ---------------------------------------------------------------------------


class TranscribeView(APIView):
    permission_classes = [IsManagerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'audio': {'type': 'string', 'format': 'binary'},
                },
                'required': ['audio'],
            }
        },
        responses={
            200: inline_serializer(
                'TranscriptionResponse',
                {
                    'status': serializers.CharField(),
                    'data': inline_serializer(
                        'TranscriptionData',
                        {'text': serializers.CharField()},
                    ),
                },
            ),
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Bad request'),
            500: OpenApiResponse(
                response=ErrorResponseSerializer, description='Transcription failed'
            ),
        },
        tags=['ai'],
    )
    def post(self, request, *args, **kwargs):
        serializer = TranscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        audio_file = serializer.validated_data['audio']
        audio_data = audio_file.read()

        try:
            from ai.multimodal.whisper import SpeechTranscriber

            transcriber = SpeechTranscriber()
            text = transcriber.transcribe(audio_data, filename=audio_file.name)
            return Response({'status': 'success', 'data': {'text': text}})
        except ValueError as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            logger.exception('Transcription failed')
            return Response(
                {'status': 'error', 'message': 'Transcription failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# Invoice Scan Endpoints
# ---------------------------------------------------------------------------


class InvoiceScanView(APIView):
    permission_classes = [IsManagerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    def post(self, request, *args, **kwargs):
        serializer = InvoiceScanUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = InvoiceScanService()
        try:
            result = service.scan_invoice(serializer.validated_data['file'], request.user)
        except InvoiceExtractionTimeout as exc:
            return Response(
                {
                    'status': 'error',
                    'error': 'InvoiceExtractionTimeout',
                    'message': str(exc),
                    'code': status.HTTP_504_GATEWAY_TIMEOUT,
                },
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except InvoiceExtractionMalformed as exc:
            msg = str(exc)
            code = status.HTTP_422_UNPROCESSABLE_ENTITY
            err_type = 'InvoiceExtractionMalformed'
            if 'does not support vision' in msg:
                code = status.HTTP_501_NOT_IMPLEMENTED
                err_type = 'ProviderNotSupported'
            return Response(
                {
                    'status': 'error',
                    'error': err_type,
                    'message': msg,
                    'code': code,
                },
                status=code,
            )
        return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)


class InvoiceScanConfirmView(APIView):
    permission_classes = [IsManagerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    def post(self, request, *args, **kwargs):
        serializer = InvoiceScanConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = InvoiceScanService()
        try:
            result = service.confirm_scan(
                serializer.validated_data['scan_id'],
                request.user,
                serializer.validated_data['confirmed_data'],
            )
        except PermissionError as exc:
            return Response(
                {
                    'status': 'error',
                    'error': 'PermissionDenied',
                    'message': str(exc),
                    'code': status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvoiceAlreadyConfirmed as exc:
            return Response(
                {
                    'status': 'error',
                    'error': 'InvoiceAlreadyConfirmed',
                    'message': str(exc),
                    'code': status.HTTP_409_CONFLICT,
                },
                status=status.HTTP_409_CONFLICT,
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'error': 'DoesNotExist',
                    'message': 'Invoice scan not found.',
                    'code': status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)


class InvoiceScanRejectView(APIView):
    permission_classes = [IsManagerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    def post(self, request, scan_id: int, *args, **kwargs):
        service = InvoiceScanService()
        try:
            result = service.reject_scan(scan_id, request.user)
        except PermissionError as exc:
            return Response(
                {
                    'status': 'error',
                    'error': 'PermissionDenied',
                    'message': str(exc),
                    'code': status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except InvoiceAlreadyConfirmed as exc:
            return Response(
                {
                    'status': 'error',
                    'error': 'InvoiceAlreadyConfirmed',
                    'message': str(exc),
                    'code': status.HTTP_409_CONFLICT,
                },
                status=status.HTTP_409_CONFLICT,
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': 'error',
                    'error': 'DoesNotExist',
                    'message': 'Invoice scan not found.',
                    'code': status.HTTP_404_NOT_FOUND,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Unified Chat Endpoint  — POST /api/ai/chat/
# ---------------------------------------------------------------------------


class ChatEndpointView(APIView):
    """
    POST /api/ai/chat/
    Unified endpoint that routes queries to NL Query or RAG engine
    based on mode parameter or automatic intent classification.
    """

    permission_classes = [IsViewerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    CHAT_TIMEOUT_SECONDS = 25

    @extend_schema(
        request=ChatSerializer,
        responses={
            200: inline_serializer(
                'ChatResponse',
                {
                    'status': serializers.CharField(),
                    'data': inline_serializer(
                        'ChatData',
                        {
                            'engine': serializers.CharField(),
                            'mode': serializers.CharField(),
                            'answer': serializers.CharField(),
                            'action': serializers.DictField(required=False),
                            'sources': serializers.ListField(
                                child=serializers.DictField(), required=False
                            ),
                        },
                    ),
                },
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Bad request or prompt injection detected',
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
            504: OpenApiResponse(response=ErrorResponseSerializer, description='Gateway timeout'),
        },
        examples=[
            OpenApiExample(
                'Chat Request (auto)',
                value={'query': 'How many Widget-001 do we have?'},
                request_only=True,
            ),
            OpenApiExample(
                'Chat Request (explicit mode)',
                value={'query': 'What is our return policy?', 'mode': 'rag'},
                request_only=True,
            ),
            OpenApiExample(
                'Chat Response',
                value={
                    'status': 'success',
                    'data': {
                        'engine': 'nl_query',
                        'mode': 'auto',
                        'answer': 'You have 42 units of Widget-001 in stock.',
                        'action': {'type': 'get_inventory', 'filters': {}},
                    },
                },
                response_only=True,
            ),
        ],
        tags=['ai'],
    )
    def post(self, request, *args, **kwargs):
        serializer = ChatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        query = serializer.validated_data['query']
        mode = serializer.validated_data['mode']
        conversation_id = serializer.validated_data.get('conversation_id')

        # --- Prompt injection check (Task A10) ---
        try:
            is_safe, matched_pattern = prompt_injection_filter(query)
        except Exception:
            logger.exception('Prompt injection filter failed')
            is_safe, matched_pattern = False, 'filter_error'

        if not is_safe:
            AuditLog.objects.create(
                user=request.user,
                event='PROMPT_INJECTION_ATTEMPT',
                data_snapshot={
                    'query': query[:200],
                    'matched_pattern': matched_pattern,
                    'endpoint': 'chat',
                },
            )
            return Response(
                {
                    'status': 'error',
                    'error': 'InvalidQueryError',
                    'message': 'Query contains disallowed content.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Intent classification (only for auto mode) ---
        classifier_decision = None
        if mode == 'auto':
            from ai.llm.intent_classifier import classify_intent

            classification = classify_intent(query)
            classifier_decision = classification.intent

            # If confidence is below 0.7, default to nl_query (safer for operational queries)
            if classification.confidence < 0.7:
                engine = 'nl_query'
            elif classification.intent == 'out_of_scope':
                # For out_of_scope with high confidence, still try nl_query as fallback
                engine = 'nl_query'
            else:
                engine = classification.intent
        else:
            engine = mode

        # --- Load conversation history (only for RAG — NL query path ignores it) ---
        conv_service = ConversationService()
        history = []
        if conversation_id and engine == 'rag':
            try:
                conversation = conv_service.get_conversation(conversation_id, request.user)
                history = conv_service.get_history_for_llm(conversation_id)
            except ValueError:
                return Response(
                    {'status': 'error', 'message': 'Conversation not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif conversation_id:
            try:
                conversation = conv_service.get_conversation(conversation_id, request.user)
            except ValueError:
                return Response(
                    {'status': 'error', 'message': 'Conversation not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # --- Execute pipeline with timeout ---
        pipeline_start = time.time()
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._run_engine, engine, query, request.user, history)
        try:
            result = future.result(timeout=self.CHAT_TIMEOUT_SECONDS)
            executor.shutdown(wait=False)
        except FuturesTimeout:
            executor.shutdown(wait=False)
            logger.warning('Chat pipeline timed out after %ds', self.CHAT_TIMEOUT_SECONDS)
            return Response(
                {'status': 'error', 'message': 'Request timed out. Please try a simpler question.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except RAGServiceUnavailable as exc:
            executor.shutdown(wait=False)
            return Response(
                {'status': 'error', 'message': exc.message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except LLMQuotaExhaustedError as exc:
            executor.shutdown(wait=False)
            logger.warning('LLM quota exhausted: %s', exc)
            return Response(
                {'status': 'error', 'message': sanitize_llm_error(exc)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ValueError as exc:
            executor.shutdown(wait=False)
            msg = str(exc)
            if msg == 'PROMPT_INJECTION_DETECTED':
                logger.warning('Prompt injection blocked in NL query pipeline')
                return Response(
                    {'status': 'error', 'message': 'Query contains disallowed content.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            logger.exception('Chat pipeline error')
            return Response(
                {'status': 'error', 'message': 'An unexpected error occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as exc:
            executor.shutdown(wait=False)
            logger.exception('Chat pipeline failed')
            msg = (
                sanitize_llm_error(exc)
                if is_llm_quota_error(exc)
                else 'An unexpected error occurred while processing your request.'
            )
            return Response(
                {'status': 'error', 'message': msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        latency_ms = round((time.time() - pipeline_start) * 1000)

        # --- Save to conversation ---
        if conversation_id:
            is_new = conversation.messages.count() == 0
            conv_service.save_message(
                conversation_id=conversation_id,
                role='user',
                content=query,
                mode=mode,
            )
            conv_service.save_message(
                conversation_id=conversation_id,
                role='assistant',
                content=result.get('answer', ''),
                engine=engine,
                sources=result.get('sources', []),
                mode=mode,
            )
            if is_new:
                conv_service.auto_title(conversation_id, query)

        # --- Build response ---
        response_data = {
            'engine': engine,
            'mode': mode,
            'answer': result.get('answer', ''),
        }
        if 'action' in result:
            response_data['action'] = result['action']
        if 'sources' in result:
            response_data['sources'] = result['sources']
        if conversation_id:
            response_data['conversation_id'] = str(conversation_id)

        # --- Tracing and audit ---
        self._trace_chat(
            user=request.user,
            query=query,
            mode=mode,
            engine=engine,
            classifier_decision=classifier_decision,
            result=result,
            latency_ms=latency_ms,
        )

        return Response({'status': 'success', 'data': response_data}, status=status.HTTP_200_OK)

    def _run_engine(self, engine: str, query: str, user, history: list | None = None) -> dict:
        """Dispatch to the appropriate engine and return a normalized result dict."""
        if engine == 'rag':
            return self._run_rag(query, user, history)
        return self._run_nl_query(query, user, history)

    def _run_rag(self, query: str, user, history: list | None = None) -> dict:
        """Execute the RAG pipeline via RAGQueryService."""
        service = RAGQueryService()
        try:
            result = service.execute(query, user=user, history=history)
        except ConnectionError as exc:
            if 'COHERE' in str(exc).upper():
                raise RAGServiceUnavailable(
                    'Cohere reranking service is unavailable. Please try again later.'
                )
            raise ValueError(f'Service unavailable: {exc}')

        return {
            'answer': result['answer'],
            'sources': result['sources'],
        }

    def _run_nl_query(self, query: str, user, history: list | None = None) -> dict:
        """Execute the NL Query pipeline — mirrors NLQueryEndpointView._run_pipeline."""
        # Defense-in-depth: prompt injection check (caller also checks in post())
        is_safe, matched_pattern = prompt_injection_filter(query)
        if not is_safe:
            AuditLog.objects.create(
                user=user,
                event='PROMPT_INJECTION_ATTEMPT',
                data_snapshot={
                    'query': query[:200],
                    'matched_pattern': matched_pattern,
                    'endpoint': 'chat_nl_query',
                },
            )
            raise ValueError('PROMPT_INJECTION_DETECTED')

        from ai.llm.chain import call_gpt4o_formatter, get_nl_chain
        from apps.inventory.views import (
            _handle_forecast_demand,
            _handle_get_inventory,
            _handle_get_low_stock,
            _handle_get_sales_report,
            _handle_get_supplier_info,
            _handle_get_top_products,
            _handle_get_total_value,
        )

        # Step B: LangChain Processing
        try:
            chain_instance = get_nl_chain()
            chain_result = chain_instance.run(query)
            chain_dict = chain_result.to_dict()
            action_type = chain_dict.get('action')
            filters = chain_dict.get('filters', {})
        except Exception as exc:
            raise ValueError(f'LLM Chain failure: {exc}')

        # Step C: Dispatch to handler
        handler_map = {
            'get_inventory': _handle_get_inventory,
            'get_sales_report': _handle_get_sales_report,
            'get_low_stock': _handle_get_low_stock,
            'forecast_demand': _handle_forecast_demand,
            'get_supplier_info': _handle_get_supplier_info,
            'get_total_value': _handle_get_total_value,
            'get_top_products': _handle_get_top_products,
        }
        handler = handler_map.get(action_type)
        if not handler:
            raise ValueError(f'Unknown action type: {action_type}')

        try:
            from ai.llm.schemas import NLQueryFilters

            nl_filters = NLQueryFilters(**filters) if isinstance(filters, dict) else filters
            raw_data = handler(nl_filters)
        except Exception as exc:
            raise ValueError(f'Database execution error: {exc}')

        # Step D: Format to natural language
        try:
            answer = call_gpt4o_formatter(original_query=query, raw_data=raw_data)
        except Exception as exc:
            logger.exception('Formatter failed: %s', exc)
            answer = f'Here is the requested information: {raw_data}'

        return {
            'answer': answer,
            'action': {'type': action_type, 'filters': filters},
        }

    def _trace_chat(self, user, query, mode, engine, classifier_decision, result, latency_ms):
        """Log chat query to audit system and Langfuse."""
        trace_data = {
            'query': query,
            'mode': mode,
            'engine': engine,
            'classifier_decision': classifier_decision,
            'answer_length': len(result.get('answer', '')),
            'latency_ms': latency_ms,
        }

        def _write_audit():
            try:
                AuditLog.objects.create(
                    user=user,
                    event='AI_CHAT_QUERY',
                    data_snapshot=trace_data,
                )
            except Exception as exc:
                logger.debug('Audit log failed: %s', exc)

        threading.Thread(target=_write_audit, daemon=True).start()

        try:
            lf = _get_langfuse()
            if lf is not None:
                trace = lf.trace(
                    name='chat_query',
                    user_id=str(user.id) if user else 'anonymous',
                    metadata={
                        'mode': mode,
                        'engine': engine,
                        'classifier_decision': classifier_decision,
                        'latency_ms': latency_ms,
                        'alert_thresholds': get_langfuse_alert_thresholds(),
                    },
                )
                if classifier_decision:
                    trace.span(
                        name='intent_classification',
                        input={'query': query},
                        output={
                            'decision': classifier_decision,
                            'engine_selected': engine,
                        },
                    )
                trace.span(
                    name=f'{engine}_execution',
                    input={'query': query},
                    output={
                        'answer': result.get('answer', ''),
                        'sources': result.get('sources', []),
                        'action': result.get('action'),
                    },
                )
                lf.flush()
        except Exception as lf_err:
            logger.debug('Langfuse trace skipped: %s', lf_err)


# ---------------------------------------------------------------------------
# Streaming Chat Endpoint  — POST /api/ai/chat/stream/
# ---------------------------------------------------------------------------


class ChatStreamView(APIView):
    """
    POST /api/ai/chat/stream/
    SSE streaming endpoint. Returns tokens as the LLM generates them.
    """

    permission_classes = [IsViewerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'

    def post(self, request, *args, **kwargs):
        serializer = ChatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        query = serializer.validated_data['query']
        mode = serializer.validated_data['mode']
        conversation_id = serializer.validated_data.get('conversation_id')

        # --- Prompt injection check ---
        try:
            is_safe, matched_pattern = prompt_injection_filter(query)
        except Exception:
            logger.exception('Prompt injection filter failed')
            is_safe = False

        if not is_safe:
            return Response(
                {
                    'status': 'error',
                    'error': 'InvalidQueryError',
                    'message': 'Query contains disallowed content.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Intent classification (only for auto mode) ---
        engine = mode
        if mode == 'auto':
            from ai.llm.intent_classifier import classify_intent

            classification = classify_intent(query)
            if classification.confidence < 0.7:
                engine = 'nl_query'
            elif classification.intent == 'out_of_scope':
                engine = 'nl_query'
            else:
                engine = classification.intent

        # --- Load conversation ---
        conv_service = ConversationService()
        conversation = None
        if conversation_id:
            try:
                conversation = conv_service.get_conversation(conversation_id, request.user)
            except ValueError:
                return Response(
                    {'status': 'error', 'message': 'Conversation not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # --- History (only for RAG) ---
        history = []
        if conversation_id and engine == 'rag':
            history = conv_service.get_history_for_llm(conversation_id)

        user = request.user
        shared = {}

        def event_stream():
            """Generator that yields SSE events."""
            # Send metadata first
            metadata = {'engine': engine, 'mode': mode}
            if conversation_id:
                metadata['conversation_id'] = str(conversation_id)
            yield f'event: metadata\ndata: {_json.dumps(metadata)}\n\n'

            try:
                # Heartbeat before streaming to keep connection alive
                yield ': thinking\n\n'
                if engine == 'rag':
                    yield from self._stream_rag(query, user, history, shared)
                else:
                    yield from self._stream_nl_query(query, user, shared)
            except Exception as exc:
                logger.exception('Streaming chat failed')
                error_msg = (
                    sanitize_llm_error(exc)
                    if is_llm_quota_error(exc)
                    else 'An unexpected error occurred.'
                )
                yield f'event: error\ndata: {_json.dumps({"message": error_msg})}\n\n'
                return

            # Save to conversation after stream completes
            if conversation_id:
                full_answer = shared.get('full_answer', '')
                try:
                    is_new = conversation.messages.count() == 0
                    conv_service.save_message(
                        conversation_id=conversation_id,
                        role='user',
                        content=query,
                        mode=mode,
                    )
                    conv_service.save_message(
                        conversation_id=conversation_id,
                        role='assistant',
                        content=full_answer,
                        engine=engine,
                        mode=mode,
                    )
                    if is_new:
                        conv_service.auto_title(conversation_id, query)
                except Exception:
                    logger.exception('Failed to save conversation')

            yield 'event: done\ndata: {}\n\n'

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    def _stream_rag(self, query, user, history, shared):
        """Stream RAG pipeline response."""
        service = RAGQueryService()
        full_answer = ''

        yield ': searching documents...\n\n'
        for event in service.execute_stream(query, user=user, history=history):
            if event['type'] == 'token':
                full_answer += event['content']
                yield f'event: token\ndata: {_json.dumps({"content": event["content"]})}\n\n'
            elif event['type'] == 'done':
                done_data = {'sources': event.get('sources', [])}
                if event.get('action'):
                    done_data['action'] = event['action']
                yield f'event: done\ndata: {_json.dumps(done_data)}\n\n'

        shared['full_answer'] = full_answer

    def _stream_nl_query(self, query, user, shared):
        """Stream NL Query pipeline response (streams only the formatter step)."""
        from ai.llm.chain import call_gpt4o_formatter_stream, get_nl_chain
        from apps.inventory.views import (
            _handle_forecast_demand,
            _handle_get_inventory,
            _handle_get_low_stock,
            _handle_get_sales_report,
            _handle_get_supplier_info,
            _handle_get_top_products,
            _handle_get_total_value,
        )

        # Defense-in-depth: prompt injection check
        is_safe, matched_pattern = prompt_injection_filter(query)
        if not is_safe:
            raise ValueError('PROMPT_INJECTION_DETECTED')

        # Step B: NL chain (structured, not streamable)
        yield ': classifying query...\n\n'
        chain_instance = get_nl_chain()
        chain_result = chain_instance.run(query)
        chain_dict = chain_result.to_dict()
        action_type = chain_dict.get('action')
        filters = chain_dict.get('filters', {})

        # Step C: DB query
        handler_map = {
            'get_inventory': _handle_get_inventory,
            'get_sales_report': _handle_get_sales_report,
            'get_low_stock': _handle_get_low_stock,
            'forecast_demand': _handle_forecast_demand,
            'get_supplier_info': _handle_get_supplier_info,
            'get_total_value': _handle_get_total_value,
            'get_top_products': _handle_get_top_products,
        }
        handler = handler_map.get(action_type)
        if not handler:
            raise ValueError(f'Unknown action type: {action_type}')

        from ai.llm.schemas import NLQueryFilters

        nl_filters = NLQueryFilters(**filters) if isinstance(filters, dict) else filters
        raw_data = handler(nl_filters)

        # Step D: Stream formatter
        yield ': generating response...\n\n'
        full_answer = ''
        for chunk in call_gpt4o_formatter_stream(original_query=query, raw_data=raw_data):
            full_answer += chunk
            yield f'event: token\ndata: {_json.dumps({"content": chunk})}\n\n'

        done_data = {'action': {'type': action_type, 'filters': filters}}
        yield f'event: done\ndata: {_json.dumps(done_data)}\n\n'

        shared['full_answer'] = full_answer
