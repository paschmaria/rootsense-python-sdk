"""Tests for RootSense client."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from rootsense.client import RootSenseClient
from rootsense.config import Config


class TestRootSenseClient:
    """Test RootSenseClient functionality."""

    def test_client_initialization(self, mock_config):
        """Test client initializes correctly."""
        with patch('rootsense.client.HttpTransport'), \
             patch('rootsense.client.WebSocketTransport'), \
             patch('rootsense.client.ErrorCollector'):
            
            client = RootSenseClient(mock_config)
            
            assert client.config == mock_config
            assert client._initialized is True

    def test_client_with_prometheus_enabled(self):
        """Test client initializes with Prometheus collector when enabled."""
        config = Config(
            api_key="test_key",
            project_id="test_project",
            enable_prometheus=True
        )
        
        with patch('rootsense.client.HttpTransport'), \
             patch('rootsense.client.WebSocketTransport'), \
             patch('rootsense.client.ErrorCollector'), \
             patch('rootsense.client.PrometheusCollector') as mock_prom:
            
            client = RootSenseClient(config)
            
            assert mock_prom.called
            assert client.prometheus_collector is not None

    def test_client_without_prometheus(self, mock_config):
        """Test client works without Prometheus collector."""
        with patch('rootsense.client.HttpTransport'), \
             patch('rootsense.client.WebSocketTransport'), \
             patch('rootsense.client.ErrorCollector'):
            
            client = RootSenseClient(mock_config)
            
            assert client.prometheus_collector is None

    def test_capture_exception(self, mock_config, sample_exception):
        """Test capturing exceptions."""
        with patch('rootsense.client.HttpTransport'), \
             patch('rootsense.client.WebSocketTransport'), \
             patch('rootsense.client.ErrorCollector') as mock_collector:
            
            mock_collector.return_value.capture_exception = Mock(return_value="event-123")
            
            client = RootSenseClient(mock_config)
            event_id = client.capture_exception(sample_exception)
            
            assert event_id == "event-123"
            mock_collector.return_value.capture_exception.assert_called_once()

    def test_capture_message(self, mock_config):
        """Test capturing messages."""
        with patch('rootsense.client.HttpTransport'), \
             patch('rootsense.client.WebSocketTransport'), \
             patch('rootsense.client.ErrorCollector') as mock_collector:
            
            mock_collector.return_value.capture_message = Mock(return_value="event-456")
            
            client = RootSenseClient(mock_config)
            event_id = client.capture_message("Test message", level="error")
            
            assert event_id == "event-456"
            mock_collector.return_value.capture_message.assert_called_once()

    def test_client_close(self, mock_config):
        """Test client cleanup."""
        with patch('rootsense.client.HttpTransport'), \
             patch('rootsense.client.WebSocketTransport') as mock_ws, \
             patch('rootsense.client.ErrorCollector') as mock_collector:
            
            mock_collector.return_value.flush = Mock()
            mock_ws.return_value.close = Mock()
            
            client = RootSenseClient(mock_config)
            client.close()
            
            assert client._initialized is False
            mock_collector.return_value.flush.assert_called_once()
            mock_ws.return_value.close.assert_called_once()

    def test_context_manager(self, mock_config):
        """Test client works as context manager."""
        with patch('rootsense.client.HttpTransport'), \
             patch('rootsense.client.WebSocketTransport'), \
             patch('rootsense.client.ErrorCollector'):
            
            with RootSenseClient(mock_config) as client:
                assert client._initialized is True
            
            assert client._initialized is False
