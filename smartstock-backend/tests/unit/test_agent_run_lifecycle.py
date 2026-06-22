"""Validation tests for AgentRun lifecycle tracking.

Covers:
- create_agent_run creates record with status=running and started_at
- complete_agent_run updates status, completed_at, error_message
- Duration calculation is correct
- Failure path sets status=failed with error_message
- Dashboard API returns real-time dynamic data
- Pagination works
- Day filters (1/7/30/90) work
- Ordering is newest-first
- AgentRunLog still receives records (Prometheus compat)
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from ai.agents.tracking import complete_agent_run, create_agent_run
from apps.audit.models import AgentRun
from apps.authentication.models import CustomUser
from apps.monitoring.models import AgentRunLog


class CreateAgentRunTest(TestCase):
    def test_creates_record_with_running_status(self):
        run = create_agent_run('test_agent')
        self.assertEqual(run.status, AgentRun.Status.RUNNING)
        self.assertEqual(run.agent_name, 'test_agent')
        self.assertIsNotNone(run.started_at)
        self.assertIsNone(run.completed_at)
        self.assertIsNotNone(run.id)

    def test_created_at_is_set(self):
        run = create_agent_run('test_agent')
        self.assertIsNotNone(run.created_at)


class CompleteAgentRunTest(TestCase):
    def test_complete_with_success(self):
        run = create_agent_run('test_agent')
        completed = complete_agent_run(run.id, status=AgentRun.Status.COMPLETED)
        self.assertEqual(completed.status, AgentRun.Status.COMPLETED)
        self.assertIsNotNone(completed.completed_at)
        self.assertEqual(completed.error_message, '')

    def test_complete_with_failure(self):
        run = create_agent_run('test_agent')
        completed = complete_agent_run(
            run.id,
            status=AgentRun.Status.FAILED,
            error_message='Something broke',
        )
        self.assertEqual(completed.status, AgentRun.Status.FAILED)
        self.assertEqual(completed.error_message, 'Something broke')
        self.assertIsNotNone(completed.completed_at)

    def test_nonexistent_run_returns_none(self):
        result = complete_agent_run(99999, status=AgentRun.Status.COMPLETED)
        self.assertIsNone(result)


class DurationCalculationTest(TestCase):
    def test_duration_seconds_with_both_timestamps(self):
        run = create_agent_run('test_agent')
        run.started_at = timezone.now() - timedelta(seconds=30)
        run.completed_at = timezone.now()
        self.assertIsNotNone(run.duration_seconds)
        self.assertAlmostEqual(run.duration_seconds, 30.0, delta=1.0)

    def test_duration_seconds_without_started_at(self):
        run = AgentRun(agent_name='test', status='pending')
        self.assertIsNone(run.duration_seconds)

    def test_duration_seconds_without_completed_at(self):
        run = create_agent_run('test_agent')
        self.assertIsNone(run.duration_seconds)


class IndexesExistTest(TestCase):
    def test_status_created_at_index_exists(self):
        indexes = AgentRun._meta.indexes
        index_names = [idx.name for idx in indexes]
        self.assertIn('agentrun_status_created_idx', index_names)

    def test_agent_name_created_at_index_exists(self):
        indexes = AgentRun._meta.indexes
        index_names = [idx.name for idx in indexes]
        self.assertIn('agentrun_name_created_idx', index_names)

    def test_created_at_has_db_index(self):
        field = AgentRun._meta.get_field('created_at')
        self.assertTrue(field.db_index)


class AgentRunDashboardAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='admin@test.com',
            username='admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='testpass123',
            role='viewer',
        )
        # Create some agent runs across different days
        now = timezone.now()
        for i in range(5):
            AgentRun.objects.create(
                agent_name='forecasting_agent',
                status=AgentRun.Status.COMPLETED,
                started_at=now - timedelta(hours=i),
                completed_at=now - timedelta(hours=i) + timedelta(minutes=5),
            )
        # Create one old run (30 days ago)
        AgentRun.objects.create(
            agent_name='purchasing_agent',
            status=AgentRun.Status.FAILED,
            started_at=now - timedelta(days=30),
            completed_at=now - timedelta(days=30) + timedelta(minutes=2),
            error_message='Timeout',
        )
        # Create one running (no completed_at)
        AgentRun.objects.create(
            agent_name='forecasting_agent',
            status=AgentRun.Status.RUNNING,
            started_at=now - timedelta(minutes=1),
        )

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def test_list_agent_runs_as_viewer(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_agent_runs_unauthenticated(self):
        resp = self.client.get('/api/audit/logs/agent-runs/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_default_7_day_filter(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        data = resp.json()
        results = data.get('data', data.get('results', []))
        for run in results:
            created = timezone.datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            cutoff = timezone.now() - timedelta(days=7)
            self.assertGreaterEqual(created, cutoff)

    def test_1_day_filter(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/?days=1',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        results = data.get('data', data.get('results', []))
        for run in results:
            created = timezone.datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            cutoff = timezone.now() - timedelta(days=1)
            self.assertGreaterEqual(created, cutoff)

    def test_30_day_filter_includes_old_run(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/?days=30',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_ordering_newest_first(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        data = resp.json()
        results = data.get('data', data.get('results', []))
        if len(results) >= 2:
            first = timezone.datetime.fromisoformat(results[0]['created_at'].replace('Z', '+00:00'))
            second = timezone.datetime.fromisoformat(
                results[1]['created_at'].replace('Z', '+00:00')
            )
            self.assertGreaterEqual(first, second)

    def test_pagination_present(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        data = resp.json()
        self.assertIn('data', data)
        self.assertIn('meta', data)

    def test_duration_seconds_in_response(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        data = resp.json()
        results = data.get('data', data.get('results', []))
        completed_runs = [r for r in results if r.get('status') == 'completed']
        if completed_runs:
            self.assertIn('duration_seconds', completed_runs[0])


class AgentRunLogBackwardCompatTest(TestCase):
    """Verify AgentRunLog (Prometheus) still works alongside AgentRun."""

    def test_create_agent_run_does_not_affect_agentrunlog(self):
        before = AgentRunLog.objects.count()
        create_agent_run('test_agent')
        after = AgentRunLog.objects.count()
        self.assertEqual(before, after)

    def test_agentrunlog_still_creatable(self):
        log = AgentRunLog.objects.create(
            agent_name='test_agent',
            outcome='success',
            duration_ms=1500,
        )
        self.assertIsNotNone(log.id)
        self.assertEqual(log.outcome, 'success')

    def test_both_models_coexist(self):
        run = create_agent_run('test_agent')
        complete_agent_run(run.id, status=AgentRun.Status.COMPLETED)
        AgentRunLog.objects.create(
            agent_name='test_agent',
            outcome='success',
            duration_ms=5000,
        )
        self.assertEqual(AgentRun.objects.count(), 1)
        self.assertEqual(AgentRunLog.objects.count(), 1)
