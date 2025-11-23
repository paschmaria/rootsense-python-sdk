"""Tests for error collection."""

import pytest
import time
from unittest.mock import Mock, MagicMock
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

    def test_record_request(self, collector):
        """Test request metric recording."""
        collector.record_request(
            method="GET",
            endpoint="/users",
            status_code=200,
            duration=0.123,
            service="api"
        )
        # Should not raise

    def test_active_request_tracking(self, collector):
        """Test active request tracking."""
        with collector.track_active_request("api"):
            pass
        # Should not raise

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

    def test_flush(self, collector, transport):
        """Test flushing pending events."""
        collector.capture_message("Test 1")
        collector.capture_message("Test 2")
        
        collector.flush(timeout=1)
        # Should have sent events
