from rest_framework import serializers
from .models import Product, SKU, StockLevel, SalesRecord ,Supplier


class SKUCompactSerializer(serializers.ModelSerializer):
    """Compact SKU serializer for nesting inside ProductSerializer."""
    class Meta:
        model = SKU
        fields = ('id', 'code', 'attributes', 'created_at')


class ProductSerializer(serializers.ModelSerializer):
    skus = SKUCompactSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductWriteSerializer(serializers.ModelSerializer):
    """Serializer for create/update — no nested SKUs."""
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'category')

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError('Product name must be at least 2 characters.')
        return value.strip()


class SKUSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SKU
        fields = '__all__'

    def validate_code(self, value):
        import re
        if not re.match(r'^[A-Za-z0-9-]+$', value):
            raise serializers.ValidationError('SKU code may only contain letters, digits, and hyphens.')
        return value.upper()


class StockLevelSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.code', read_only=True)
    product_name = serializers.CharField(source='sku.product.name', read_only=True)

    class Meta:
        model = StockLevel
        fields = '__all__'

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError('Quantity cannot be negative.')
        return value

    def validate_reorder_point(self, value):
        if value < 0:
            raise serializers.ValidationError('Reorder point cannot be negative.')
        return value


class SalesRecordSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.code', read_only=True)

    class Meta:
        model = SalesRecord
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

    def validate_contact_email(self, value):
        return value.lower().strip()

    def validate_default_lead_time_days(self, value):
        if value < 1:
            raise serializers.ValidationError('Lead time must be at least 1 day.')
        return value