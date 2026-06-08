import time

from django.core.management.base import BaseCommand, CommandError

from ai.rag.ingestion import ingest_pdf


class Command(BaseCommand):
    help = "Ingest a PDF document into the RAG knowledge base"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            required=True,
            help="Path to a PDF file to ingest",
        )

    def handle(self, *args, **options):
        start = time.time()
        file_path = options["file"]

        self.stdout.write(f"Ingesting PDF: {file_path} ...")
        try:
            result = ingest_pdf(file_path)
        except Exception as e:
            raise CommandError(f"Ingestion failed: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"Processed: {result['filename']}\n"
            f"  Pages:        {result['pages']}\n"
            f"  Chunks:       {result['chunks']}\n"
            f"  API calls:    {result['api_calls']}\n"
            f"  Total time:   {time.time() - start:.2f}s"
        ))
