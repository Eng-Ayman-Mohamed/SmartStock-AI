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
        from ai.llm.provider_config import get_provider_config

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
