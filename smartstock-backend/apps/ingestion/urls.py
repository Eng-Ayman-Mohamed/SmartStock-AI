from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')

urlpatterns = [
    path('rag-query/', views.RAGQueryView.as_view(), name='rag-query'),
    path('transcribe/', views.TranscribeView.as_view(), name='transcribe'),
    path('invoice-scan/', views.InvoiceScanView.as_view(), name='invoice-scan'),
    path(
        'invoice-scan/confirm/', views.InvoiceScanConfirmView.as_view(), name='invoice-scan-confirm'
    ),
    path(
        'invoice-scan/<int:scan_id>/reject/',
        views.InvoiceScanRejectView.as_view(),
        name='invoice-scan-reject',
    ),
    path('', include(router.urls)),
]
