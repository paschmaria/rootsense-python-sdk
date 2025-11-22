"""Tests for configuration parsing."""

import pytest
import os
from rootsense.config import Config


class TestConfig:
    """Test configuration parsing."""

    def test_separate_params(self):
        """Test initialization with separate parameters."""
        config = Config(
            api_key="test-key",
            project_id="test-project",
            backend_url="https://api.test.com"
        )
        
        assert config.api_key == "test-key"
        assert config.project_id == "test-project"
        assert config.backend_url == "https://api.test.com"
        assert config.events_endpoint == "https://api.test.com/v1/projects/test-project/events"

    def test_connection_string(self):
        """Test initialization with connection string."""
        config = Config(
            connection_string="rootsense://test-key@api.test.com/test-project"
        )
        
        assert config.api_key == "test-key"
        assert config.project_id == "test-project"
        assert config.backend_url == "https://api.test.com"

    def test_env_vars(self, monkeypatch):
        """Test initialization from environment variables."""
        monkeypatch.setenv("ROOTSENSE_API_KEY", "env-key")
        monkeypatch.setenv("ROOTSENSE_PROJECT_ID", "env-project")
        monkeypatch.setenv("ROOTSENSE_BACKEND_URL", "https://api.env.com")
        
        config = Config()
        
        assert config.api_key == "env-key"
        assert config.project_id == "env-project"
        assert config.backend_url == "https://api.env.com"

    def test_missing_api_key(self):
        """Test that missing API key raises error."""
        with pytest.raises(ValueError, match="api_key is required"):
            Config(project_id="test-project")

    def test_missing_project_id(self):
        """Test that missing project ID raises error."""
        with pytest.raises(ValueError, match="project_id is required"):
            Config(api_key="test-key")

    def test_invalid_connection_string(self):
        """Test that invalid connection string raises error."""
        with pytest.raises(ValueError, match="Invalid connection string format"):
            Config(connection_string="invalid-format")

    def test_defaults(self):
        """Test default configuration values."""
        config = Config(api_key="test-key", project_id="test-project")
        
        assert config.environment == "production"
        assert config.sample_rate == 1.0
        assert config.debug is False
        assert config.sanitize_pii is True
        assert config.max_breadcrumbs == 100
        assert config.buffer_size == 1000

    def test_custom_options(self):
        """Test custom configuration options."""
        config = Config(
            api_key="test-key",
            project_id="test-project",
            environment="staging",
            sample_rate=0.5,
            debug=True,
            sanitize_pii=False,
            max_breadcrumbs=50,
            buffer_size=500
        )
        
        assert config.environment == "staging"
        assert config.sample_rate == 0.5
        assert config.debug is True
        assert config.sanitize_pii is False
        assert config.max_breadcrumbs == 50
        assert config.buffer_size == 500
