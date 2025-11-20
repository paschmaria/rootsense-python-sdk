"""Flask integration for RootSense.

This module provides Flask-specific middleware for automatic error capture
and request context tracking.
"""

import logging
from functools import wraps
from typing import Optional, Callable, Any

from flask import Flask, request, g
from werkzeug.exceptions import HTTPException

import rootsense
from rootsense.config import Config
from rootsense.client import RootSenseClient

logger = logging.getLogger(__name__)


class RootSenseFlask:
    """Flask integration for RootSense.
    
    Automatically captures exceptions and adds request context.
    
    Example:
        >>> from flask import Flask
        >>> from rootsense.integrations.flask import RootSenseFlask
        >>> 
        >>> app = Flask(__name__)
        >>> RootSenseFlask(
        ...     app,
        ...     api_key="your-api-key",
        ...     project_id="your-project-id"
        ... )
    """
    
    def __init__(
        self,
        app: Optional[Flask] = None,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        **config_kwargs
    ):
        """Initialize Flask integration.
        
        Args:
            app: Flask application instance
            api_key: RootSense API key
            project_id: RootSense project ID
            **config_kwargs: Additional configuration options
        """
        self.app = app
        self.client: Optional[RootSenseClient] = None
        
        if app is not None:
            self.init_app(app, api_key, project_id, **config_kwargs)
    
    def init_app(
        self,
        app: Flask,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        **config_kwargs
    ):
        """Initialize the Flask app with RootSense.
        
        Args:
            app: Flask application instance
            api_key: RootSense API key
            project_id: RootSense project ID
            **config_kwargs: Additional configuration options
        """
        # Get configuration from Flask config or parameters
        api_key = api_key or app.config.get('ROOTSENSE_API_KEY')
        project_id = project_id or app.config.get('ROOTSENSE_PROJECT_ID')
        
        if not api_key or not project_id:
            raise ValueError(
                "api_key and project_id are required. "
                "Provide them as arguments or set ROOTSENSE_API_KEY and "
                "ROOTSENSE_PROJECT_ID in Flask config."
            )
        
        # Merge configuration
        config_dict = {
            'api_key': api_key,
            'project_id': project_id,
            **config_kwargs
        }
        
        # Override with Flask config if present
        for key in ['api_url', 'environment', 'release', 'debug']:
            flask_key = f'ROOTSENSE_{key.upper()}'
            if flask_key in app.config:
                config_dict[key] = app.config[flask_key]
        
        # Initialize RootSense
        config = Config(**config_dict)
        self.client = RootSenseClient(config)
        
        # Store client in app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['rootsense'] = self.client
        
        # Register hooks
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown)
        
        # Register error handlers
        app.register_error_handler(Exception, self._handle_exception)
        
        # Add /metrics endpoint if Prometheus is enabled
        if config.enable_prometheus:
            self._add_metrics_endpoint(app)
        
        logger.info(f"RootSense Flask integration initialized for project {project_id}")
    
    def _before_request(self):
        """Hook called before each request."""
        # Store request start time
        g.rootsense_start_time = self._get_timestamp()
        
        # Add request context
        rootsense.set_context('request', {
            'url': request.url,
            'method': request.method,
            'endpoint': request.endpoint,
            'view_args': request.view_args,
        })
        
        # Add headers (excluding sensitive ones)
        headers = dict(request.headers)
        for sensitive_header in ['Authorization', 'Cookie', 'X-Api-Key']:
            headers.pop(sensitive_header, None)
        
        rootsense.set_context('headers', headers)
        
        # Add user agent
        if request.user_agent:
            rootsense.set_tag('browser', request.user_agent.browser)
            rootsense.set_tag('platform', request.user_agent.platform)
        
        # Add client IP (respecting X-Forwarded-For)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip:
            rootsense.set_tag('client_ip', client_ip.split(',')[0].strip())
    
    def _after_request(self, response):
        """Hook called after each request."""
        # Add response status
        rootsense.set_tag('response_status', response.status_code)
        
        # Calculate request duration
        if hasattr(g, 'rootsense_start_time'):
            duration = self._get_timestamp() - g.rootsense_start_time
            rootsense.set_context('performance', {
                'duration_ms': duration * 1000
            })
        
        return response
    
    def _teardown(self, exception=None):
        """Hook called when request context is torn down."""
        # Clear request-specific context
        pass
    
    def _handle_exception(self, error: Exception):
        """Handle exceptions and send to RootSense."""
        # Add error context
        rootsense.push_breadcrumb(
            message=f"Exception occurred: {type(error).__name__}",
            category="error",
            level="error"
        )
        
        # Capture exception (but not 404s)
        if not isinstance(error, HTTPException) or error.code >= 500:
            rootsense.capture_exception(error)
        
        # Re-raise to let Flask handle it
        raise error
    
    def _add_metrics_endpoint(self, app: Flask):
        """Add /metrics endpoint for Prometheus."""
        try:
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            
            @app.route('/metrics')
            def metrics():
                """Prometheus metrics endpoint."""
                return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
        except ImportError:
            logger.warning("prometheus_client not installed, /metrics endpoint not available")
    
    @staticmethod
    def _get_timestamp() -> float:
        """Get current timestamp in seconds."""
        import time
        return time.time()


def capture_exceptions(f: Callable) -> Callable:
    """Decorator to capture exceptions from Flask route handlers.
    
    Example:
        >>> @app.route('/api/endpoint')
        >>> @capture_exceptions
        >>> def my_endpoint():
        ...     # Your code
        ...     pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            rootsense.capture_exception(e)
            raise
    return decorated_function
