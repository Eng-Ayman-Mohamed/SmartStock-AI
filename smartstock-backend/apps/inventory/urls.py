from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'skus', views.SKUViewSet)
router.register(r'stock-levels', views.StockLevelViewSet)
router.register(r'sales-records', views.SalesRecordViewSet)
router.register(r'suppliers', views.SupplierViewSet)
urlpatterns = [
    path('', include(router.urls)),
]
