"""Flask integration for RootSense."""

import time
import logging
from functools import wraps
from typing import Optional

try:
    from flask import Flask, request, g
    from werkzeug.exceptions import HTTPException
except ImportError:
    raise ImportError("Flask is not installed. Install with: pip install rootsense[flask]")

from rootsense.config import get_client
from rootsense.context import set_context, set_tag

logger = logging.getLogger(__name__)


class FlaskIntegration:
    """Flask integration for automatic error tracking and performance monitoring."""

    def __init__(self, app: Optional[Flask] = None, client=None):
        self.client = client
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize the Flask app with RootSense.
        
        Args:
            app: Flask application instance
        """
        if self.client is None:
            self.client = get_client()

        if self.client is None:
            logger.warning("RootSense not initialized. Call rootsense.init() first.")
            return

        # Register request handlers
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

        # Register error handler
        app.register_error_handler(Exception, self._handle_exception)

        logger.info("RootSense Flask integration initialized")

    def _before_request(self):
        """Called before each request."""
        g._rootsense_start_time = time.time()
        
        # Set request context
        set_context("request", {
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "remote_addr": request.remote_addr,
        })
        
        # Set user context if available
        if hasattr(g, "user") and g.user:
            from rootsense.context import set_user
            set_user({
                "id": getattr(g.user, "id", None),
                "email": getattr(g.user, "email", None),
                "username": getattr(g.user, "username", None),
            })

    def _after_request(self, response):
        """Called after each request.
        
        Args:
            response: Flask response object
            
        Returns:
            The response object
        """
        if hasattr(g, "_rootsense_start_time"):
            duration = time.time() - g._rootsense_start_time
            
            # Track performance metrics
            set_tag("http.status_code", response.status_code)
            set_tag("http.response_time", duration)
            
            # Track successful request (for auto-resolution)
            if 200 <= response.status_code < 400:
                set_tag("request.success", True)

        return response

    def _teardown_request(self, exc=None):
        """Called when request context is torn down.
        
        Args:
            exc: Exception if one occurred, None otherwise
        """
        if exc is not None and self.client:
            self.client.capture_exception(exc)

    def _handle_exception(self, exc):
        """Handle exceptions that occur during request processing.
        
        Args:
            exc: The exception that occurred
            
        Raises:
            The original exception
        """
        if self.client:
            # Capture the exception
            self.client.capture_exception(exc)

        # Re-raise the exception so Flask can handle it
        if isinstance(exc, HTTPException):
            return exc
        raise exc


def capture_flask_errors(app: Flask, client=None):
    """Convenience function to add RootSense to a Flask app.
    
    Args:
        app: Flask application instance
        client: Optional RootSense client instance
        
    Returns:
        FlaskIntegration instance
        
    Example:
        >>> from flask import Flask
        >>> import rootsense
        >>> from rootsense.integrations.flask import capture_flask_errors
        >>> 
        >>> rootsense.init(api_key="your-api-key", project_id="your-project-id")
        >>> app = Flask(__name__)
        >>> capture_flask_errors(app)
    """
    integration = FlaskIntegration(app, client)
    return integration
