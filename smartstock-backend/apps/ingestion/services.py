import base64
import logging
import os
import time

from django.core.exceptions import ValidationError
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from openai import APITimeoutError

from ai.llm.output_validator import validate_response_safety
from ai.multimodal.vision import VisionExtractor
from ai.observability.langfuse import invoke_with_langfuse
from ai.rag.ingestion import ingest_pdf
from apps.audit.models import AuditEvent
from apps.audit.utils import log_ai_action
from apps.inventory.services import InventoryService

from .models import Document, DocumentChunk
from .repositories import InvoiceScanRepository

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'text/csv': 'csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'text/plain': 'txt',
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

INVOICE_REQUIRED_FIELDS = [
    'product_name',
    'sku_code',
    'quantity_received',
    'unit_price',
    'supplier_name',
]

# Required fields for the structured (multi-line) invoice path.
INVOICE_HEADER_REQUIRED = ['supplier_name']
LINE_ITEM_REQUIRED = ['item_name', 'sku_code', 'quantity']

# Header fields stored alongside the legacy mirror fields in extracted_data.
INVOICE_HEADER_FIELDS = [
    'supplier_name',
    'invoice_number',
    'invoice_date',
    'due_date',
    'invoice_total',
    'tax_amount',
    'currency',
]


class InvoiceExtractionMalformed(Exception):
    pass


class InvoiceExtractionTimeout(Exception):
    pass


class InvoiceAlreadyConfirmed(Exception):
    pass


