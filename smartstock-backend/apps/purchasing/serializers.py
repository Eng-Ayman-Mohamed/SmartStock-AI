from rest_framework import serializers

from apps.inventory.models import Supplier

from .models import PurchaseOrder


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.code', read_only=True)
    product_name = serializers.CharField(source='sku.product.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    def get_requested_by_name(self, obj):
        user = getattr(obj, 'requested_by', None)
        if user is None:
            return None
        return user.get_full_name() or user.email

    def get_approved_by_name(self, obj):
        user = getattr(obj, 'approved_by', None)
        if user is None:
            return None
        return user.get_full_name() or user.email

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ('requested_by', 'approved_by', 'status')
