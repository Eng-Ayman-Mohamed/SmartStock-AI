Mawada Alexander

Is the rag system automatic?
Yes — managers and admins upload PDFs through the dashboard UI via POST /api/ai/documents/upload/. The system automatically chunks, embeds, and stores them in pgvector. No CLI required.

What document types does RAG handle?
RAG handles ONLY unstructured PDF documents: supplier policies, contracts, warehouse procedures, and product specifications. Database records (products, suppliers, stock levels, sales, POs) are NOT embedded into the vector store — they are queried live via the NL Query engine which translates natural language into structured ORM queries. This is by design: DB data changes in real-time and must always be queried from the source.

How do you add new documents to the knowledge base?
1. Navigate to /dashboard/documents in the dashboard
2. Drag-and-drop a PDF or click to browse
3. Select the document type (policy, contract, procedure, specification)
4. The system uploads to Cloudinary, chunks the PDF (512 tokens, 50 overlap), generates embeddings via text-embedding-3-small, and stores chunks in pgvector
5. Re-uploading a file with the same name replaces old chunks (delete-and-recreate)

Alternative (CLI fallback):
python manage.py ingest_document --file /path/to/document.pdf

Remaining improvements:
1. Django signals or a Celery task to re-ingest when source PDFs change in Cloudinary
2. Bulk upload support (multiple PDFs at once)
3. Document versioning (keep old versions accessible)