class InvoiceScanService:
    def __init__(self, repo=None, extractor=None, inventory_service=None, audit_logger=None):
        self.repo = repo or InvoiceScanRepository()
        self.extractor = extractor or VisionExtractor()
        self.inventory_service = inventory_service or InventoryService()
        self.audit_logger = audit_logger or log_ai_action

    def scan_invoice(self, file, user) -> dict:
        raw = file.read()
        file.seek(0)
        scan = self.repo.create(
            {
                'uploaded_by': user,
                'original_filename': getattr(file, 'name', 'invoice'),
                'content_type': getattr(file, 'content_type', '') or 'application/octet-stream',
                'file_size': len(raw),
            }
        )
        file_data_url = self._to_data_url(raw, scan.content_type)

        try:
            extracted = self.extractor.extract(file_data_url)
        except (TimeoutError, APITimeoutError) as exc:
            self._mark_failed(scan, user, 'timeout', str(exc))
            raise InvoiceExtractionTimeout(
                'Invoice processing timed out. Please try again or enter the data manually.'
            )
        except ValueError as exc:
            self._mark_failed(scan, user, 'malformed_json', str(exc))
            raise InvoiceExtractionMalformed(str(exc))
        except Exception as exc:
            from core.exceptions import LLMQuotaExhaustedError, is_llm_quota_error

            if is_llm_quota_error(exc):
                self._mark_failed(scan, user, 'quota_exhausted', str(exc))
                raise LLMQuotaExhaustedError(
                    'AI service quota has been reached. Please try again shortly or contact your admin.'
                ) from exc
            raise

        if not isinstance(extracted, dict):
            self._mark_failed(
                scan, user, 'malformed_json', 'Vision response was not a JSON object.'
            )
            raise InvoiceExtractionMalformed('Vision response was not a JSON object.')

        extracted_data, confidence = self._normalize_extraction(extracted)
        missing_fields = [
            field for field in INVOICE_REQUIRED_FIELDS if not extracted_data.get(field)
        ]
        status_value = 'partial' if missing_fields else 'extracted'
        scan = self.repo.update(
            scan.id,
            {
                'status': status_value,
                'extracted_data': extracted_data,
                'confidence': confidence,
                'missing_fields': missing_fields,
                'failure_reason': 'missing required fields' if missing_fields else '',
            },
        )

        if missing_fields:
            self._audit_failure(
                user=user,
                scan=scan,
                reason='partial_extraction',
                details={'missing_fields': missing_fields, 'extracted_data': extracted_data},
            )

        return self._scan_payload(scan)

    def confirm_scan(self, scan_id: int, user, confirmed_data: dict) -> dict:
        scan = self.repo.get_by_id(scan_id)
        self._validate_scan_owner(scan, user)
        if scan.is_confirmed or scan.status == 'confirmed':
            raise InvoiceAlreadyConfirmed('Invoice scan has already been confirmed.')
        if scan.status == 'rejected':
            raise ValidationError('Rejected invoice scans cannot be confirmed.')

        line_items = confirmed_data.get('line_items')
        if isinstance(line_items, list) and line_items:
            return self._confirm_multi_line(scan, user, confirmed_data, line_items)

        missing = [field for field in INVOICE_REQUIRED_FIELDS if not confirmed_data.get(field)]
        if missing:
            raise ValidationError(f'Missing confirmed invoice fields: {", ".join(missing)}')

        inventory_result = self.inventory_service.apply_confirmed_invoice(confirmed_data, user=user)
        final_data = dict(confirmed_data)
        final_data['inventory_result'] = inventory_result
        scan = self.repo.mark_confirmed(scan.id, final_data)

        changed_fields = {
            field: {
                'original': scan.extracted_data.get(field),
                'confirmed': confirmed_data.get(field),
            }
            for field in INVOICE_REQUIRED_FIELDS
            if scan.extracted_data.get(field) != confirmed_data.get(field)
        }
        self.audit_logger(
            AuditEvent.INVOICE_CONFIRMED,
            user,
            entity_type='InvoiceScan',
            entity_id=scan.id,
            data={
                'original': scan.extracted_data,
                'confirmed': confirmed_data,
                'changed_fields': changed_fields,
                'inventory_result': inventory_result,
            },
        )
        payload = self._scan_payload(scan)
        payload['inventory_result'] = inventory_result
        return payload

    def _confirm_multi_line(self, scan, user, confirmed_data: dict, line_items: list) -> dict:
        for field in INVOICE_HEADER_REQUIRED:
            if not confirmed_data.get(field):
                raise ValidationError(f'Missing confirmed invoice fields: {field}')

        valid_lines = []
        for index, line in enumerate(line_items, start=1):
            if not isinstance(line, dict):
                raise ValidationError(f'Line item {index} is invalid.')
            missing = [field for field in LINE_ITEM_REQUIRED if not line.get(field)]
            if missing:
                raise ValidationError(f'Line item {index} is missing: {", ".join(missing)}')
            valid_lines.append(line)

        inventory_result = self.inventory_service.apply_confirmed_invoice_lines(
            confirmed_data, valid_lines, user=user
        )
        final_data = dict(confirmed_data)
        final_data['inventory_result'] = inventory_result
        original_data = scan.extracted_data
        scan = self.repo.mark_confirmed(scan.id, final_data)

        changed_fields = {
            field: {
                'original': original_data.get(field),
                'confirmed': confirmed_data.get(field),
            }
            for field in INVOICE_HEADER_FIELDS
            if original_data.get(field) != confirmed_data.get(field)
        }
        self.audit_logger(
            AuditEvent.INVOICE_CONFIRMED,
            user,
            entity_type='InvoiceScan',
            entity_id=scan.id,
            data={
                'original': original_data,
                'confirmed': confirmed_data,
                'changed_fields': changed_fields,
                'line_count': len(valid_lines),
                'inventory_result': inventory_result,
            },
        )
        payload = self._scan_payload(scan)
        payload['inventory_result'] = inventory_result
        return payload

    def reject_scan(self, scan_id: int, user) -> dict:
        scan = self.repo.get_by_id(scan_id)
        self._validate_scan_owner(scan, user)
        if scan.is_confirmed or scan.status == 'confirmed':
            raise InvoiceAlreadyConfirmed('Confirmed invoice scans cannot be rejected.')
        scan = self.repo.mark_rejected(scan.id)
        self.audit_logger(
            AuditEvent.INVOICE_REJECTED,
            user,
            entity_type='InvoiceScan',
            entity_id=scan.id,
            data={'extracted_data': scan.extracted_data},
        )
        return self._scan_payload(scan)

    def _to_data_url(self, raw: bytes, content_type: str) -> str:
        encoded = base64.b64encode(raw).decode('ascii')
        return f'data:{content_type};base64,{encoded}'

    def _normalize_extraction(self, extracted: dict) -> tuple[dict, dict]:
        from ai.llm.invoice_schema import InvoiceExtraction

        extraction = InvoiceExtraction.from_vision_json(extracted)
        header = extraction.header.model_dump()
        line_items = [item.model_dump() for item in extraction.line_items]
        raw_confidence = extraction.confidence or {}

        first = line_items[0] if line_items else {}
        data = {
            # Invoice-level header fields.
            'supplier_name': header.get('supplier_name'),
            'invoice_number': header.get('invoice_number'),
            'invoice_date': header.get('invoice_date'),
            'due_date': header.get('due_date'),
            'invoice_total': header.get('invoice_total'),
            'tax_amount': header.get('tax_amount'),
            'currency': header.get('currency'),
            # Structured line items.
            'line_items': line_items,
            # Legacy mirror fields (keep missing-field detection + confirm path stable).
            'product_name': first.get('item_name'),
            'sku_code': first.get('sku_code'),
            'quantity_received': first.get('quantity'),
            'unit_price': first.get('unit_price'),
        }

        confidence_keys = INVOICE_HEADER_FIELDS + [
            'product_name',
            'sku_code',
            'quantity_received',
            'unit_price',
            'line_items',
        ]
        confidence = {
            key: self._normalize_confidence(raw_confidence.get(key)) for key in confidence_keys
        }
        return data, confidence

    def _normalize_confidence(self, value) -> float:
        if value is None:
            return 0.0
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0
        if value > 1:
            value = value / 100
        return max(0.0, min(value, 1.0))

    def _validate_scan_owner(self, scan, user):
        if scan.uploaded_by_id != user.id:
            raise PermissionError('You cannot access another user invoice scan.')

    def _mark_failed(self, scan, user, reason: str, detail: str):
        scan = self.repo.update(
            scan.id,
            {
                'status': 'failed',
                'failure_reason': detail,
                'missing_fields': INVOICE_REQUIRED_FIELDS,
            },
        )
        self._audit_failure(user=user, scan=scan, reason=reason, details={'detail': detail})

    def _audit_failure(self, user, scan, reason: str, details: dict):
        self.audit_logger(
            AuditEvent.VISION_EXTRACTION_FAILED,
            user,
            entity_type='InvoiceScan',
            entity_id=scan.id if scan else None,
            data={'reason': reason, **details},
        )

    def _scan_payload(self, scan) -> dict:
        return {
            'scan_id': scan.id,
            'status': scan.status,
            'extracted_data': scan.extracted_data,
            'confidence': scan.confidence,
            'missing_fields': scan.missing_fields,
            'failure_reason': scan.failure_reason,
            'confirmed_data': scan.confirmed_data,
            'is_confirmed': scan.is_confirmed,
        }


