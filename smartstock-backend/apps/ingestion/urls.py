from django.urls import path

from . import views

urlpatterns = [
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('documents/', views.DocumentListView.as_view(), name='document-list'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),
]
