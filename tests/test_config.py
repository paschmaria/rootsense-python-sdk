"""Tests for RootSense configuration."""

import pytest
import os
from unittest.mock import patch

from rootsense.config import Config, init, get_client


class TestConfig:
    """Test Config class."""

    def test_config_initialization(self):
        """Test basic config initialization."""
        config = Config(
            api_key="test_key",
            project_id="test_project"
        )
        
        assert config.api_key == "test_key"
        assert config.project_id == "test_project"
        assert config.environment == "production"
        assert config.debug is False

    def test_config_with_environment(self):
        """Test config with custom environment."""
        config = Config(
            api_key="test_key",
            project_id="test_project",
            environment="staging"
        )
        
        assert config.environment == "staging"

    def test_config_from_environment_variables(self):
        """Test config from environment variables."""
        with patch.dict(os.environ, {
            'ROOTSENSE_API_KEY': 'env_key',
            'ROOTSENSE_PROJECT_ID': 'env_project',
            'ROOTSENSE_ENVIRONMENT': 'development'
        }):
            config = Config.from_env()
            
            assert config.api_key == 'env_key'
            assert config.project_id == 'env_project'
            assert config.environment == 'development'

    def test_config_missing_required_fields(self):
        """Test config raises error without required fields."""
        with pytest.raises(ValueError):
            Config(api_key="test_key")  # Missing project_id


class TestGlobalConfig:
    """Test global configuration functions."""

    def test_init_creates_client(self):
        """Test init() creates global client."""
        with patch('rootsense.config.RootSenseClient'):
            client = init(
                api_key="test_key",
                project_id="test_project"
            )
            
            assert client is not None

    def test_get_client_returns_initialized_client(self):
        """Test get_client() returns the initialized client."""
        with patch('rootsense.config.RootSenseClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            
            init(api_key="test_key", project_id="test_project")
            client = get_client()
            
            assert client == mock_client

    def test_get_client_without_init(self):
        """Test get_client() returns None if not initialized."""
        # Reset global client
        import rootsense.config
        rootsense.config._client = None
        
        client = get_client()
        assert client is None