class IngestionService:
    def upload_document(self, file, user, doc_type=None):
        raw = file.read()
        file.seek(0)

        try:
            import magic

            mime_type = magic.from_buffer(raw[:2048], mime=True)
        except ImportError:
            mime_type = getattr(file, 'content_type', '') or ''
        detected_type = ALLOWED_MIME_TYPES.get(mime_type)
        if not detected_type:
            raise ValueError(f'Unsupported file type: {mime_type}')

        if len(raw) > MAX_FILE_SIZE:
            raise ValueError('File size exceeds 10MB limit.')

        actual_doc_type = doc_type or detected_type
        if doc_type and doc_type != detected_type:
            actual_doc_type = detected_type

        try:
            import cloudinary.uploader

            upload_result = cloudinary.uploader.upload(
                file, resource_type='raw', folder='smartstock_documents'
            )
            cloudinary_url = upload_result.get('secure_url', '')
        except Exception as e:
            logger.warning('Cloudinary upload failed: %s', e)
            cloudinary_url = ''

        original_filename = getattr(file, 'original_filename', None) or getattr(
            file, 'name', 'untitled'
        )
        filename = f'{user.id}_{original_filename}' if user else original_filename

        document = Document.objects.create(
            filename=filename,
            original_filename=original_filename,
            doc_type=actual_doc_type,
            file_size=len(raw),
            uploaded_by=user,
            cloudinary_url=cloudinary_url,
        )

        if actual_doc_type == 'pdf':
            tmp_path = None
            try:
                import tempfile

                file.seek(0)
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    for chunk in file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name
                result = ingest_pdf(tmp_path, document_id=document.id)
                document.total_chunks = result['chunks']
                document.save(update_fields=['total_chunks'])
            except Exception as e:
                logger.exception('PDF ingestion failed for document %s: %s', document.id, e)
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        return document

    def get_document(self, document_id):
        try:
            return Document.objects.get(pk=document_id)
        except Document.DoesNotExist:
            return None

    def list_documents(self):
        return Document.objects.filter(is_active=True).order_by('-ingested_at')

    def soft_delete_document(self, document_id):
        try:
            document = Document.objects.get(pk=document_id)
            document.is_active = False
            document.save(update_fields=['is_active'])
            DocumentChunk.objects.filter(document=document).update(metadata={'deactivated': True})
            return True
        except Document.DoesNotExist:
            return False


