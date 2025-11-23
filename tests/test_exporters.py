"""Tests for OpenTelemetry exporters."""

import pytest
from unittest.mock import Mock, MagicMock
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.metrics.export import MetricsData, ResourceMetrics, ScopeMetrics, Metric
from opentelemetry.sdk.resources import Resource

from rootsense.instrumentation.exporters import RootSenseSpanExporter, RootSenseMetricExporter

class TestRootSenseSpanExporter:
    """Test span exporter."""

    @pytest.fixture
    def error_collector(self):
        return Mock()

    @pytest.fixture
    def http_transport(self):
        return Mock()

    @pytest.fixture
    def exporter(self, error_collector, http_transport):
        return RootSenseSpanExporter(error_collector, http_transport)

    def test_export_spans(self, exporter, http_transport):
        """Test exporting spans."""
        class MockContext:
            trace_id = 12345678901234567890123456789012
            span_id = 1234567890123456
            
        class MockSpan:
            name = "test-span"
            context = MockContext()
            parent = None
            start_time = 1000
            end_time = 2000
            status = Mock()
            attributes = {"http.method": "GET"}
            events = []
            
        span = MockSpan()
        span.status.is_ok = False
        span.status.status_code = StatusCode.ERROR

        result = exporter.export([span])

        assert http_transport.send_events.called
        args = http_transport.send_events.call_args[0]
        events = args[0]
        assert len(events) == 1
        assert events[0]["type"] == "span"
        assert events[0]["name"] == "test-span"
        assert events[0]["operation_type"] == "http"

    def test_ignore_irrelevant_spans(self, exporter, http_transport):
        """Test that irrelevant successful spans are ignored."""
        span = Mock()
        span.name = "internal-op"
        span.status.is_ok = True
        span.attributes = {}  # No special attributes

        exporter.export([span])

        # Should not send event
        assert not http_transport.send_events.called

    def test_track_success(self, exporter, http_transport):
        """Test that successful operations trigger success signal."""
        class MockContext:
            trace_id = 12345678901234567890123456789012
            span_id = 1234567890123456
            
        class MockSpan:
            name = "GET /api/users"
            context = MockContext()
            status = Mock()
            attributes = {"http.method": "GET", "http.route": "/api/users"}
            parent = None
            start_time = 1000
            end_time = 2000
            events = []
            
        span = MockSpan()
        span.status.is_ok = True
        
        exporter.export([span])

        # Should send success signal
            
        assert http_transport.send_success_signal.called
        args = http_transport.send_success_signal.call_args
        fingerprint = args[0][0]
        assert "http:GET:/api/users" in fingerprint


class TestRootSenseMetricExporter:
    """Test metric exporter."""

    @pytest.fixture
    def http_transport(self):
        return Mock()

    @pytest.fixture
    def exporter(self, http_transport):
        return RootSenseMetricExporter(http_transport)

    def test_export_metrics(self, exporter, http_transport):
        """Test exporting metrics."""
        # Mock complex OTel metric structure
        metric_data = MagicMock()
        
        resource_metrics = MagicMock()
        resource_metrics.resource = Resource.create({"service.name": "test"})
        
        scope_metrics = MagicMock()
        
        metric = MagicMock()
        metric.name = "test_metric"
        metric.description = "Test metric"
        metric.unit = "1"
        
        data_point = MagicMock()
        data_point.attributes = {"label": "value"}
        data_point.start_time_unix_nano = 1000
        data_point.time_unix_nano = 2000
        data_point.value = 42
        
        metric.data.data_points = [data_point]
        scope_metrics.metrics = [metric]
        resource_metrics.scope_metrics = [scope_metrics]
        metric_data.resource_metrics = [resource_metrics]

        exporter.export(metric_data)

        assert http_transport.send_events.called
        events = http_transport.send_events.call_args[0][0]
        assert len(events) == 1
        assert events[0]["type"] == "metric"
        assert events[0]["name"] == "test_metric"
        assert events[0]["data_points"][0]["value"] == 42
