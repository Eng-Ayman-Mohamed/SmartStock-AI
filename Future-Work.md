Mawada Alexander

Is the rag system automatic?
It's not automatic — you have to run python manage.py ingest_document --file <path> manually each time.

What document types does RAG handle?
RAG handles ONLY unstructured PDF documents: supplier policies, contracts, warehouse procedures, and product specifications. Database records (products, suppliers, stock levels, sales, POs) are NOT embedded into the vector store — they are queried live via the NL Query engine which translates natural language into structured ORM queries. This is by design: DB data changes in real-time and must always be queried from the source.

How do you add new documents to the knowledge base?
Run: python manage.py ingest_document --file /path/to/document.pdf
The pipeline chunks the PDF (512 tokens, 50 overlap), generates embeddings via text-embedding-3-small, and stores them in pgvector. Re-running on the same filename replaces old chunks (delete-and-recreate).

To make ingestion automatic, you would need:
1. A file upload API endpoint + frontend UI for managers/admins
2. Django signals or a Celery task to re-ingest when source PDFs change
