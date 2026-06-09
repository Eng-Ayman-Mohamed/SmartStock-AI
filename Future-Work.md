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

RAG remaining improvements:

1. Django signals or a Celery task to re-ingest when source PDFs change in Cloudinary
2. Bulk upload support (multiple PDFs at once)
3. Document versioning (keep old versions accessible)

---

## Frontend design critique findings (2026-06-10)

### Strategic

**Real AI Assistant API** — `src/features/ai-assistant/pages/AIAssistantPage.tsx`
Chat is mocked with `setTimeout` and hardcoded placeholder response. Needs connection to real LLM endpoint (backend `/api/ai/chat/`) for streaming, context-aware answers, and actual inventory queries.

**Keyboard shortcuts** — Global

- `Ctrl+K` command palette, `n` new product, `a` approve PO, `?` shortcut overlay

**Help system & onboarding** — Global
First-time wizard (3 steps), contextual tooltips on complex features, help menu in header.

**Bulk operations** — `InventoryPage.tsx`, `PurchasingPage.tsx`
Multi-select checkboxes, bulk delete/status update, batch approve/reject.

### Design polish

**8px grid drift** — `ForecastingPage.tsx:73` uses `gap-5` instead of `gap-6`

**StatCard hardcoded sizes** — `StatCard.tsx:33` uses `text-[26px]` and `text-[11px]` instead of design tokens

**Sidebar tooltip overflow** — `Sidebar.tsx:159` `left-full ml-2` can overflow viewport edge

### Delight & micro-interactions

- Chart hover effects (crosshair, gradient fills, data point highlight)
- Success animations on mutations (green flash on row, checkmark stamp)
- Empty state custom SVGs using sticker palette instead of Lucide icons

### Pre-existing issues (unchanged)

- **SuppliersPage.tsx** not found — sidebar links to `/suppliers` but page is missing
- **SettingsPage.tsx** not found — referenced in sidebar and breadcrumb config
- **11 lint errors** in `purchasing/` — `SupplierModal.tsx` setState in effect, unused `err` variable, 8x `any` types

### Build

- Main JS bundle ~808 kB exceeds 500 kB — consider route-level code-splitting with `React.lazy()` and dynamic imports for chart/AI libraries
