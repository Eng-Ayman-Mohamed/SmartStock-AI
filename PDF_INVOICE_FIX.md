# Fix: PDF invoice scanning (400 Bad Request)

## What was happening
Uploading a **PDF** invoice failed with `400 Bad Request` from the vision API.
Image invoices (PNG / JPEG / WebP) worked fine.

**Root cause:** the OpenAI-compatible vision endpoint (Groq / OpenAI) only accepts
raster images through the `image_url` content type. `VisionExtractor` was sending
the PDF bytes straight through as an `image_url` data URL, which the provider
rejects — hence the 400.

## The fix
PDFs are now rasterized to images **before** being sent to the vision model.

### Code changes
- **`smartstock-backend/ai/multimodal/vision.py`**
  - `_is_pdf(data_url)` — detects `application/pdf` data URLs.
  - `_convert_pdf_to_images(data_url)` — decodes the base64 PDF and renders each
    page to a JPEG data URL via `pdf2image.convert_from_bytes` (Poppler).
    - DPI = `200`, JPEG quality `85` (good quality, bounded size).
    - Capped at `MAX_PDF_PAGES = 5` so multi-page invoices still extract all
      line items without runaway token usage.
    - Failures (missing `pdf2image`/Poppler, corrupt PDF, empty PDF) raise a
      clear `ValueError`, which the service maps to a clean
      `InvoiceExtractionMalformed` message instead of a raw 400/500.
  - `_extract_openai_compatible(...)` — converts PDFs to one-or-more `image_url`
    parts; images still pass through unchanged.
  - Gemini path is untouched — it accepts `application/pdf` natively.

- **`smartstock-backend/requirements.txt`** — added `pdf2image` and `Pillow`.
- **`smartstock-backend/Dockerfile`** — added the `poppler-utils` system package
  (Poppler is the rendering backend `pdf2image` shells out to).

### Tests
- **`smartstock-backend/tests/unit/ai/test_vision_pdf.py`** — covers PDF
  detection, image pass-through, PDF → JPEG rasterization, the page cap/DPI being
  forwarded, and the three error paths (corrupt PDF, no pages, missing
  `pdf2image`). `pdf2image` is mocked so the suite needs no Poppler binary.

## Behavior after the fix
| Input | Before | After |
|-------|--------|-------|
| PDF invoice | ❌ 400 Bad Request | ✅ rasterized → extracted |
| JPEG / PNG invoice | ✅ works | ✅ unchanged |
| Corrupt / empty PDF | ❌ opaque error | ✅ clean "malformed" message |
| Multi-page PDF | n/a | ✅ up to 5 pages extracted |

## Deployment note
Rebuild the backend image so `poppler-utils` + the new Python deps are installed.
Without the Poppler binary, PDF scans return the clear "Poppler not installed"
message rather than crashing.
