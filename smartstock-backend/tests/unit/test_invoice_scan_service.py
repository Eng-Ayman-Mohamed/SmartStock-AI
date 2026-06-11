from types import SimpleNamespace

import pytest

from apps.audit.models import AuditEvent
from apps.ingestion.services import (
    InvoiceAlreadyConfirmed,
    InvoiceExtractionMalformed,
    InvoiceExtractionTimeout,
    InvoiceScanService,
)


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
    service = InvoiceScanService(repo=repo, extractor=extractor, audit_logger=lambda *args, **kwargs: audits.append(args))

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


def test_confirm_scan_rejects_other_users_scan():
    owner = user(1)
    scan = SimpleNamespace(id=1, uploaded_by_id=owner.id, is_confirmed=False, status='extracted')
    service = InvoiceScanService(repo=FakeInvoiceRepo(scan=scan), audit_logger=lambda *args, **kwargs: None)

    with pytest.raises(PermissionError):
        service.confirm_scan(1, user(2), complete_extraction_payload())


def test_confirm_scan_rejects_already_confirmed_scan():
    owner = user(1)
    scan = SimpleNamespace(id=1, uploaded_by_id=owner.id, is_confirmed=True, status='confirmed')
    service = InvoiceScanService(repo=FakeInvoiceRepo(scan=scan), audit_logger=lambda *args, **kwargs: None)

    with pytest.raises(InvoiceAlreadyConfirmed):
        service.confirm_scan(1, owner, complete_extraction_payload())


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


def complete_extraction_payload():
    return {
        'product_name': 'Wireless Mouse',
        'sku_code': 'WM-001',
        'quantity_received': 10,
        'unit_price': '21.25',
        'supplier_name': 'TechSupply',
    }
