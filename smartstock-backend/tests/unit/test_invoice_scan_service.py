from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from apps.audit.models import AuditEvent
from apps.ingestion.services import (
    InvoiceAlreadyConfirmed,
    InvoiceExtractionMalformed,
    InvoiceExtractionTimeout,
    InvoiceScanService,
)
from apps.inventory.services import InventoryService


class FakeFile:
    name = 'invoice.png'
    content_type = 'image/png'

    def __init__(self, content=b'image-bytes'):
        self.content = content
        self.offset = 0

    def read(self):
        self.offset = len(self.content)
        return self.content

    def seek(self, offset):
        self.offset = offset


class FakeInvoiceRepo:
    def __init__(self, scan=None):
        self.scan = scan
        self.updated = []

    def create(self, data):
        self.scan = SimpleNamespace(
            id=1,
            uploaded_by_id=data['uploaded_by'].id,
            original_filename=data['original_filename'],
            content_type=data['content_type'],
            file_size=data['file_size'],
            status='pending',
            extracted_data={},
            confidence={},
            missing_fields=[],
            failure_reason='',
            confirmed_data={},
            is_confirmed=False,
        )
        return self.scan

    def update(self, scan_id, data):
        assert scan_id == self.scan.id
        self.updated.append(data)
        for key, value in data.items():
            setattr(self.scan, key, value)
        return self.scan

    def get_by_id(self, scan_id):
        assert scan_id == self.scan.id
        return self.scan

    def mark_confirmed(self, scan_id, confirmed_data):
        return self.update(
            scan_id,
            {
                'status': 'confirmed',
                'confirmed_data': confirmed_data,
                'is_confirmed': True,
            },
        )

    def mark_rejected(self, scan_id):
        return self.update(scan_id, {'status': 'rejected'})


class FakeExtractor:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def extract(self, file_data_url):
        if self.error:
            raise self.error
        return self.response


class FakeInventoryService:
    def __init__(self):
        self.calls = []

    def apply_confirmed_invoice(self, confirmed_data, user=None):
        self.calls.append((confirmed_data, user))
        return {
            'product_id': 10,
            'sku_id': 20,
            'stock_level_id': 30,
            'quantity_added': int(confirmed_data['quantity_received']),
            'quantity_on_hand': int(confirmed_data['quantity_received']),
        }


def user(user_id):
    return SimpleNamespace(id=user_id)


def complete_extraction():
    return {
        'product_name': {'value': 'Wireless Mouse', 'confidence': 0.95},
        'sku_code': {'value': 'WM-001', 'confidence': 0.98},
        'quantity_received': {'value': 12, 'confidence': 0.9},
        'unit_price': {'value': '21.25', 'confidence': 0.88},
        'supplier_name': {'value': 'TechSupply', 'confidence': 0.85},
    }


def test_scan_invoice_returns_partial_and_audits_missing_fields():
    audits = []
    repo = FakeInvoiceRepo()
    extractor = FakeExtractor(response={'product_name': {'value': 'Mouse', 'confidence': 0.91}})
    service = InvoiceScanService(
        repo=repo, extractor=extractor, audit_logger=lambda *args, **kwargs: audits.append(args)
    )

    result = service.scan_invoice(FakeFile(), user(1))

    assert result['status'] == 'partial'
    assert 'sku_code' in result['missing_fields']
    assert repo.scan.status == 'partial'
    assert audits[0][0] == AuditEvent.VISION_EXTRACTION_FAILED


def test_scan_invoice_malformed_json_marks_failed_and_raises_422_error():
    audits = []
    repo = FakeInvoiceRepo()
    service = InvoiceScanService(
        repo=repo,
        extractor=FakeExtractor(error=ValueError('bad json')),
        audit_logger=lambda *args, **kwargs: audits.append(args),
    )

    with pytest.raises(InvoiceExtractionMalformed):
        service.scan_invoice(FakeFile(), user(1))

    assert repo.scan.status == 'failed'
    assert repo.scan.failure_reason == 'bad json'
    assert audits[0][0] == AuditEvent.VISION_EXTRACTION_FAILED


