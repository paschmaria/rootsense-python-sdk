"""Integration tests for FastAPI middleware."""

import pytest
from unittest.mock import Mock
import rootsense
from rootsense.config import Config

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from rootsense.middleware.fastapi import capture_fastapi_errors
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")
class TestFastAPIIntegration:
    """Test FastAPI integration."""

    @pytest.fixture
    def app(self):
        """Create FastAPI test app."""
        app = FastAPI()
        
        # Initialize RootSense
        config = Config(
            api_key="test-key",
            project_id="test-project",
            debug=True
        )
        client = rootsense.RootSenseClient(config)
        
        # Add RootSense integration
        capture_fastapi_errors(app, client)
        
        @app.get("/")
        async def index():
            return {"status": "ok"}
        
        @app.get("/error")
        async def error():
            raise ValueError("Test error")
        
        return app

    def test_successful_request(self, app):
        """Test that successful requests are tracked."""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200

    def test_error_capture(self, app):
        """Test that errors are captured."""
        client = TestClient(app)
        with pytest.raises(ValueError):
            client.get("/error")
