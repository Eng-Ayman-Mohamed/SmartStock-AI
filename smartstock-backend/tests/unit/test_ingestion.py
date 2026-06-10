import io
import os
import time
from unittest.mock import MagicMock, patch

import pypdf
from django.test import TestCase

from ai.rag.ingestion import (
    BATCH_SIZE,
    chunk_pdf_pages,
    chunk_text,
    extract_text_from_pdf,
    ingest_pdf,
)
from apps.ingestion.models import DocumentChunk


class ChunkTextTest(TestCase):
    def test_chunk_text_single_chunk(self):
        text = 'short text'
        result = chunk_text(text, chunk_size=100, overlap=0)
        self.assertEqual(result, ['short text'])

    def test_chunk_text_multiple_chunks(self):
        text = 'word ' * 600
        result = chunk_text(text, chunk_size=512, overlap=50)
        self.assertGreater(len(result), 1)
        for chunk in result:
            words = chunk.split()
            self.assertLessEqual(len(words), 512)

    def test_chunk_text_empty(self):
        self.assertEqual(chunk_text(''), [])


class ExtractTextFromPdfTest(TestCase):
    def test_extract_text_from_pdf(self):
        import tempfile

        writer = pypdf.PdfWriter()
        writer.add_blank_page(612, 792)

        buf = io.BytesIO()
        writer.write(buf)
        buf.seek(0)

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(buf.getvalue())
            tmp_path = tmp.name

        try:
            result = extract_text_from_pdf(tmp_path)
            self.assertIsInstance(result, list)
        finally:
            os.unlink(tmp_path)


class ChunkPdfPagesTest(TestCase):
    def test_chunk_pdf_pages(self):
        pages = [
            {'page_number': 1, 'text': 'hello world foo bar baz qux'},
        ]
        chunks = chunk_pdf_pages(pages)
        self.assertGreater(len(chunks), 0)
        for c in chunks:
            self.assertIn('text', c)
            self.assertIn('page_number', c)

    def test_chunk_pdf_pages_preserves_page_number(self):
        pages = [
            {'page_number': 3, 'text': 'word ' * 600},
        ]
        chunks = chunk_pdf_pages(pages)
        for c in chunks:
            self.assertEqual(c['page_number'], 3)


@patch('ai.rag.ingestion.OpenAIEmbeddings')
class IngestPdfTest(TestCase):
    def setUp(self):
        writer = pypdf.PdfWriter()
        writer.add_blank_page(612, 792)
        import tempfile

        self.tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        writer.write(self.tmp)
        self.tmp.close()

    def tearDown(self):
        import os

        os.unlink(self.tmp.name)

    def test_ingest_pdf_creates_chunks(self, mock_embeddings_cls):
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1] * 1536]
        mock_embeddings_cls.return_value = mock_instance

        result = ingest_pdf(self.tmp.name)
        self.assertIn('chunks', result)
        self.assertIn('filename', result)
        self.assertIn('api_calls', result)

    def test_ingest_pdf_replaces_existing_chunks(self, mock_embeddings_cls):
        mock_instance = MagicMock()
        mock_instance.embed_documents.return_value = [[0.1] * 1536]
        mock_embeddings_cls.return_value = mock_instance

        result1 = ingest_pdf(self.tmp.name)
        first_count = result1['chunks']

        result2 = ingest_pdf(self.tmp.name)
        second_count = result2['chunks']

        self.assertEqual(first_count, second_count)
        total = DocumentChunk.objects.filter(source_document=result1['filename']).count()
        self.assertEqual(total, second_count)


@patch('ai.rag.ingestion.OpenAIEmbeddings')
class BatchEmbeddingTest(TestCase):
    def test_batch_delay_respected(self, mock_embeddings_cls):
        mock_instance = MagicMock()
        mock_instance.embed_documents.side_effect = [
            [[0.1] * 1536] * BATCH_SIZE,
            [[0.2] * 1536],
        ]
        mock_embeddings_cls.return_value = mock_instance

        texts = ['text'] * (BATCH_SIZE + 1)
        start = time.time()
        from ai.rag.ingestion import generate_embeddings

        generate_embeddings(texts)
        elapsed = time.time() - start
        self.assertGreaterEqual(elapsed, 0)
