import time
from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from ai.rag.ingestion import ingest_database_records, ingest_pdf


class Command(BaseCommand):
    help = "Ingest a document into the RAG knowledge base"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to a PDF file to ingest",
        )

    def handle(self, *args, **options):
        start = time.time()

        if options.get("file"):
            file_path = options["file"]
            self.stdout.write(f"Ingesting PDF: {file_path} ...")
            result = ingest_pdf(file_path)
            self.stdout.write(self.style.SUCCESS(
                f"Processed: {result['filename']}\n"
                f"  Pages:        {result['pages']}\n"
                f"  Chunks:       {result['chunks']}\n"
                f"  API calls:    {result['api_calls']}\n"
                f"  Total time:   {time.time() - start:.2f}s"
            ))
        else:
            self.stdout.write("Ingesting database records ...")
            result = ingest_database_records()
            self.stdout.write(self.style.SUCCESS(
                f"Database records:\n"
                f"  Chunks:       {result['chunks']}\n"
                f"  API calls:    {result['api_calls']}\n"
                f"  Total time:   {time.time() - start:.2f}s"
            ))
