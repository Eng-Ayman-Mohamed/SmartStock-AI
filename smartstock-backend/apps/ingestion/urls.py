from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')

urlpatterns = [
    path('rag-query/', views.RAGQueryView.as_view(), name='rag-query'),
    path('transcribe/', views.TranscribeView.as_view(), name='transcribe'),
    path('', include(router.urls)),
]
