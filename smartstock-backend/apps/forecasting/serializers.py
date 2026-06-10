from rest_framework import serializers

from .models import ForecastResult


class ForecastResultSerializer(serializers.ModelSerializer):
    sku_code = serializers.CharField(source='sku.code', read_only=True)
    product_name = serializers.CharField(source='sku.product.name', read_only=True)

    class Meta:
        model = ForecastResult
        fields = '__all__'
