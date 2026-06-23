"""Tolerant parsing of vision-model invoice JSON into a stable structure.

The vision model is asked for ``{"header": {...}, "line_items": [...]}`` but real
responses are messy: fields may arrive flat, wrapped as ``{"value", "confidence"}``,
under aliased keys, or with malformed rows. ``InvoiceExtraction.from_vision_json``
absorbs all of that without ever raising on a single bad cell, and also understands
the LEGACY flat 5-field shape so older callers/tests keep working.

Pure pydantic + stdlib (no Django import) so it stays cheap to unit-test.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Accepted aliases for header fields (first match wins).
HEADER_ALIASES: dict[str, list[str]] = {
    'supplier_name': ['supplier_name', 'supplier', 'vendor', 'vendor_name', 'seller', 'from'],
    'invoice_number': ['invoice_number', 'invoice_no', 'invoice_id', 'number', 'inv_no', 'invoice'],
    'invoice_date': ['invoice_date', 'date', 'issue_date', 'issued', 'issued_on'],
    'due_date': ['due_date', 'payment_due', 'due', 'due_on'],
    'currency': ['currency', 'currency_code', 'curr'],
    'invoice_total': [
        'invoice_total',
        'total',
        'grand_total',
        'total_amount',
        'amount_due',
        'amount',
    ],
    'tax_amount': ['tax_amount', 'tax', 'vat', 'vat_amount', 'tax_total', 'gst'],
}

# Accepted aliases for line-item columns (first match wins).
LINE_ALIASES: dict[str, list[str]] = {
    'item_name': ['item_name', 'name', 'description', 'product_name', 'item', 'product'],
    'sku_code': ['sku_code', 'sku', 'code', 'item_code', 'product_code'],
    'quantity': ['quantity', 'qty', 'quantity_received', 'count', 'units'],
    'unit_price': ['unit_price', 'price', 'rate', 'unit_cost', 'cost'],
    'total_price': ['total_price', 'total', 'line_total', 'amount', 'subtotal'],
}

NUMERIC_HEADER = {'invoice_total', 'tax_amount'}
NUMERIC_LINE = {'quantity', 'unit_price', 'total_price'}

LEGACY_FIELDS = ['product_name', 'sku_code', 'quantity_received', 'unit_price', 'supplier_name']


def _unwrap(raw):
    """Return ``(value, confidence)`` from a plain value or a ``{value, confidence}`` dict."""
    if isinstance(raw, dict) and ('value' in raw or 'confidence' in raw):
        return raw.get('value'), raw.get('confidence')
    return raw, None


def _clean_str(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coerce_number(value):
    """Best-effort numeric coercion; tolerates '$', ',' and blanks. Returns None on failure."""
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = value
    else:
        cleaned = str(value).replace('$', '').replace(',', '').strip()
        if not cleaned:
            return None
        try:
            number = float(cleaned)
        except (TypeError, ValueError):
            return None
    if isinstance(number, float) and number.is_integer():
        return int(number)
    return number


def _pick(source: dict, aliases: list[str]):
    for alias in aliases:
        if alias in source:
            return source[alias]
    return None


class InvoiceLineItem(BaseModel):
    item_name: Optional[str] = None
    sku_code: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None

    def is_empty(self) -> bool:
        return all(
            getattr(self, field) in (None, '')
            for field in ('item_name', 'sku_code', 'quantity', 'unit_price', 'total_price')
        )


class InvoiceHeader(BaseModel):
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = None
    invoice_total: Optional[float] = None
    tax_amount: Optional[float] = None


class InvoiceExtraction(BaseModel):
    header: InvoiceHeader = Field(default_factory=InvoiceHeader)
    line_items: list[InvoiceLineItem] = Field(default_factory=list)
    confidence: dict = Field(default_factory=dict)

    @classmethod
    def from_vision_json(cls, raw) -> 'InvoiceExtraction':
        if not isinstance(raw, dict):
            return cls()

        confidence: dict = {}
        header_src = raw.get('header') if isinstance(raw.get('header'), dict) else None
        line_src = raw.get('line_items') if isinstance(raw.get('line_items'), list) else None

        if header_src is not None or line_src is not None:
            header = cls._parse_header(header_src or {}, confidence)
            line_items = cls._parse_line_items(line_src or [], confidence)
        else:
            fields_blob = raw.get('fields') if isinstance(raw.get('fields'), dict) else raw
            conf_blob = raw.get('confidence') if isinstance(raw.get('confidence'), dict) else {}
            header, line_items = cls._parse_legacy(fields_blob, conf_blob, confidence)

        # Merge any top-level confidence blob for header fields not already captured.
        top_conf = raw.get('confidence') if isinstance(raw.get('confidence'), dict) else {}
        for key, value in top_conf.items():
            confidence.setdefault(key, value)

        return cls(header=header, line_items=line_items, confidence=confidence)

    @staticmethod
    def _parse_header(source: dict, confidence: dict) -> InvoiceHeader:
        data = {}
        for key, aliases in HEADER_ALIASES.items():
            value, conf = _unwrap(_pick(source, aliases))
            data[key] = _coerce_number(value) if key in NUMERIC_HEADER else _clean_str(value)
            if conf is not None:
                confidence[key] = conf
        return InvoiceHeader(**data)

    @staticmethod
    def _parse_line_items(rows: list, confidence: dict) -> list[InvoiceLineItem]:
        items: list[InvoiceLineItem] = []
        scores: list[float] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            data = {}
            row_scores: list[float] = []
            for key, aliases in LINE_ALIASES.items():
                value, conf = _unwrap(_pick(row, aliases))
                data[key] = _coerce_number(value) if key in NUMERIC_LINE else _clean_str(value)
                if conf is not None:
                    coerced = _coerce_number(conf)
                    if coerced is not None:
                        row_scores.append(float(coerced))
            row_conf = _coerce_number(row.get('confidence'))
            if row_conf is not None:
                row_scores.append(float(row_conf))
            item = InvoiceLineItem(**data)
            if item.is_empty():
                continue
            items.append(item)
            if row_scores:
                scores.append(sum(row_scores) / len(row_scores))
        if scores:
            confidence['line_items'] = sum(scores) / len(scores)
        return items

    @staticmethod
    def _parse_legacy(fields_blob: dict, conf_blob: dict, confidence: dict):
        legacy = {}
        for field in LEGACY_FIELDS:
            value, conf = _unwrap(fields_blob.get(field))
            if conf is None:
                conf = conf_blob.get(field)
            legacy[field] = value
            if conf is not None:
                confidence[field] = conf

        header = InvoiceHeader(supplier_name=_clean_str(legacy.get('supplier_name')))
        line = InvoiceLineItem(
            item_name=_clean_str(legacy.get('product_name')),
            sku_code=_clean_str(legacy.get('sku_code')),
            quantity=_coerce_number(legacy.get('quantity_received')),
            unit_price=_coerce_number(legacy.get('unit_price')),
        )
        line_items = [] if line.is_empty() else [line]
        return header, line_items
