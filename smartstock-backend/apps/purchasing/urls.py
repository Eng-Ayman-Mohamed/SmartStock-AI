from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'suppliers', views.SupplierViewSet)
router.register(r'orders', views.PurchaseOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
