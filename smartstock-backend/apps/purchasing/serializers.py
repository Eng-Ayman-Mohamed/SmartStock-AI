from rest_framework import serializers

from .models import PurchaseOrder, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ('requested_by', 'approved_by', 'status')
