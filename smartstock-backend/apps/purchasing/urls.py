from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'orders', views.PurchaseOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
