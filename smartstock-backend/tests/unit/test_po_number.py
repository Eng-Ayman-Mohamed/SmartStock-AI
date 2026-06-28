from django.test import TestCase

from apps.purchasing.po_number import generate_po_number


class GeneratePoNumberTest(TestCase):
    def test_no_last_returns_first_of_year(self):
        result = generate_po_number(last_seq=None)
        self.assertRegex(result, r'^PO-\d{4}-001$')

    def test_with_last_increments_sequence(self):
        result = generate_po_number(last_seq=5)
        self.assertEqual(result, 'PO-2026-006')

    def test_increments_across_boundary(self):
        result = generate_po_number(last_seq=999)
        self.assertEqual(result, 'PO-2026-1000')

    def test_first_of_year(self):
        result = generate_po_number(last_seq=None)
        parts = result.split('-')
        self.assertEqual(parts[2], '001')
