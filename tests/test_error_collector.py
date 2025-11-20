"""Tests for error collector."""

import pytest
from unittest.mock import Mock, patch
import hashlib

from rootsense.collectors.error_collector import ErrorCollector


class TestErrorCollector:
    """Test ErrorCollector functionality."""

    def test_capture_exception(self, mock_config, mock_http_transport, sample_exception):
        """Test capturing an exception."""
        collector = ErrorCollector(mock_config, mock_http_transport)
        
        event_id = collector.capture_exception(sample_exception)
        
        assert event_id is not None
        assert mock_http_transport.send_event.called

    def test_capture_message(self, mock_config, mock_http_transport):
        """Test capturing a message."""
        collector = ErrorCollector(mock_config, mock_http_transport)
        
        event_id = collector.capture_message("Test message", level="warning")
        
        assert event_id is not None
        assert mock_http_transport.send_event.called

    def test_fingerprint_generation(self, mock_config, mock_http_transport):
        """Test that fingerprints are generated consistently."""
        collector = ErrorCollector(mock_config, mock_http_transport)
        
        # Create two identical exceptions
        exceptions = []
        for _ in range(2):
            try:
                raise ValueError("Same error")
            except ValueError as e:
                exceptions.append(e)
        
        event1 = collector._build_event_data(exceptions[0], {})
        event2 = collector._build_event_data(exceptions[1], {})
        
        assert event1.get('fingerprint') == event2.get('fingerprint')

    def test_error_buffering(self, mock_config, mock_http_transport):
        """Test that errors are buffered before sending."""
        collector = ErrorCollector(mock_config, mock_http_transport)
        collector.start()
        
        # Capture multiple errors
        for i in range(5):
            try:
                raise ValueError(f"Error {i}")
            except ValueError as e:
                collector.capture_exception(e)
        
        # Buffer should have events
        assert len(collector._buffer) > 0

    def test_flush(self, mock_config, mock_http_transport):
        """Test flushing the buffer."""
        collector = ErrorCollector(mock_config, mock_http_transport)
        collector.start()
        
        # Add some events to buffer
        for i in range(3):
            try:
                raise ValueError(f"Error {i}")
            except ValueError as e:
                collector.capture_exception(e)
        
        # Flush
        collector.flush(timeout=1)
        
        # Buffer should be empty after flush
        assert len(collector._buffer) == 0
