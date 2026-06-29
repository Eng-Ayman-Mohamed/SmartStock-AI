import pytest
from django.urls import reverse
from rest_framework import status

from apps.notifications.models import Notification, UserNotification


@pytest.fixture
def notification(db, user):
    notif = Notification.objects.create(
        type='monitoring',
        severity='warning',
        title='Test Alert',
        message='Test message',
    )
    UserNotification.objects.create(user=user, notification=notif)
    return notif


@pytest.mark.django_db
class TestNotificationViewSet:
    def test_list_notifications(self, api_client, auth_headers, notification):
        url = reverse('notification-list')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_list_notifications_empty(self, api_client, auth_headers):
        url = reverse('notification-list')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_list_notifications_filter_by_type(self, api_client, auth_headers, notification):
        url = reverse('notification-list')
        response = api_client.get(url, {'type': 'monitoring'}, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_list_notifications_filter_by_type_no_match(
        self, api_client, auth_headers, notification
    ):
        url = reverse('notification-list')
        response = api_client.get(url, {'type': 'forecast'}, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_list_notifications_filter_by_severity(self, api_client, auth_headers, notification):
        url = reverse('notification-list')
        response = api_client.get(url, {'severity': 'warning'}, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_retrieve_notification(self, api_client, auth_headers, notification):
        url = reverse('notification-detail', args=[notification.id])
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Test Alert'

    def test_mark_read(self, api_client, auth_headers, notification, user):
        url = reverse('notification-mark-read', args=[notification.id])
        response = api_client.post(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert UserNotification.objects.filter(
            user=user, notification=notification, is_read=True
        ).exists()

    def test_mark_read_idempotent(self, api_client, auth_headers, notification, user):
        UserNotification.objects.filter(user=user, notification=notification).update(is_read=True)
        url = reverse('notification-mark-read', args=[notification.id])
        response = api_client.post(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_mark_all_read(self, api_client, auth_headers, notification, user):
        url = reverse('notification-mark-all-read')
        response = api_client.post(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_mark_all_read_updates_unread(self, api_client, auth_headers, notification, user):
        UserNotification.objects.filter(user=user, notification=notification).update(is_read=False)
        url = reverse('notification-mark-all-read')
        response = api_client.post(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        user_notif = UserNotification.objects.get(user=user, notification=notification)
        assert user_notif.is_read is True

    def test_dismiss(self, api_client, auth_headers, notification, user):
        url = reverse('notification-dismiss', args=[notification.id])
        response = api_client.post(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert not UserNotification.objects.filter(user=user, notification=notification).exists()

    def test_dismiss_no_existing_user_notification(self, api_client, auth_headers, notification):
        url = reverse('notification-dismiss', args=[notification.id])
        response = api_client.post(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUnreadCountView:
    def test_unread_count(self, api_client, auth_headers, notification, user):
        UserNotification.objects.filter(user=user, notification=notification).update(is_read=False)
        url = reverse('unread-count')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_unread_count_zero(self, api_client, auth_headers):
        url = reverse('unread-count')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_unread_count_excludes_read(self, api_client, auth_headers, notification, user):
        UserNotification.objects.filter(user=user, notification=notification).update(is_read=True)
        url = reverse('unread-count')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_unread_count_multiple_notifications(self, api_client, auth_headers, user):
        n1 = Notification.objects.create(type='monitoring', severity='info', title='N1')
        n2 = Notification.objects.create(type='forecast', severity='critical', title='N2')
        UserNotification.objects.create(user=user, notification=n1, is_read=False)
        UserNotification.objects.create(user=user, notification=n2, is_read=False)
        url = reverse('unread-count')
        response = api_client.get(url, **auth_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
