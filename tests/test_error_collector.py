"""Tests for error collection."""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from rootsense.config import Config
from rootsense.collectors.error_collector import ErrorCollector
from rootsense.context import set_context, set_user, set_tag


class TestErrorCollector:
    """Test error collector functionality."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config(
            api_key="test-key",
            project_id="test-project",
            debug=True
        )

    @pytest.fixture
    def transport(self):
        """Create mock transport."""
        return Mock()

    @pytest.fixture
    def collector(self, config, transport):
        """Create error collector."""
        collector = ErrorCollector(config, transport)
        collector.start()
        yield collector
        collector.stop()

    def test_capture_exception(self, collector):
        """Test exception capture."""
        try:
            1 / 0
        except Exception as e:
            event_id = collector.capture_exception(e)
            
        assert event_id is not None
        time.sleep(0.1)  # Allow worker to process

    def test_capture_exception_with_context(self, collector):
        """Test exception capture with context."""
        context = {
            "service": "api",
            "endpoint": "/users",
            "method": "POST"
        }
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            event_id = collector.capture_exception(e, context=context)
            
        assert event_id is not None

    def test_capture_message(self, collector):
        """Test message capture."""
        event_id = collector.capture_message("Test message", level="info")
        assert event_id is not None

    def test_event_enrichment(self, collector):
        """Test that events are enriched with context."""
        # Set context
        set_user({"id": "123", "email": "test@example.com"})
        set_tag("environment", "test")
        set_context("request", {"url": "/test"})
        
        try:
            raise ValueError("Test")
        except Exception as e:
            event_id = collector.capture_exception(e)
            
        assert event_id is not None
        time.sleep(0.1)

    def test_fingerprint_generation(self, collector):
        """Test fingerprint generation for grouping."""
        context1 = {"service": "api", "endpoint": "/users"}
        context2 = {"service": "api", "endpoint": "/users"}
        context3 = {"service": "api", "endpoint": "/posts"}
        
        try:
            raise ValueError("Test")
        except Exception as e:
            fp1 = collector._generate_fingerprint(e, context1)
            fp2 = collector._generate_fingerprint(e, context2)
            fp3 = collector._generate_fingerprint(e, context3)
        
        # Same error+service+endpoint should have same fingerprint
        assert fp1 == fp2
        # Different endpoint should have different fingerprint
        assert fp1 != fp3



    def test_buffer_overflow(self, config, transport):
        """Test behavior when buffer is full."""
        small_config = Config(
            api_key="test-key",
            project_id="test-project",
            buffer_size=2
        )
        collector = ErrorCollector(small_config, transport)
        
        # Fill buffer
        event_id1 = collector.capture_message("Message 1")
        event_id2 = collector.capture_message("Message 2")
        event_id3 = collector.capture_message("Message 3")  # Should be dropped
        
        assert event_id1 is not None
        assert event_id2 is not None
        # Third should be None due to full buffer

        collector.flush(timeout=1)
        # Should have sent events

    @patch("rootsense.collectors.error_collector.REGISTRY")
    @patch("rootsense.collectors.error_collector.PROMETHEUS_AVAILABLE", True)
    def test_collect_prometheus_metrics(self, mock_registry, collector):
        """Test Prometheus metric collection."""
        # Ensure metrics are enabled
        collector._metrics_enabled = True
        # Mock metric family
        mock_metric = MagicMock()
        mock_metric.name = "test_metric"
        mock_metric.documentation = "Test doc"
        mock_metric.unit = "1"
        
        mock_sample = MagicMock()
        mock_sample.name = "test_metric"
        mock_sample.labels = {"label": "value"}
        mock_sample.value = 10.0
        
        mock_metric.samples = [mock_sample]
        
        mock_registry.collect.return_value = [mock_metric]
        
        # Force metric collection
        events = collector._collect_prometheus_metrics()
        
        assert len(events) == 1
        assert events[0]["type"] == "metric"
        assert events[0]["name"] == "test_metric"
        assert events[0]["data_points"][0]["value"] == 10.0
        assert events[0]["data_points"][0]["attributes"]["label"] == "value"

    @patch("rootsense.collectors.error_collector.REGISTRY")
    @patch("rootsense.collectors.error_collector.PROMETHEUS_AVAILABLE", True)
    def test_metrics_on_stop(self, mock_registry, collector, transport):
        """Test that metrics are collected when stopping."""
        collector._metrics_enabled = True
        collector.batch_send_duration = MagicMock()
        
        # Setup mock metrics
        mock_metric = MagicMock()
        mock_metric.name = "test_metric"
        mock_metric.samples = [MagicMock(value=1.0, labels={})]
        mock_registry.collect.return_value = [mock_metric]
        
        time.sleep(0.1)
        collector.stop()
        
        # Should have sent batch with metrics
        assert transport.send_events.called
        batch = transport.send_events.call_args[0][0]
        
        # Check for metric event in batch
        has_metric = any(e.get("type") == "metric" for e in batch)
        assert has_metric
