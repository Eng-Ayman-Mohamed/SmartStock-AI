from unittest.mock import MagicMock

from django.test import RequestFactory, TestCase

from apps.inventory.models import Supplier
from apps.purchasing.serializers import SupplierSerializer


class SupplierSerializerMaskingTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_contact_phone_masked_for_viewer(self):
        supplier = Supplier(
            name='Mask Test Supplier',
            contact_email='test@example.com',
            contact_phone='555-123-4567',
        )
        request = self.factory.get('/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.role = 'viewer'

        serializer = SupplierSerializer(supplier, context={'request': request})
        data = serializer.data

        self.assertEqual(data['contact_phone'], '***-***-****')
        self.assertEqual(data['contact_email'], '***@***.***')

    def test_contact_phone_not_masked_for_admin(self):
        supplier = Supplier(
            name='Admin Supplier',
            contact_email='admin@example.com',
            contact_phone='555-999-8888',
        )
        request = self.factory.get('/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.role = 'admin'

        serializer = SupplierSerializer(supplier, context={'request': request})
        data = serializer.data

        self.assertEqual(data['contact_phone'], '555-999-8888')
        self.assertEqual(data['contact_email'], 'admin@example.com')

    def test_contact_phone_not_masked_for_manager(self):
        supplier = Supplier(
            name='Manager Supplier',
            contact_email='mgr@example.com',
            contact_phone='555-777-6666',
        )
        request = self.factory.get('/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.role = 'manager'

        serializer = SupplierSerializer(supplier, context={'request': request})
        data = serializer.data

        self.assertEqual(data['contact_phone'], '555-777-6666')

    def test_no_masking_when_no_contact_fields(self):
        supplier = Supplier(
            name='No Contact Supplier',
            contact_email='nocontact@example.com',
            contact_phone=None,
        )
        request = self.factory.get('/')
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.role = 'viewer'

        serializer = SupplierSerializer(supplier, context={'request': request})
        data = serializer.data

        self.assertEqual(data['contact_email'], '***@***.***')
        self.assertIsNone(data['contact_phone'])
