"""Integration tests for Flask middleware."""

import pytest
from unittest.mock import Mock
import rootsense
from rootsense.config import Config

try:
    from flask import Flask
    from rootsense.middleware.flask import capture_flask_errors
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not installed")
class TestFlaskIntegration:
    """Test Flask integration."""

    @pytest.fixture
    def app(self):
        """Create Flask test app."""
        app = Flask(__name__)
        
        # Initialize RootSense
        config = Config(
            api_key="test-key",
            project_id="test-project",
            debug=True
        )
        client = rootsense.RootSenseClient(config)
        
        # Add RootSense integration
        capture_flask_errors(app, client)
        
        @app.route("/")
        def index():
            return "OK", 200
        
        @app.route("/error")
        def error():
            raise ValueError("Test error")
        
        return app

    def test_successful_request(self, app):
        """Test that successful requests are tracked."""
        with app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200

    def test_error_capture(self, app):
        """Test that errors are captured."""
        with app.test_client() as client:
            with pytest.raises(ValueError):
                client.get("/error")
