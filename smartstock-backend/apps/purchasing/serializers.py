from rest_framework import serializers

from apps.inventory.models import Supplier

from .models import PurchaseOrder


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role not in ('manager', 'admin'):
                if data.get('contact_email'):
                    data['contact_email'] = '***@***.***'
                if data.get('contact_phone'):
                    data['contact_phone'] = '***-***-****'
        return data


class PurchaseOrderSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.code', read_only=True)
    product_name = serializers.CharField(source='sku.product.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    requested_by_name = serializers.CharField(
        source='requested_by.name', read_only=True, allow_null=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.name', read_only=True, allow_null=True
    )

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ('requested_by', 'approved_by', 'status')
