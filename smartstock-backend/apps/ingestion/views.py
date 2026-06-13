import logging
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

import cloudinary.uploader
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ai.llm.chain import prompt_injection_filter
from ai.observability.langfuse import get_langfuse_alert_thresholds, get_langfuse_client
from ai.rag.ingestion import ingest_pdf
from apps.audit.models import AuditLog
from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer, ValidationErrorResponseSerializer

from .models import Document
from .serializers import (
    ChatSerializer,
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
        except Exception as e:
            logger.exception('Transcription failed')
            return Response(
                {'status': 'error', 'message': f'Transcription failed: {e}'},
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
            return Response(
                {
                    'status': 'error',
                    'error': 'InvoiceExtractionMalformed',
                    'message': str(exc),
                    'code': status.HTTP_422_UNPROCESSABLE_ENTITY,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
        return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Unified Chat Endpoint  — POST /api/ai/chat/
#   mode=auto → GPT-4o-mini classifies query → nl or rag
#   mode=nl   → NL Query engine (live inventory data)
#   mode=rag  → RAG engine (document search)
# ---------------------------------------------------------------------------


class ChatView(APIView):
    permission_classes = [IsManagerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'
    CHAT_TIMEOUT_SECONDS = 10

    @extend_schema(
        request=ChatSerializer,
        responses={
            200: inline_serializer(
                'ChatResponse',
                {
                    'status': serializers.CharField(),
                    'data': inline_serializer(
                        'ChatResponseData',
                        {
                            'engine': serializers.CharField(),
                            'mode': serializers.CharField(),
                            'answer': serializers.CharField(),
                            'action': serializers.DictField(required=False, allow_null=True),
                            'sources': serializers.ListField(
                                child=serializers.DictField(), required=False, allow_null=True
                            ),
                        },
                    ),
                },
            ),
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Bad request'),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description='Validation error'
            ),
            504: OpenApiResponse(response=ErrorResponseSerializer, description='Gateway timeout'),
        },
        examples=[
            OpenApiExample(
                'Chat Request (auto)',
                value={'query': 'How many Widget-001 do we have?', 'mode': 'auto'},
                request_only=True,
            ),
            OpenApiExample(
                'Chat Response',
                value={
                    'status': 'success',
                    'data': {
                        'engine': 'nlquery',
                        'mode': 'data',
                        'answer': 'You have 45 units of Widget-001 in stock.',
                        'action': {'type': 'get_inventory', 'filters': {}},
                        'sources': None,
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
        mode = serializer.validated_data.get('mode', 'auto')

        # --- Prompt injection check ---
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
                {
                    'status': 'error',
                    'error': 'InvalidQueryError',
                    'message': 'Query contains disallowed content.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Determine engine ---
        engine = mode
        if mode == 'auto':
            engine = self._classify_intent(query)

        # --- Execute pipeline with timeout ---
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_pipeline, query, engine, request.user)
                result = future.result(timeout=self.CHAT_TIMEOUT_SECONDS)
        except FuturesTimeout:
            return Response(
                {'status': 'error', 'message': 'Request timed out. Please try a simpler question.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            logger.exception('Chat pipeline failed')
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                'status': 'success',
                'data': {
                    'engine': f'{engine}query',
                    'mode': mode,
                    'answer': result['answer'],
                    'action': result.get('action'),
                    'sources': result.get('sources'),
                },
            },
            status=status.HTTP_200_OK,
        )

    def _classify_intent(self, query: str) -> str:
        """Use GPT-4o-mini to classify query as 'nl' or 'rag'."""
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model='gpt-4o-mini',
            temperature=0,
            api_key=os.environ.get('OPENAI_API_KEY'),
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    'system',
                    'Classify this inventory management query as either:\n'
                    '- "nl" if it asks about live inventory data (stock, sales, '
                    'forecasts, suppliers, products, POs, reorder)\n'
                    '- "rag" if it asks about documents, policies, procedures, '
                    'uploaded files, contracts, or specifications\n'
                    'Respond with exactly one word: nl or rag.',
                ),
                ('user', query),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        try:
            result = chain.invoke({}).strip().lower()
            return 'nl' if result.startswith('nl') else 'rag'
        except Exception:
            logger.warning('Intent classification failed, defaulting to nl')
            return 'nl'

    def _run_pipeline(self, query: str, engine: str, user):
        if engine == 'rag':
            return self._run_rag_pipeline(query, user)
        return self._run_nl_pipeline(query, user)

    def _run_rag_pipeline(self, query: str, user) -> dict:
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

        latency_ms = round((time.time() - pipeline_start) * 1000)
        self._trace_query(user, query, 'rag', latency_ms)

        return {
            'answer': result['answer'],
            'sources': result['sources'],
            'action': None,
        }

    def _run_nl_pipeline(self, query: str, user) -> dict:
        from apps.inventory.views import (
            _handler_map,
            get_nl_chain,
            get_langfuse,
        )
        from ai.llm.chain import call_gpt4o_formatter

        pipeline_start = time.time()

        # Step 1: Run NL chain
        try:
            chain_instance = get_nl_chain()
            chain_result = chain_instance.run(query)
            chain_dict = chain_result.to_dict()
            action_type = chain_dict.get('action')
            filters = chain_dict.get('filters', {})
        except Exception as e:
            raise ValueError(f'Chain processing failed: {e}')

        # Step 2: Dispatch to handler
        handler = _handler_map.get(action_type)
        if handler is None:
            raise ValueError(f'Unknown action type: {action_type}')

        try:
            raw_data = handler(filters)
        except Exception as e:
            raise ValueError(f'Database execution error: {e}')

        # Step 3: Format natural language response
        try:
            answer = call_gpt4o_formatter(original_query=query, raw_data=raw_data)
        except Exception as e:
            raise ValueError(f'Formatting failed: {e}')

        # Step 4: Tracing
        latency_ms = round((time.time() - pipeline_start) * 1000)
        self._trace_query(user, query, 'nl', latency_ms, action_type, filters)

        AuditLog.objects.create(
            user=user,
            event='AI_NL_QUERY',
            data_snapshot={
                'query': query,
                'action': action_type,
                'response_length': len(answer),
                'pipeline_time_ms': latency_ms,
            },
        )

        return {
            'answer': answer,
            'action': {'type': action_type, 'filters': filters},
            'sources': None,
        }

    def _trace_query(
        self, user, query: str, engine: str, latency_ms: int, action=None, filters=None
    ):
        from apps.inventory.views import get_langfuse

        trace_data = {
            'query': query,
            'engine': engine,
            'latency_ms': latency_ms,
            'action': action,
            'filters': filters,
        }
        try:
            AuditLog.objects.create(
                user=user,
                event='AI_CHAT',
                data_snapshot=trace_data,
            )
        except Exception:
            pass

        try:
            lf = get_langfuse()
            if lf is not None:
                trace = lf.trace(
                    name='chat',
                    user_id=str(user.id) if user else 'anonymous',
                    metadata={'engine': engine, 'latency_ms': latency_ms},
                )
                trace.span(
                    name='pipeline',
                    input={'query': query, 'action': action},
                    output={'latency_ms': latency_ms},
                )
                lf.flush()
        except Exception:
            pass
