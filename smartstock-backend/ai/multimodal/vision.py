import json
import os
import re

from openai import OpenAI


class VisionExtractor:
    REQUIRED_FIELDS = [
        'product_name',
        'sku_code',
        'quantity_received',
        'unit_price',
        'supplier_name',
    ]

    def __init__(self, client=None, model: str = 'gpt-4o', timeout: int = 15):
        self.client = client
        self.model = model
        self.timeout = timeout

    def extract(self, file_data_url: str) -> dict:
        client = self.client or OpenAI(api_key=os.getenv('OPENAI_API_KEY'), timeout=self.timeout)
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
