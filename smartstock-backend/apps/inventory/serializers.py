import re

from rest_framework import serializers
from .models import Product, SKU, StockLevel, SalesRecord, Supplier, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class SKUCompactSerializer(serializers.ModelSerializer):
    """Compact SKU serializer for nesting inside ProductSerializer."""
    class Meta:
        model = SKU
        fields = ('id', 'code', 'attributes', 'created_at')


class ProductSerializer(serializers.ModelSerializer):
    skus = SKUCompactSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductWriteSerializer(serializers.ModelSerializer):
    """Serializer for create/update — no nested SKUs."""
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'category', 'supplier',
            'unit_price', 'unit_of_measure', 'reorder_point', 'safety_stock',
        )
        read_only_fields = ('id',)

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
        if not re.match(r'^[A-Za-z0-9-]+$', value):
            raise serializers.ValidationError('SKU code may only contain letters, digits, and hyphens.')
        return value.upper()


class StockLevelSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.code', read_only=True)
    product_name = serializers.CharField(source='sku.product.name', read_only=True)

    quantity = serializers.IntegerField(source='quantity_on_hand', read_only=True)
    quantity_available = serializers.IntegerField(read_only=True)

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

    # Added
    def validate_reorder_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Reorder quantity must be at least 1.'
            )
        return value


class SalesRecordSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.code', read_only=True)

    class Meta:
        model = SalesRecord
        fields = '__all__'

    def validate_quantity_sold(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Quantity sold cannot be negative.'
            )
        return value

class SupplierSerializer(serializers.ModelSerializer):

    name = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'Supplier name is required.',
            'blank': 'Supplier name cannot be blank.',
        }
    )

    contact_email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Contact email is required.',
        }
    )

    class Meta:
        model = Supplier
        fields = '__all__'

    def validate_contact_email(self, value):
        return value.lower().strip()

    def validate_default_lead_time_days(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Lead time must be at least 1 day.'
            )

        if value > 365:
            raise serializers.ValidationError(
                'Lead time cannot exceed 365 days.'
            )

        return value
