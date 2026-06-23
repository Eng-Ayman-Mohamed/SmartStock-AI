import json
import re


class VisionExtractor:
    # Legacy flat field list, kept for backward compatibility (still imported elsewhere).
    REQUIRED_FIELDS = [
        'product_name',
        'sku_code',
        'quantity_received',
        'unit_price',
        'supplier_name',
    ]

    # Structured schema requested from the vision model: invoice header + line items.
    INVOICE_SCHEMA = {
        'header': {
            'supplier_name': {'value': 'string', 'confidence': 'number 0.0-1.0'},
            'invoice_number': {'value': 'string or null', 'confidence': 'number 0.0-1.0'},
            'invoice_date': {'value': 'YYYY-MM-DD or null', 'confidence': 'number 0.0-1.0'},
            'due_date': {'value': 'YYYY-MM-DD or null', 'confidence': 'number 0.0-1.0'},
            'invoice_total': {'value': 'number or null', 'confidence': 'number 0.0-1.0'},
            'tax_amount': {'value': 'number or null', 'confidence': 'number 0.0-1.0'},
            'currency': {'value': 'string or null', 'confidence': 'number 0.0-1.0'},
        },
        'line_items': [
            {
                'item_name': 'string',
                'sku_code': 'string or null',
                'quantity': 'number',
                'unit_price': 'number',
                'total_price': 'number or null',
            }
        ],
    }

    SYSTEM_PROMPT = (
        'You extract structured data from a supplier invoice for a warehouse inventory system. '
        'Return STRICT JSON only, no markdown. The top-level object must have exactly two keys: '
        '"header" (an object) and "line_items" (an array with one object per product row). '
        'Use null for any field that is not present. Write dates as ISO YYYY-MM-DD. '
        'Write all numbers as plain numbers without currency symbols or thousands separators. '
        'Use this schema: '
    )

    # PDF rasterization settings. Groq/OpenAI vision endpoints reject PDFs sent
    # as image_url, so PDF invoices are rendered to JPEG pages first. The cap
    # bounds token usage while still covering multi-page invoices.
    PDF_DPI = 200
    MAX_PDF_PAGES = 5

    def __init__(self, client=None, model: str = None, timeout: int = 15):
        from ai.llm.provider_config import PROVIDER, get_provider_config

        self._provider = PROVIDER
        config = get_provider_config()
        self.client = client
        self.model = model or config.get('vision_model')
        self.timeout = timeout
        self._supports_vision = config.get('supports_vision', True)

    def extract(self, file_data_url: str) -> dict:
        if not self._supports_vision or not self.model:
            from ai.llm.provider_config import PROVIDER

            raise ValueError(
                f'Provider "{PROVIDER}" does not support vision/image analysis. '
                'Switch to OpenAI or Gemini for invoice scanning.'
            )

        if self._provider == 'gemini':
            return self._extract_gemini(file_data_url)

        return self._extract_openai_compatible(file_data_url)

    def _extract_gemini(self, file_data_url: str) -> dict:
        """Extract invoice data using Google Gemini vision API."""
        from google import genai
        from google.genai import types

        from ai.llm.provider_config import get_api_key

        client = genai.Client(api_key=get_api_key())

        # Convert data URL to bytes for Gemini
        import base64

        header, b64data = file_data_url.split(',', 1)
        mime_type = header.split(':')[1].split(';')[0]
        image_bytes = base64.b64decode(b64data)

        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                self.SYSTEM_PROMPT + json.dumps(self.INVOICE_SCHEMA),
            ],
        )
        content = response.text or ''
        return self._parse_json(content)

    def _extract_openai_compatible(self, file_data_url: str) -> dict:
        """Extract invoice data using OpenAI-compatible vision API (OpenAI/Groq)."""
        from ai.llm.provider_config import get_vision_client

        if self._is_pdf(file_data_url):
            image_urls = self._convert_pdf_to_images(file_data_url)
        else:
            image_urls = [file_data_url]

        user_content = [
            {
                'type': 'text',
                'text': 'Extract the invoice header fields and every line-item row.',
            },
        ]
        user_content.extend({'type': 'image_url', 'image_url': {'url': url}} for url in image_urls)

        client = self.client or get_vision_client()
        response = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    'role': 'system',
                    'content': self.SYSTEM_PROMPT + json.dumps(self.INVOICE_SCHEMA),
                },
                {
                    'role': 'user',
                    'content': user_content,
                },
            ],
        )
        content = response.choices[0].message.content or ''
        return self._parse_json(content)

    @staticmethod
    def _is_pdf(file_data_url: str) -> bool:
        """Return True when a data URL carries a PDF payload."""
        header = file_data_url.split(',', 1)[0]
        return 'application/pdf' in header.lower()

    def _convert_pdf_to_images(self, pdf_data_url: str) -> list[str]:
        """Rasterize a base64 PDF data URL into JPEG image data URLs (one per page).

        Vision endpoints that only accept raster images need the PDF rendered
        first. Raises ValueError with an actionable message on any failure so the
        caller surfaces a clean "malformed" error instead of a raw 400/500.
        """
        import base64
        from io import BytesIO

        _, b64data = pdf_data_url.split(',', 1)
        pdf_bytes = base64.b64decode(b64data)

        try:
            from pdf2image import convert_from_bytes
        except ImportError as exc:
            raise ValueError(
                'PDF invoice support requires the pdf2image package and the '
                'Poppler system dependency.'
            ) from exc

        try:
            pages = convert_from_bytes(pdf_bytes, dpi=self.PDF_DPI, last_page=self.MAX_PDF_PAGES)
        except Exception as exc:
            raise ValueError(
                f'Could not read PDF invoice (corrupt file or Poppler not installed): {exc}'
            ) from exc

        if not pages:
            raise ValueError('PDF invoice contained no readable pages.')

        image_urls = []
        for page in pages:
            buffer = BytesIO()
            page.convert('RGB').save(buffer, format='JPEG', quality=85)
            encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
            image_urls.append(f'data:image/jpeg;base64,{encoded}')
        return image_urls

    def _parse_json(self, content: str) -> dict:
        cleaned = content.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        return json.loads(cleaned)
