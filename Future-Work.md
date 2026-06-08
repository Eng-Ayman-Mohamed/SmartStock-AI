Mawada Alexander

Is the rag system automatic?
It's not automatic — you have to run python manage.py ingest_document manually each time.

If theres is a change in the database for the products is it linked directly with the vector chunks?
 Changes to products/suppliers in the database are not synced to the vector chunks automatically.

 Here's what happens:
- ingest_document --file policy.pdf — creates chunks and embeddings from a PDF at that point in time. If the PDF changes, you re-run it.
- ingest_document (no file) — queries all Products, SKUs, Suppliers, POs from the DB, creates chunks, and stores them. It's a static snapshot — if you add a new product or update a supplier, the vector DB still has the old data.
To make it live, you'd need either:
1. Django signals — auto-recreate the relevant chunk when a Product/Supplier/PO is saved or deleted
2. A periodic Celery task — sync all DB records to the vector store every N minutes
