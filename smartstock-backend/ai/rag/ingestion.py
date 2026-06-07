import io
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import pypdf
from django.db import transaction
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from apps.ingestion.models import DocumentChunk

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
BATCH_DELAY_SECONDS = 1
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def extract_text_from_pdf(file_path: str) -> list[dict]:
    reader = pypdf.PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text and text.strip():
            pages.append({"page_number": i, "text": text.strip()})
    return pages


def chunk_pdf_pages(pages: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=lambda t: len(t.split()),
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = []
    for page in pages:
        page_texts = splitter.split_text(page["text"])
        for t in page_texts:
            chunks.append({
                "text": t,
                "page_number": page["page_number"],
            })
    return chunks


def chunk_database_records() -> list[dict]:
    from apps.inventory.models import Product, SKU, StockLevel, Supplier as InvSupplier
    from apps.purchasing.models import PurchaseOrder

    chunks = []
    now = datetime.now(timezone.utc).isoformat()

    products = Product.objects.select_related().all()
    for product in products:
        for sku in product.skus.all():
            stock = getattr(sku, 'stock_level', None)
            reorder = stock.reorder_point if stock else "N/A"
            text = (
                f"Product: {product.name}, "
                f"SKU: {sku.code}, "
                f"Reorder Point: {reorder} units."
            )
            chunks.append({
                "text": text,
                "source_document": "product_catalogue",
                "page_number": None,
                "metadata": {
                    "doc_type": "catalogue",
                    "ingested_at": now,
                },
            })

    suppliers = InvSupplier.objects.all()
    for supplier in suppliers:
        text = (
            f"Supplier: {supplier.name}, "
            f"Email: {supplier.contact_email}, "
            f"Phone: {supplier.contact_phone or 'N/A'}, "
            f"Address: {supplier.address or 'N/A'}, "
            f"Lead Time: {supplier.default_lead_time_days} days, "
            f"Active: {supplier.is_active}"
        )
        chunks.append({
            "text": text,
            "source_document": "supplier_records",
            "page_number": None,
            "metadata": {
                "doc_type": "catalogue",
                "ingested_at": now,
            },
        })

    orders = PurchaseOrder.objects.select_related("sku__product", "supplier").all()
    for po in orders:
        text = (
            f"Purchase Order {po.id}: "
            f"SKU: {po.sku.code}, "
            f"Product: {po.sku.product.name}, "
            f"Supplier: {po.supplier.name}, "
            f"Quantity: {po.quantity}, "
            f"Status: {po.status}"
        )
        chunks.append({
            "text": text,
            "source_document": "purchase_orders",
            "page_number": None,
            "metadata": {
                "doc_type": "catalogue",
                "ingested_at": now,
            },
        })

    return chunks


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        chunk_size=BATCH_SIZE,
    )
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_embeddings = embeddings.embed_documents(batch)
        all_embeddings.extend(batch_embeddings)
        if i + BATCH_SIZE < len(texts):
            time.sleep(BATCH_DELAY_SECONDS)
    return all_embeddings


def delete_existing_chunks(source_document: str):
    deleted, _ = DocumentChunk.objects.filter(source_document=source_document).delete()
    if deleted:
        logger.info("Deleted %s existing chunk(s) for '%s'", deleted, source_document)
    return deleted


def ingest_pdf(file_path: str) -> dict:
    filename = file_path.rsplit("/", 1)[-1]
    pages = extract_text_from_pdf(file_path)
    raw_chunks = chunk_pdf_pages(pages)
    total_pages = len(pages)

    texts = [c["text"] for c in raw_chunks]
    embeddings = generate_embeddings(texts)

    now = datetime.now(timezone.utc).isoformat()
    with transaction.atomic():
        delete_existing_chunks(filename)
        bulk = []
        for chunk_data, embedding in zip(raw_chunks, embeddings):
            bulk.append(DocumentChunk(
                chunk_text=chunk_data["text"],
                embedding=embedding,
                source_document=filename,
                page_number=chunk_data["page_number"],
                metadata={
                    "doc_type": "pdf",
                    "ingested_at": now,
                },
            ))
        DocumentChunk.objects.bulk_create(bulk)

    return {
        "filename": filename,
        "pages": total_pages,
        "chunks": len(raw_chunks),
        "api_calls": (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE,
    }


def ingest_database_records() -> dict:
    raw_chunks = chunk_database_records()
    if not raw_chunks:
        return {"chunks": 0, "api_calls": 0}

    texts = [c["text"] for c in raw_chunks]
    embeddings = generate_embeddings(texts)

    with transaction.atomic():
        for chunk_data, embedding in zip(raw_chunks, embeddings):
            DocumentChunk.objects.create(
                chunk_text=chunk_data["text"],
                embedding=embedding,
                source_document=chunk_data["source_document"],
                page_number=chunk_data["page_number"],
                metadata=chunk_data["metadata"],
            )

    return {
        "chunks": len(raw_chunks),
        "api_calls": (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE,
    }


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=lambda t: len(t.split()),
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_text(text)
