from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.ingestion.serializers import (
    ChatSerializer,
    DocumentChunkSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    InvoiceScanConfirmSerializer,
    InvoiceScanUploadSerializer,
    RAGQuerySerializer,
    TranscriptionSerializer,
)


class DocumentUploadSerializerTest(TestCase):
    def _make_pdf(self, content=b'%PDF-1.4 fake content'):
        return SimpleUploadedFile('test.pdf', content, content_type='application/pdf')

    def test_valid_pdf(self):
        s = DocumentUploadSerializer()
        file = self._make_pdf(b'%PDF-1.4 some valid pdf bytes here')
        result = s.validate_file(file)
        self.assertEqual(result.name, 'test.pdf')

    def test_non_pdf_rejected(self):
        s = DocumentUploadSerializer()
        file = SimpleUploadedFile('test.txt', b'not a pdf', content_type='text/plain')
        with self.assertRaises(ValidationError):
            s.validate_file(file)

    def test_bad_magic_bytes(self):
        s = DocumentUploadSerializer()
        file = SimpleUploadedFile('test.pdf', b'NOTPDF at all', content_type='application/pdf')
        with self.assertRaises(ValidationError):
            s.validate_file(file)

    def test_oversized_file(self):
        s = DocumentUploadSerializer()
        large_content = b'%PDF-1.4' + b'\x00' * (11 * 1024 * 1024)
        file = SimpleUploadedFile('big.pdf', large_content, content_type='application/pdf')
        with self.assertRaises(ValidationError):
            s.validate_file(file)

    def test_wrong_content_type_header(self):
        s = DocumentUploadSerializer()
        file = SimpleUploadedFile('test.pdf', b'%PDF-1.4 content', content_type='image/png')
        with self.assertRaises(ValidationError):
            s.validate_file(file)


class RAGQuerySerializerTest(TestCase):
    def test_valid_query(self):
        s = RAGQuerySerializer(data={'query': 'What is the stock level?'})
        self.assertTrue(s.is_valid())

    def test_short_query_rejected(self):
        s = RAGQuerySerializer(data={'query': 'ab'})
        self.assertFalse(s.is_valid())

    def test_strips_whitespace(self):
        s = RAGQuerySerializer(data={'query': '  What is stock?  '})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data['query'], 'What is stock?')

    def test_missing_query(self):
        s = RAGQuerySerializer(data={})
        self.assertFalse(s.is_valid())


class ChatSerializerTest(TestCase):
    def test_valid_chat(self):
        s = ChatSerializer(data={'query': 'Show me sales data'})
        self.assertTrue(s.is_valid())

    def test_default_mode_is_auto(self):
        s = ChatSerializer(data={'query': 'test'})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data['mode'], 'auto')

    def test_custom_mode(self):
        s = ChatSerializer(data={'query': 'test', 'mode': 'rag'})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data['mode'], 'rag')

    def test_invalid_mode(self):
        s = ChatSerializer(data={'query': 'test', 'mode': 'invalid'})
        self.assertFalse(s.is_valid())

    def test_empty_query_rejected(self):
        s = ChatSerializer(data={'query': ''})
        self.assertFalse(s.is_valid())

    def test_query_too_long(self):
        s = ChatSerializer(data={'query': 'x' * 2001})
        self.assertFalse(s.is_valid())


class TranscriptionSerializerTest(TestCase):
    def test_valid_audio(self):
        audio = SimpleUploadedFile('test.mp3', b'fake audio', content_type='audio/mpeg')
        s = TranscriptionSerializer(data={'audio': audio})
        self.assertTrue(s.is_valid())

    def test_oversized_audio_rejected(self):
        large_audio = SimpleUploadedFile('big.mp3', b'\x00' * (26 * 1024 * 1024), content_type='audio/mpeg')
        s = TranscriptionSerializer(data={'audio': large_audio})
        self.assertFalse(s.is_valid())


class InvoiceScanUploadSerializerTest(TestCase):
    def test_valid_jpeg(self):
        f = SimpleUploadedFile('inv.jpg', b'\xff\xd8\xff fake', content_type='image/jpeg')
        s = InvoiceScanUploadSerializer(data={'file': f})
        self.assertTrue(s.is_valid())

    def test_valid_png(self):
        f = SimpleUploadedFile('inv.png', b'\x89PNG fake', content_type='image/png')
        s = InvoiceScanUploadSerializer(data={'file': f})
        self.assertTrue(s.is_valid())

    def test_valid_pdf(self):
        f = SimpleUploadedFile('inv.pdf', b'%PDF-1.4', content_type='application/pdf')
        s = InvoiceScanUploadSerializer(data={'file': f})
        self.assertTrue(s.is_valid())

    def test_invalid_content_type(self):
        f = SimpleUploadedFile('inv.gif', b'GIF89a', content_type='image/gif')
        s = InvoiceScanUploadSerializer(data={'file': f})
        self.assertFalse(s.is_valid())

    def test_oversized_file(self):
        f = SimpleUploadedFile('big.pdf', b'\x00' * (6 * 1024 * 1024), content_type='application/pdf')
        s = InvoiceScanUploadSerializer(data={'file': f})
        self.assertFalse(s.is_valid())


class InvoiceScanConfirmSerializerTest(TestCase):
    def test_missing_required_fields(self):
        s = InvoiceScanConfirmSerializer(data={'scan_id': 1, 'confirmed_data': {}})
        self.assertFalse(s.is_valid())

    @patch('apps.ingestion.serializers.INVOICE_REQUIRED_FIELDS', ['supplier', 'amount'])
    def test_valid_confirmed_data(self):
        s = InvoiceScanConfirmSerializer(
            data={
                'scan_id': 1,
                'confirmed_data': {'supplier': 'Acme', 'amount': 100},
            }
        )
        self.assertTrue(s.is_valid())


class DocumentChunkSerializerTest(TestCase):
    def test_fields(self):
        s = DocumentChunkSerializer()
        self.assertIn('chunk_text', s.fields)
        self.assertIn('source_document', s.fields)


class DocumentSerializerTest(TestCase):
    def test_fields(self):
        s = DocumentSerializer()
        self.assertIn('filename', s.fields)
        self.assertIn('doc_type', s.fields)