class RAGQueryService:
    """
    Thin orchestrator for the RAG pipeline.

    Pipeline order:
        1. Hybrid search (dense + FTS) with query embedding
        2. Cohere reranking → top 3 chunks
        3. Build context from top chunks
        4. Call LLM with RAG system prompt
        5. Post-process citations
        6. Return answer + sources
    """

    RAG_SYSTEM_PROMPT = (
        'You are SmartStock AI, a warehouse inventory assistant.\n\n'
        'CRITICAL CONSTRAINT — STRICTLY CONTEXT-ONLY:\n'
        'You MUST answer SOLELY based on the information in the Context below.\n'
        '• If the Context contains a clear, direct answer → provide it and cite the source.\n'
        '• If the Context mentions the topic but does NOT contain enough detail to answer '
        'the specific question → say: "The provided documents do not contain enough '
        'information to answer this question."\n'
        '• If the Context does not mention the topic at all → say: "I cannot find '
        'this information in the provided records."\n\n'
        'WHAT YOU MUST NEVER DO:\n'
        '• Never use your own general knowledge to answer — even if you know the answer.\n'
        '• Never elaborate, explain, or supplement the context with external information.\n'
        '• Never answer a question that the context does not explicitly support.\n\n'
        'WHEN CITING:\n'
        'Use the format: [Source: <document>, Page: <page>]\n\n'
        'Context:\n{context}'
    )

    def __init__(self):
        self._llm = None
        self._embeddings = None
        self._last_token_usage = {}

    def _get_llm(self):
        if self._llm is None:
            from ai.llm.provider_config import get_chat_llm

            self._llm = get_chat_llm()
        return self._llm

    def _get_embeddings(self):
        if self._embeddings is None:
            from ai.llm.provider_config import get_embeddings

            self._embeddings = get_embeddings()
        return self._embeddings

    def embed_query(self, query: str) -> list[float]:
        embeddings = self._get_embeddings()
        return embeddings.embed_query(query)

    def hybrid_search(self, query: str, top_k: int = 10) -> list[dict]:
        from ai.rag.retrieval import hybrid_search

        return hybrid_search(query, top_k=top_k)

    def rerank(self, query: str, chunks: list[dict], top_n: int = 3) -> list[dict]:
        if not chunks:
            return []

        cohere_key = os.getenv('COHERE_API_KEY')
        if not cohere_key:
            raise ConnectionError('COHERE_API_KEY is not set. Cohere reranking unavailable.')

        import cohere

        co = cohere.Client(cohere_key)
        documents = [c.get('content', '') for c in chunks]

        last_error = None
        for attempt in range(3):
            try:
                response = co.rerank(
                    query=query,
                    documents=documents,
                    top_n=top_n,
                    model='rerank-english-v3.0',
                )
                break
            except cohere.errors.TooManyRequestsError:
                wait = min(2 ** (attempt + 2), 30)
                logger.warning(
                    'Cohere rerank rate-limited (attempt %d), retrying in %ds...',
                    attempt + 1,
                    wait,
                )
                time.sleep(wait)
                last_error = ConnectionError('Cohere rate limit exceeded')
            except Exception as e:
                last_error = e
                if attempt < 2:
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        'Cohere rerank attempt %d failed (%s), retrying in %ds...',
                        attempt + 1,
                        e,
                        wait,
                    )
                    time.sleep(wait)
        else:
            raise last_error

        reranked = []
        for result in response.results:
            chunk = chunks[result.index].copy()
            chunk['rerank_score'] = result.relevance_score
            reranked.append(chunk)
        return reranked

    def build_context(self, chunks: list[dict]) -> str:
        parts = []
        for chunk in chunks:
            doc = chunk.get('source_document', 'unknown')
            page = chunk.get('page_number', '?')
            text = chunk.get('content', '')
            parts.append(f'[Source: {doc}, Page: {page}]\n{text}')
        return '\n\n---\n\n'.join(parts)

    def call_llm(self, query: str, context: str, history: list | None = None) -> str:
        answer, token_usage = self.call_llm_with_usage(query, context, history)
        self._last_token_usage = token_usage
        return answer

    def call_llm_with_usage(
        self, query: str, context: str, history: list | None = None
    ) -> tuple[str, dict]:
        llm = self._get_llm()

        messages = [
            ('system', self.RAG_SYSTEM_PROMPT),
        ]

        if history:
            for m in history[-10:]:
                role = m.get('role', 'user')
                content = m.get('content', '')
                if role in ('user', 'assistant'):
                    messages.append((role, content))

        messages.append(('user', '{query}'))

        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm
        response, token_usage = invoke_with_langfuse(
            chain,
            {'context': context, 'query': query},
            include_token_usage=True,
        )
        answer = StrOutputParser().invoke(response).strip()
        if not validate_response_safety(answer):
            logger.warning('RAGQueryService call_llm output blocked by response safety validator')
            answer = "I'm sorry, I cannot provide that information."
        return answer, token_usage

    def call_llm_stream(self, query: str, context: str, history: list | None = None):
        """Streaming version of call_llm. Yields text chunks."""
        llm = self._get_llm()

        messages = [
            ('system', self.RAG_SYSTEM_PROMPT),
        ]

        if history:
            for m in history[-10:]:
                role = m.get('role', 'user')
                content = m.get('content', '')
                if role in ('user', 'assistant'):
                    messages.append((role, content))

        messages.append(('user', '{query}'))

        prompt = ChatPromptTemplate.from_messages(messages)
        chain = prompt | llm | StrOutputParser()
        try:
            for chunk in chain.stream({'context': context, 'query': query}):
                if chunk:
                    yield chunk
        except Exception as exc:
            logger.warning('RAGQueryService call_llm_stream failed: %s', exc)
            yield "I'm sorry, I cannot provide that information."

    def extract_sources(self, chunks: list[dict]) -> list[dict]:
        seen = set()
        sources = []
        for chunk in chunks:
            doc = chunk.get('source_document', '')
            page = chunk.get('page_number')
            key = (doc, page)
            if key not in seen and doc:
                seen.add(key)
                sources.append(
                    {
                        'document': doc,
                        'page': page,
                        'document_id': chunk.get('document_id'),
                        'chunk_text': chunk.get('chunk_text', chunk.get('content', '')),
                    }
                )
        return sources

    def execute(self, query: str, user=None, history: list | None = None) -> dict:
        start = time.time()

        # Step 1: Hybrid search (embeds query + dense + sparse search)
        search_results = self.hybrid_search(query, top_k=10)

        # Step 2: Rerank to top 5 chunks (broader context)
        try:
            top_chunks = self.rerank(query, search_results, top_n=5)
        except ConnectionError:
            logger.warning('Cohere unavailable — falling back to vector-score ranking')
            top_chunks = sorted(search_results, key=lambda c: c.get('score', 0), reverse=True)[:5]

        # Step 3: If no relevant chunks found, return explicit no-answer
        # Use rerank_score when available (Cohere), fall back to original score
        # Threshold 0.05: rerank scores for partially-matching chunks can be low but still useful.
        # The LLM decides final relevance — we just filter out complete noise.
        if not top_chunks or all(
            c.get('rerank_score', c.get('score', 0)) < 0.05 for c in top_chunks
        ):
            latency_ms = round((time.time() - start) * 1000)
            return {
                'answer': 'I cannot find this information in the provided records.',
                'sources': [],
                'latency_ms': latency_ms,
                'chunks_retrieved': len(search_results),
                'chunks_reranked': len(top_chunks),
                'retrieved_chunks': [
                    {
                        'content': c.get('content', '')[:200],
                        'source_document': c.get('source_document', ''),
                        'page_number': c.get('page_number'),
                        'score': c.get('score', 0),
                        'rerank_score': c.get('rerank_score'),
                    }
                    for c in top_chunks
                ],
                'token_usage': {},
            }

        # Step 4: Build context and call LLM
        context = self.build_context(top_chunks)
        self._last_token_usage = {}
        llm_response = self.call_llm(query, context, history)
        token_usage = self._last_token_usage

        # Step 5: Post-process citations
        from ai.rag.citation import inject_citations

        sources = self.extract_sources(top_chunks)
        llm_response = inject_citations(llm_response, sources)

        latency_ms = round((time.time() - start) * 1000)
        return {
            'answer': llm_response,
            'sources': sources,
            'latency_ms': latency_ms,
            'chunks_retrieved': len(search_results),
            'chunks_reranked': len(top_chunks),
            'retrieved_chunks': [
                {
                    'content': c.get('content', '')[:200],
                    'source_document': c.get('source_document', ''),
                    'page_number': c.get('page_number'),
                    'score': c.get('score', 0),
                    'rerank_score': c.get('rerank_score'),
                }
                for c in top_chunks
            ],
            'token_usage': token_usage,
        }

    def execute_stream(self, query: str, user=None, history: list | None = None):
        """Streaming version of execute. Yields {'type': 'metadata'|'token'|'done'|'error', ...}."""
        start = time.time()

        # Step 1: Hybrid search
        search_results = self.hybrid_search(query, top_k=10)

        # Step 2: Rerank to top 5 chunks
        try:
            top_chunks = self.rerank(query, search_results, top_n=5)
        except ConnectionError:
            logger.warning('Cohere unavailable — falling back to vector-score ranking')
            top_chunks = sorted(search_results, key=lambda c: c.get('score', 0), reverse=True)[:5]

        # Step 3: If no relevant chunks found
        if not top_chunks or all(
            c.get('rerank_score', c.get('score', 0)) < 0.05 for c in top_chunks
        ):
            yield {
                'type': 'token',
                'content': 'I cannot find this information in the provided records.',
            }
            yield {'type': 'done', 'sources': [], 'action': None}
            return

        # Step 4: Build context
        context = self.build_context(top_chunks)
        sources = self.extract_sources(top_chunks)

        # Step 5: Stream LLM answer
        full_answer = ''
        for chunk in self.call_llm_stream(query, context, history):
            full_answer += chunk
            yield {'type': 'token', 'content': chunk}

        # Step 6: Post-process citations
        from ai.rag.citation import inject_citations

        final_answer = inject_citations(full_answer, sources)
        # Yield the corrected answer if citations changed the text
        if final_answer != full_answer:
            yield {'type': 'token', 'content': final_answer[len(full_answer) :]}

        latency_ms = round((time.time() - start) * 1000)
        yield {
            'type': 'done',
            'sources': sources,
            'action': None,
            'latency_ms': latency_ms,
        }