def test_scan_invoice_timeout_marks_failed_and_raises_timeout_error():
    repo = FakeInvoiceRepo()
    service = InvoiceScanService(
        repo=repo,
        extractor=FakeExtractor(error=TimeoutError('slow')),
        audit_logger=lambda *args, **kwargs: None,
    )

    with pytest.raises(InvoiceExtractionTimeout):
        service.scan_invoice(FakeFile(), user(1))

    assert repo.scan.status == 'failed'


def test_scan_invoice_non_object_response_marks_failed_and_raises_422_error():
    audits = []
    repo = FakeInvoiceRepo()
    service = InvoiceScanService(
        repo=repo,
        extractor=FakeExtractor(response=['not', 'an', 'object']),
        audit_logger=lambda *args, **kwargs: audits.append((args, kwargs)),
    )

    with pytest.raises(InvoiceExtractionMalformed):
        service.scan_invoice(FakeFile(), user(1))

    assert repo.scan.status == 'failed'
    assert repo.scan.failure_reason == 'Vision response was not a JSON object.'
    assert audits[0][1]['data']['reason'] == 'malformed_json'


def test_confirm_scan_rejects_other_users_scan():
    owner = user(1)
    scan = SimpleNamespace(id=1, uploaded_by_id=owner.id, is_confirmed=False, status='extracted')
    service = InvoiceScanService(
        repo=FakeInvoiceRepo(scan=scan), audit_logger=lambda *args, **kwargs: None
    )

    with pytest.raises(PermissionError):
        service.confirm_scan(1, user(2), complete_extraction_payload())


def test_confirm_scan_rejects_already_confirmed_scan():
    owner = user(1)
    scan = SimpleNamespace(id=1, uploaded_by_id=owner.id, is_confirmed=True, status='confirmed')
    service = InvoiceScanService(
        repo=FakeInvoiceRepo(scan=scan), audit_logger=lambda *args, **kwargs: None
    )

    with pytest.raises(InvoiceAlreadyConfirmed):
        service.confirm_scan(1, owner, complete_extraction_payload())


def test_confirm_scan_rejects_rejected_scan():
    owner = user(1)
    scan = SimpleNamespace(id=1, uploaded_by_id=owner.id, is_confirmed=False, status='rejected')
    service = InvoiceScanService(
        repo=FakeInvoiceRepo(scan=scan), audit_logger=lambda *args, **kwargs: None
    )

    with pytest.raises(ValidationError):
        service.confirm_scan(1, owner, complete_extraction_payload())


def test_confirm_scan_requires_all_invoice_fields():
    owner = user(1)
    scan = SimpleNamespace(id=1, uploaded_by_id=owner.id, is_confirmed=False, status='extracted')
    service = InvoiceScanService(
        repo=FakeInvoiceRepo(scan=scan), audit_logger=lambda *args, **kwargs: None
    )
    payload = complete_extraction_payload()
    payload['supplier_name'] = ''

    with pytest.raises(ValidationError) as exc:
        service.confirm_scan(1, owner, payload)

    assert 'supplier_name' in str(exc.value)


def test_confirm_scan_updates_inventory_and_audits_changes():
    audits = []
    owner = user(1)
    scan = SimpleNamespace(
        id=1,
        uploaded_by_id=owner.id,
        is_confirmed=False,
        status='extracted',
        extracted_data={
            'product_name': 'Wireless Mouse',
            'sku_code': 'WM-001',
            'quantity_received': 10,
            'unit_price': '21.25',
            'supplier_name': 'TechSupply',
        },
        confidence={},
        missing_fields=[],
        failure_reason='',
        confirmed_data={},
    )
    inventory = FakeInventoryService()
    service = InvoiceScanService(
        repo=FakeInvoiceRepo(scan=scan),
        inventory_service=inventory,
        audit_logger=lambda *args, **kwargs: audits.append((args, kwargs)),
    )
    confirmed = complete_extraction_payload()
    confirmed['quantity_received'] = 12

    result = service.confirm_scan(1, owner, confirmed)

    assert result['status'] == 'confirmed'
    assert inventory.calls[0][0]['quantity_received'] == 12
    assert audits[0][0][0] == AuditEvent.INVOICE_CONFIRMED
    assert audits[0][1]['data']['changed_fields']['quantity_received'] == {
        'original': 10,
        'confirmed': 12,
    }


