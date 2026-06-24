import logging
import os
import time
from datetime import datetime, timezone

import pypdf
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from langchain_text_splitters import RecursiveCharacterTextSplitter

from apps.ingestion.models import DocumentChunk

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
BATCH_DELAY_SECONDS = 1
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
MAX_RETRIES = 3


def extract_text_from_pdf(file_path: str) -> list[dict]:
    reader = pypdf.PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text and text.strip():
            pages.append({'page_number': i, 'text': text.strip()})
    return pages


def chunk_pdf_pages(pages: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=lambda t: len(t.split()),
        separators=['\n\n', '\n', '.', ' ', ''],
    )
    chunks = []
    for page in pages:
        page_texts = splitter.split_text(page['text'])
        for t in page_texts:
            chunks.append(
                {
                    'text': t,
                    'page_number': page['page_number'],
                }
            )
    return chunks


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    from ai.llm.provider_config import get_embeddings

    embeddings_model = get_embeddings()
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                batch_embeddings = embeddings_model.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                break
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    wait = 2**attempt
                    logger.warning(
                        'Embedding attempt %d failed (%s), retrying in %ds...',
                        attempt + 1,
                        e,
                        wait,
                    )
                    time.sleep(wait)
        else:
            raise last_error
        if i + BATCH_SIZE < len(texts):
            time.sleep(BATCH_DELAY_SECONDS)
    return all_embeddings


def delete_existing_chunks_for_document(document_id: int):
    deleted, _ = DocumentChunk.objects.filter(document_id=document_id).delete()
    if deleted:
        logger.info('Deleted %s existing chunk(s) for document_id=%s', deleted, document_id)
    return deleted


def delete_existing_chunks(source_document: str):
    deleted, _ = DocumentChunk.objects.filter(source_document=source_document).delete()
    if deleted:
        logger.info("Deleted %s existing chunk(s) for '%s'", deleted, source_document)
    return deleted


def ingest_pdf(file_path: str, document_id: int | None = None) -> dict:
    filename = os.path.basename(file_path)
    pages = extract_text_from_pdf(file_path)
    raw_chunks = chunk_pdf_pages(pages)
    total_pages = len(pages)

    if not raw_chunks:
        logger.warning('No chunks extracted from %s', filename)
        return {
            'filename': filename,
            'pages': total_pages,
            'chunks': 0,
            'api_calls': 0,
        }

    texts = [c['text'] for c in raw_chunks]
    embeddings = generate_embeddings(texts)

    if len(embeddings) != len(texts):
        raise ValueError(
            f'Embedding count mismatch: got {len(embeddings)} embeddings for {len(texts)} texts'
        )

    now = datetime.now(timezone.utc).isoformat()
    with transaction.atomic():
        if document_id:
            delete_existing_chunks_for_document(document_id)
        else:
            delete_existing_chunks(filename)

        bulk = []
        for chunk_data, embedding in zip(raw_chunks, embeddings):
            bulk.append(
                DocumentChunk(
                    chunk_text=chunk_data['text'],
                    embedding=embedding,
                    source_document=filename,
                    page_number=chunk_data['page_number'],
                    document_id=document_id,
                    metadata={
                        'doc_type': 'pdf',
                        'ingested_at': now,
                    },
                )
            )
        created = DocumentChunk.objects.bulk_create(bulk)

        chunk_ids = [c.id for c in created]
        DocumentChunk.objects.filter(id__in=chunk_ids).update(
            tsvector=SearchVector('chunk_text', config='english')
        )

    if document_id:
        actual_count = DocumentChunk.objects.filter(document_id=document_id).count()
    else:
        actual_count = DocumentChunk.objects.filter(source_document=filename).count()

    if actual_count == 0 and len(raw_chunks) > 0:
        raise RuntimeError(f'Ingestion completed but no chunks found in DB for {filename}')

    logger.info('Ingested %s: %d pages, %d chunks created', filename, total_pages, len(created))

    return {
        'filename': filename,
        'pages': total_pages,
        'chunks': len(created),
        'api_calls': (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE,
    }
