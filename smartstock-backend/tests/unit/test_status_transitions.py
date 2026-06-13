from unittest.mock import MagicMock, patch
from django.test import TestCase
from apps.purchasing.services import PurchasingService
from core.exceptions import IllegalPOTransitionError


class StatusTransitionValidationTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)

    def test_legal_transition_succeeds(self):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        self.repo.update.return_value = MagicMock(status='pending_approval', id=1)
        result = self.service.transition_po_status(po_id=1, new_status='pending_approval')
        self.assertEqual(result.status, 'pending_approval')

    def test_illegal_transition_raises_exception(self):
        self.repo.get_by_id.return_value = MagicMock(status='confirmed')
        with self.assertRaises(IllegalPOTransitionError):
            self.service.transition_po_status(po_id=1, new_status='draft')

    def test_confirmed_to_draft_raises_exception(self):
        self.repo.get_by_id.return_value = MagicMock(status='confirmed')
        with self.assertRaises(IllegalPOTransitionError):
            self.service.transition_po_status(po_id=1, new_status='draft')

    def test_draft_to_sent_raises_exception(self):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        with self.assertRaises(IllegalPOTransitionError):
            self.service.transition_po_status(po_id=1, new_status='sent')

    def test_unknown_status_raises_exception(self):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        with self.assertRaises(IllegalPOTransitionError):
            self.service.transition_po_status(po_id=1, new_status='bogus')

    def test_transition_to_confirmed_sets_confirmed_at(self):
        self.repo.get_by_id.return_value = MagicMock(status='sent')
        self.repo.update.return_value = MagicMock(status='confirmed')
        with patch('apps.purchasing.services.timezone') as mock_tz:
            mock_tz.now.return_value = MagicMock()
            self.service.transition_po_status(po_id=1, new_status='confirmed')
            update_call = self.repo.update.call_args[0][1]
            self.assertIn('confirmed_at', update_call)

    def test_transition_creates_audit_log(self):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        self.repo.update.return_value = MagicMock(status='pending_approval')
        with patch('apps.purchasing.services.AuditLog') as mock_audit:
            self.service.transition_po_status(po_id=1, new_status='pending_approval')
            mock_audit.objects.create.assert_called_once()
