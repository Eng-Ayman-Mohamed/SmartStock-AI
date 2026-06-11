import logging

import magic

from ai.rag.ingestion import ingest_pdf

from .models import Document, DocumentChunk

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    'application/pdf': 'pdf',
    'text/csv': 'csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'text/plain': 'txt',
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class IngestionService:
    def upload_document(self, file, user, doc_type=None):
        raw = file.read()
        file.seek(0)

        mime_type = magic.from_buffer(raw[:2048], mime=True)
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

        original_filename = getattr(file, 'original_filename', None) or getattr(file, 'name', 'untitled')
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
            try:
                file.seek(0)
                chunk_count = ingest_pdf(file, document_id=document.id)
                document.total_chunks = chunk_count
                document.save(update_fields=['total_chunks'])
            except Exception as e:
                logger.exception('PDF ingestion failed for document %s: %s', document.id, e)

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
