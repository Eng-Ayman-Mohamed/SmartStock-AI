import json
import re


class VisionExtractor:
    REQUIRED_FIELDS = [
        'product_name',
        'sku_code',
        'quantity_received',
        'unit_price',
        'supplier_name',
    ]

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

        schema = {
            field: {'value': 'string or number', 'confidence': 'number from 0.0 to 1.0'}
            for field in self.REQUIRED_FIELDS
        }

        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                'Extract supplier invoice data as strict JSON only. '
                'Do not include markdown. Use this schema: ' + json.dumps(schema),
            ],
        )
        content = response.text or ''
        return self._parse_json(content)

    def _extract_openai_compatible(self, file_data_url: str) -> dict:
        """Extract invoice data using OpenAI-compatible vision API (OpenAI/Groq)."""
        from ai.llm.provider_config import get_vision_client

        client = self.client or get_vision_client()
        schema = {
            field: {'value': 'string or number', 'confidence': 'number from 0.0 to 1.0'}
            for field in self.REQUIRED_FIELDS
        }
        response = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        'Extract supplier invoice data as strict JSON only. '
                        'Do not include markdown. Use this schema: ' + json.dumps(schema)
                    ),
                },
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': 'Extract invoice fields and confidence scores.'},
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
