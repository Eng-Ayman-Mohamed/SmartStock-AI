from ai.llm.invoice_schema import InvoiceExtraction


def test_parses_new_header_and_line_items_shape():
    raw = {
        'header': {
            'supplier_name': {'value': 'Acme', 'confidence': 0.9},
            'invoice_number': {'value': 'INV-1', 'confidence': 0.8},
            'invoice_date': '2026-01-05',
            'invoice_total': {'value': '1,234.50', 'confidence': 0.7},
            'tax_amount': '$10',
        },
        'line_items': [
            {
                'item_name': 'Mouse',
                'sku_code': 'WM-1',
                'quantity': '12',
                'unit_price': '21.25',
                'total_price': '255',
            },
            {'item_name': 'Keyboard', 'sku': 'KB-1', 'qty': 3, 'price': 40},
        ],
    }

    extraction = InvoiceExtraction.from_vision_json(raw)

    assert extraction.header.supplier_name == 'Acme'
    assert extraction.header.invoice_number == 'INV-1'
    assert extraction.header.invoice_date == '2026-01-05'
    assert extraction.header.invoice_total == 1234.5
    assert extraction.header.tax_amount == 10
    assert len(extraction.line_items) == 2
    assert extraction.line_items[0].quantity == 12
    assert extraction.line_items[0].unit_price == 21.25
    # Aliased keys on the second row resolve correctly.
    assert extraction.line_items[1].sku_code == 'KB-1'
    assert extraction.line_items[1].quantity == 3
    assert extraction.line_items[1].unit_price == 40
    assert extraction.confidence['supplier_name'] == 0.9


def test_skips_malformed_line_rows():
    raw = {
        'header': {},
        'line_items': ['bad', None, 5, {'item_name': 'Good', 'sku_code': 'G-1', 'quantity': 1}],
    }

    extraction = InvoiceExtraction.from_vision_json(raw)

    assert len(extraction.line_items) == 1
    assert extraction.line_items[0].item_name == 'Good'


def test_drops_fully_empty_line_rows():
    raw = {'header': {}, 'line_items': [{'item_name': None, 'sku_code': None, 'quantity': None}]}

    extraction = InvoiceExtraction.from_vision_json(raw)

    assert extraction.line_items == []


def test_parses_legacy_flat_shape_into_single_line():
    raw = {
        'product_name': {'value': 'Mouse', 'confidence': 0.95},
        'sku_code': {'value': 'WM-1', 'confidence': 0.9},
        'quantity_received': {'value': 12, 'confidence': 0.8},
        'unit_price': {'value': '21.25', 'confidence': 0.7},
        'supplier_name': {'value': 'Acme', 'confidence': 0.85},
    }

    extraction = InvoiceExtraction.from_vision_json(raw)

    assert extraction.header.supplier_name == 'Acme'
    assert len(extraction.line_items) == 1
    assert extraction.line_items[0].item_name == 'Mouse'
    assert extraction.line_items[0].sku_code == 'WM-1'
    assert extraction.line_items[0].quantity == 12
    assert extraction.line_items[0].unit_price == 21.25
    assert extraction.confidence['product_name'] == 0.95


def test_legacy_fields_under_fields_key_with_confidence_blob():
    raw = {
        'fields': {'product_name': 'Mouse', 'sku_code': 'WM-1', 'quantity_received': 5},
        'confidence': {'product_name': 0.6},
    }

    extraction = InvoiceExtraction.from_vision_json(raw)

    assert extraction.line_items[0].item_name == 'Mouse'
    assert extraction.line_items[0].quantity == 5
    assert extraction.confidence['product_name'] == 0.6


def test_non_dict_returns_empty_extraction():
    extraction = InvoiceExtraction.from_vision_json(['not', 'a', 'dict'])

    assert extraction.line_items == []
    assert extraction.header.supplier_name is None


def test_coerces_currency_and_thousands_separators():
    raw = {'header': {'invoice_total': '$2,000.75'}, 'line_items': []}

    extraction = InvoiceExtraction.from_vision_json(raw)

    assert extraction.header.invoice_total == 2000.75