def scan_payload(status='extracted', is_confirmed=False):
    return SimpleNamespace(
        id=1,
        uploaded_by_id=1,
        is_confirmed=is_confirmed,
        status=status,
        extracted_data={'sku_code': 'WM-001'},
        confidence={'sku_code': 0.95},
        missing_fields=[],
        failure_reason='',
        confirmed_data={},
    )


def test_reject_scan_marks_scan_rejected_and_audits():
    audits = []
    service = InvoiceScanService(
        repo=FakeInvoiceRepo(scan=scan_payload()),
        audit_logger=lambda *args, **kwargs: audits.append((args, kwargs)),
    )

    result = service.reject_scan(1, user(1))

    assert result['status'] == 'rejected'
    assert audits[0][0][0] == AuditEvent.INVOICE_REJECTED
    assert audits[0][1]['data']['extracted_data'] == {'sku_code': 'WM-001'}


def test_reject_scan_rejects_already_confirmed_scan():
    service = InvoiceScanService(
        repo=FakeInvoiceRepo(scan=scan_payload(status='confirmed', is_confirmed=True)),
        audit_logger=lambda *args, **kwargs: None,
    )

    with pytest.raises(InvoiceAlreadyConfirmed):
        service.reject_scan(1, user(1))


class FakeProductRepo:
    def __init__(self, created_product=None):
        self.created_product = created_product or SimpleNamespace(id=101)
        self.created = []
        self.updated = []

    def create(self, data):
        self.created.append(data)
        for key, value in data.items():
            setattr(self.created_product, key, value)
        return self.created_product

    def update(self, product_id, data):
        self.updated.append((product_id, data))
        return SimpleNamespace(id=product_id, **data)


class FakeStockRepo:
    def __init__(self, stock=None):
        self.stock = stock
        self.created = []
        self.updated = []

    def get_by_sku_id(self, sku_id):
        return self.stock if self.stock and self.stock.sku.id == sku_id else None

    def create(self, data):
        self.created.append(data)
        self.stock = SimpleNamespace(id=301, **data)
        return self.stock

    def update(self, stock_id, data):
        self.updated.append((stock_id, data))
        for key, value in data.items():
            setattr(self.stock, key, value)
        return self.stock


class FakeSkuRepo:
    def __init__(self, sku=None):
        self.sku = sku
        self.created = []

    def get_by_code(self, sku_code):
        return self.sku if self.sku and self.sku.code == sku_code else None

    def create(self, data):
        self.created.append(data)
        self.sku = SimpleNamespace(id=201, **data)
        return self.sku


class FakeSupplierRepo:
    def __init__(self, supplier=None):
        self.supplier = supplier
        self.names = []

    def get_by_name(self, supplier_name):
        self.names.append(supplier_name)
        return self.supplier if self.supplier and self.supplier.name == supplier_name else None


def inventory_service(repo, stock_repo, sku_repo, supplier_repo, monkeypatch):
    monkeypatch.setattr('apps.inventory.services._invalidate_product_cache', lambda: None)
    return InventoryService(
        repo=repo,
        stock_repo=stock_repo,
        sku_repo=sku_repo,
        supplier_repo=supplier_repo,
    )


