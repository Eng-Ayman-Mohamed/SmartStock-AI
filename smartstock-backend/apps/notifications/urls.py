from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('unread-count/', views.UnreadCountView.as_view(), name='unread-count'),
    path('', include(router.urls)),
]
