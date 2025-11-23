"""Tests for HTTP transport."""

import pytest
from unittest.mock import Mock, patch
from rootsense.transport.http_transport import HttpTransport
from rootsense.config import Config
import requests

class TestHttpTransport:
    """Test HTTP transport functionality."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config(
            api_key="test-key",
            project_id="test-project",
            backend_url="https://api.test.com"
        )

    @pytest.fixture
    def transport(self, config):
        """Create transport instance."""
        return HttpTransport(config)

    def test_init(self, transport):
        """Test initialization."""
        assert transport.session.headers["X-API-Key"] == "test-key"
        assert transport.session.headers["Content-Type"] == "application/json"

    @patch("requests.Session.post")
    def test_send_events_success(self, mock_post, transport):
        """Test successful event sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        events = [{"event_id": "1"}]
        result = transport.send_events(events)

        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.test.com/events/batch"
        assert kwargs["json"]["events"] == events

    @patch("requests.Session.post")
    def test_send_events_client_error(self, mock_post, transport):
        """Test client error (no retry)."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        result = transport.send_events([{"event_id": "1"}])

        assert result is False
        # Should not retry on 4xx
        assert mock_post.call_count == 1

    @patch("requests.Session.post")
    def test_send_events_server_error_retry(self, mock_post, transport):
        """Test server error with retry."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Mock sleep to speed up test
        with patch("time.sleep"):
            result = transport.send_events([{"event_id": "1"}])

        assert result is False
        # Should retry 3 times
        assert mock_post.call_count == 3

    @patch("requests.Session.post")
    def test_send_events_exception_retry(self, mock_post, transport):
        """Test exception with retry."""
        mock_post.side_effect = requests.RequestException("Connection error")

        # Mock sleep
        with patch("time.sleep"):
            result = transport.send_events([{"event_id": "1"}])

        assert result is False
        assert mock_post.call_count == 3

    @patch("requests.Session.post")
    def test_send_events_success_after_retry(self, mock_post, transport):
        """Test success after retry."""
        fail_response = Mock()
        fail_response.status_code = 500
        
        success_response = Mock()
        success_response.status_code = 200

        # Fail twice, then succeed
        mock_post.side_effect = [fail_response, fail_response, success_response]

        with patch("time.sleep"):
            result = transport.send_events([{"event_id": "1"}])

        assert result is True
        assert mock_post.call_count == 3

    @patch("requests.Session.post")
    def test_send_success_signal(self, mock_post, transport):
        """Test sending success signal."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        fingerprint = "test-fingerprint"
        context = {"method": "GET"}
        
        result = transport.send_success_signal(fingerprint, context)

        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.test.com/events/success"
        assert kwargs["json"]["fingerprint"] == fingerprint
        assert kwargs["json"]["context"] == context
