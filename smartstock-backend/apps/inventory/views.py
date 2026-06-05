from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, SKU, StockLevel
from .serializers import ProductSerializer, SKUSerializer, StockLevelSerializer
from .services import InventoryService


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class SKUViewSet(viewsets.ModelViewSet):
    queryset = SKU.objects.all()
    serializer_class = SKUSerializer


class StockLevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockLevel.objects.select_related('sku__product').all()
    serializer_class = StockLevelSerializer

    @action(detail=False)
    def low_stock(self, request):
        items = InventoryService().get_low_stock_items()
        return Response(items)
