"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock

from rootsense.config import Config
from rootsense.client import RootSenseClient


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return Config(
        api_key="test_api_key",
        project_id="test_project_id",
        environment="test",
        debug=True,
        enable_prometheus=False,
        backend_url="https://api.test.rootsense.ai"
    )


@pytest.fixture
def mock_client(mock_config):
    """Create a mock RootSense client."""
    client = Mock(spec=RootSenseClient)
    client.config = mock_config
    client.capture_exception = Mock(return_value="event-123")
    client.capture_message = Mock(return_value="event-456")
    return client


@pytest.fixture
def mock_http_transport(mock_config):
    """Create a mock HTTP transport."""
    transport = Mock()
    transport.send_event = Mock(return_value=True)
    transport.send_batch = Mock(return_value=True)
    return transport


@pytest.fixture
def sample_exception():
    """Create a sample exception for testing."""
    try:
        raise ValueError("Test error message")
    except ValueError as e:
        return e


@pytest.fixture
def sample_context():
    """Create sample context data."""
    return {
        "user": {
            "id": "user123",
            "email": "test@example.com",
            "username": "testuser"
        },
        "tags": {
            "environment": "test",
            "version": "1.0.0"
        },
        "extra": {
            "request_id": "req-123",
            "session_id": "sess-456"
        }
    }
