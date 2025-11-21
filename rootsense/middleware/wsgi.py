"""WSGI middleware for RootSense."""

import time
import logging
from typing import Callable, Iterable, Any

from rootsense.config import get_client
from rootsense.context import set_context, set_tag

logger = logging.getLogger(__name__)


class WSGIMiddleware:
    """Generic WSGI middleware for automatic error tracking.
    
    This middleware works with any WSGI application (Flask, Django, Bottle, etc.)
    """

    def __init__(self, app: Callable, client=None):
        self.app = app
        self.client = client or get_client()
        
        if self.client is None:
            logger.warning("RootSense not initialized. Call rootsense.init() first.")

    def __call__(self, environ: dict, start_response: Callable) -> Iterable[bytes]:
        """Process WSGI request.
        
        Args:
            environ: WSGI environment dict
            start_response: Start response callable
            
        Returns:
            Response iterable
        """
        start_time = time.time()
        
        # Extract request information
        set_context("request", {
            "method": environ.get("REQUEST_METHOD"),
            "path": environ.get("PATH_INFO"),
            "query_string": environ.get("QUERY_STRING"),
            "remote_addr": environ.get("REMOTE_ADDR"),
        })

        status_code = None

        def custom_start_response(status: str, response_headers: list, exc_info=None):
            """Wrapper to capture response status."""
            nonlocal status_code
            # Extract status code from status line (e.g., "200 OK")
            status_code = int(status.split()[0])
            return start_response(status, response_headers, exc_info)

        try:
            # Call the wrapped application
            response = self.app(environ, custom_start_response)
            
            # Track metrics after response is generated
            duration = time.time() - start_time
            if status_code:
                set_tag("http.status_code", status_code)
                set_tag("http.response_time", duration)
                
                if 200 <= status_code < 400:
                    set_tag("request.success", True)
            
            return response
            
        except Exception as exc:
            if self.client:
                self.client.capture_exception(exc)
            raise


def wrap_wsgi_app(app: Callable, client=None) -> WSGIMiddleware:
    """Wrap a WSGI application with RootSense middleware.
    
    Args:
        app: WSGI application
        client: Optional RootSense client instance
        
    Returns:
        Wrapped WSGI application
        
    Example:
        >>> from rootsense.integrations.wsgi import wrap_wsgi_app
        >>> import rootsense
        >>> 
        >>> rootsense.init(api_key="your-api-key", project_id="your-project-id")
        >>> app = wrap_wsgi_app(app)
    """
    return WSGIMiddleware(app, client)
