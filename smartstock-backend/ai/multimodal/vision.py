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
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Extract the invoice header fields and every line-item row.',
                        },
                        {'type': 'image_url', 'image_url': {'url': file_data_url}},
                    ],
                },
            ],
        )
        content = response.choices[0].message.content or ''
        return self._parse_json(content)

    def _parse_json(self, content: str) -> dict:
        cleaned = content.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        return json.loads(cleaned)