def test_apply_confirmed_invoice_updates_existing_sku_stock_and_product(monkeypatch):
    supplier = SimpleNamespace(id=9, name='TechSupply')
    product = SimpleNamespace(id=10)
    sku = SimpleNamespace(id=20, code='WM-001', product=product)
    stock = SimpleNamespace(id=30, sku=sku, quantity_on_hand=5)
    repo = FakeProductRepo()
    stock_repo = FakeStockRepo(stock=stock)
    sku_repo = FakeSkuRepo(sku=sku)
    supplier_repo = FakeSupplierRepo(supplier=supplier)
    service = inventory_service(repo, stock_repo, sku_repo, supplier_repo, monkeypatch)

    result = service.apply_confirmed_invoice(
        {
            'product_name': 'Wireless Mouse',
            'sku_code': ' wm-001 ',
            'quantity_received': '7',
            'unit_price': '$1,234.5',
            'supplier_name': 'TechSupply',
        }
    )

    assert stock_repo.updated == [(30, {'quantity_on_hand': 12})]
    assert repo.updated[0][0] == 10
    assert str(repo.updated[0][1]['unit_price']) == '1234.50'
    assert repo.updated[0][1]['supplier'] is supplier
    assert result['quantity_added'] == 7
    assert result['quantity_on_hand'] == 12


def test_apply_confirmed_invoice_creates_product_sku_and_stock(monkeypatch):
    repo = FakeProductRepo(created_product=SimpleNamespace(id=11))
    stock_repo = FakeStockRepo()
    sku_repo = FakeSkuRepo()
    supplier_repo = FakeSupplierRepo()
    service = inventory_service(repo, stock_repo, sku_repo, supplier_repo, monkeypatch)

    result = service.apply_confirmed_invoice(
        {
            'product_name': 'Keyboard',
            'sku_code': 'KB-001',
            'quantity_received': 3,
            'unit_price': '',
            'supplier_name': '',
        }
    )

    assert repo.created == [{'name': 'Keyboard', 'supplier': None, 'unit_price': None}]
    assert sku_repo.created == [{'product': repo.created_product, 'code': 'KB-001'}]
    assert stock_repo.created[0]['quantity_on_hand'] == 3
    assert result['product_id'] == 11


def test_apply_confirmed_invoice_creates_missing_stock_for_existing_sku(monkeypatch):
    product = SimpleNamespace(id=10)
    sku = SimpleNamespace(id=20, code='WM-001', product=product)
    repo = FakeProductRepo()
    stock_repo = FakeStockRepo()
    sku_repo = FakeSkuRepo(sku=sku)
    supplier_repo = FakeSupplierRepo()
    service = inventory_service(repo, stock_repo, sku_repo, supplier_repo, monkeypatch)

    result = service.apply_confirmed_invoice(
        {
            'product_name': 'Wireless Mouse',
            'sku_code': 'WM-001',
            'quantity_received': 4,
            'unit_price': None,
            'supplier_name': '',
        }
    )

    assert stock_repo.created == [{'sku': sku, 'quantity_on_hand': 4}]
    assert repo.updated == []
    assert result['stock_level_id'] == 301


@pytest.mark.parametrize(
    ('field', 'value', 'message'),
    [
        ('quantity_received', 0, 'Quantity received must be at least 1.'),
        ('unit_price', 'not-a-price', 'Unit price must be a valid decimal.'),
        ('unit_price', '-1.00', 'Unit price cannot be negative.'),
    ],
)
def test_apply_confirmed_invoice_validates_quantity_and_price(field, value, message, monkeypatch):
    service = inventory_service(
        FakeProductRepo(),
        FakeStockRepo(),
        FakeSkuRepo(),
        FakeSupplierRepo(),
        monkeypatch,
    )
    payload = {
        'product_name': 'Wireless Mouse',
        'sku_code': 'WM-001',
        'quantity_received': 1,
        'unit_price': '1.00',
        'supplier_name': '',
    }
    payload[field] = value

    with pytest.raises(ValidationError) as exc:
        service.apply_confirmed_invoice(payload)

    assert message in str(exc.value)


def complete_extraction_payload():
    return {
        'product_name': 'Wireless Mouse',
        'sku_code': 'WM-001',
        'quantity_received': 10,
        'unit_price': '21.25',
        'supplier_name': 'TechSupply',
    }
