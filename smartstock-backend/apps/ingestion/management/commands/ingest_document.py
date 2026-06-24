import os
import time

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from ai.rag.ingestion import ingest_pdf
from apps.ingestion.models import Document


class Command(BaseCommand):
    help = 'Ingest a PDF document into the RAG knowledge base'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to a PDF file to ingest',
        )

    def handle(self, *args, **options):
        start = time.time()
        file_path = options['file']
        filename = os.path.basename(file_path)

        self.stdout.write(f'Ingesting PDF: {file_path} ...')
        try:
            file_size = os.path.getsize(file_path)
        except OSError as e:
            raise CommandError(f'Cannot read file: {e}')

        doc = Document.objects.create(
            filename=filename,
            original_filename=filename,
            doc_type='specification',
            file_size=file_size,
            cloudinary_url='',
            ingested_at=timezone.now(),
        )

        try:
            result = ingest_pdf(file_path, document_id=doc.id)
        except Exception as e:
            doc.delete()
            raise CommandError(f'Ingestion failed: {e}')

        doc.total_chunks = result['chunks']
        doc.save(update_fields=['total_chunks'])

        self.stdout.write(
            self.style.SUCCESS(
                f'Processed: {result["filename"]}\n'
                f'  Document ID:  {doc.id}\n'
                f'  Pages:        {result["pages"]}\n'
                f'  Chunks:       {result["chunks"]}\n'
                f'  API calls:    {result["api_calls"]}\n'
                f'  Total time:   {time.time() - start:.2f}s'
            )
        )
