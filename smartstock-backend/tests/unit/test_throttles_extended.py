"""Tests for core/throttles.py — SAFE throttle classes."""

from unittest.mock import MagicMock

from django.test import TestCase

from core.throttles import SAFEAnonRateThrottle, SAFEUserRateThrottle


class SAFEAnonRateThrottleTest(TestCase):
    def test_options_always_allowed(self):
        throttle = SAFEAnonRateThrottle()
        request = MagicMock()
        request.method = 'OPTIONS'
        view = MagicMock()
        self.assertTrue(throttle.allow_request(request, view))


class SAFEUserRateThrottleTest(TestCase):
    def test_options_always_allowed(self):
        throttle = SAFEUserRateThrottle()
        request = MagicMock()
        request.method = 'OPTIONS'
        view = MagicMock()
        self.assertTrue(throttle.allow_request(request, view))
