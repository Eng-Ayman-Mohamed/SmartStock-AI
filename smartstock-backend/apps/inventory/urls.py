from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'skus', views.SKUViewSet, basename='sku')
router.register(r'stock-levels', views.StockLevelViewSet, basename='stock-level')
router.register(r'sales-records', views.SalesRecordViewSet, basename='sales-record')
router.register(r'suppliers', views.SupplierViewSet, basename='supplier')
router.register(r'categories', views.CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('stock/<int:product_id>/', views.StockAdjustView.as_view(), name='stock-adjust'),
]
