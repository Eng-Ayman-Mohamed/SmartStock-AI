from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.monitoring.models import (
    AlertEvent,
    AlertRule,
    AlertStatus,
    DashboardBanner,
)

User = get_user_model()


class DashboardBannersViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass1234'
        )
        self.client.force_authenticate(user=self.user)

    def test_returns_active_banners(self):
        DashboardBanner.objects.create(
            title='Alert', message='msg', level='warning', dismissed=False
        )
        DashboardBanner.objects.create(
            title='Dismissed', message='msg', level='info', dismissed=True
        )
        response = self.client.get('/api/monitoring/banners/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_empty_banners(self):
        response = self.client.get('/api/monitoring/banners/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 0)

    def test_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/monitoring/banners/')
        self.assertEqual(response.status_code, 401)


class DismissBannerViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='manager', email='mgr@example.com', password='pass1234', role='manager'
        )
        self.client.force_authenticate(user=self.user)
        self.banner = DashboardBanner.objects.create(
            title='Alert', message='msg', level='warning', dismissed=False
        )

    def test_dismiss_banner(self):
        response = self.client.post(f'/api/monitoring/banners/{self.banner.id}/dismiss/')
        self.assertEqual(response.status_code, 200)
        self.banner.refresh_from_db()
        self.assertTrue(self.banner.dismissed)

    def test_dismiss_nonexistent_banner(self):
        response = self.client.post('/api/monitoring/banners/99999/dismiss/')
        self.assertEqual(response.status_code, 404)


class AlertEventsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser2', email='test2@example.com', password='pass1234'
        )
        self.client.force_authenticate(user=self.user)

    def test_returns_alert_events(self):
        rule = AlertRule.objects.create(name='Test Rule', metric_name='test', threshold=1.0)
        AlertEvent.objects.create(
            rule=rule, status=AlertStatus.FIRING, triggered_value=2.0, message='Alert!'
        )
        response = self.client.get('/api/monitoring/alerts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 1)

    def test_empty_events(self):
        response = self.client.get('/api/monitoring/alerts/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['data']), 0)


class EvaluationMetricsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin2', email='admin2@example.com', password='pass1234', role='admin'
        )
        self.client.force_authenticate(user=self.admin)

    @patch('ai.evaluation.metrics.log_scores_to_langfuse')
    @patch('ai.evaluation.metrics.evaluate_golden_dataset')
    def test_get_evaluation_metrics(self, mock_eval, mock_langfuse):
        mock_eval.return_value = {
            'precision_at_5': 0.85,
            'faithfulness': 0.90,
            'total_queries': 30,
            'successful_queries': 25,
        }
        response = self.client.get('/api/monitoring/evaluation/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['precision_at_5'], 0.85)
        self.assertEqual(response.data['data']['total_queries'], 30)

    def test_non_admin_forbidden(self):
        viewer = User.objects.create_user(
            username='viewer2', email='v2@example.com', password='pass1234', role='viewer'
        )
        self.client.force_authenticate(user=viewer)
        response = self.client.get('/api/monitoring/evaluation/')
        self.assertEqual(response.status_code, 403)
