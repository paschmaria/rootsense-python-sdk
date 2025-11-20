"""Django integration for RootSense."""

import time
import logging
from typing import Callable, Optional

try:
    from django.http import HttpRequest, HttpResponse
    from django.core.exceptions import MiddlewareNotUsed
    from django.conf import settings
except ImportError:
    raise ImportError("Django is not installed. Install with: pip install rootsense[django]")

from rootsense.config import get_client
from rootsense.context import set_context, set_tag, set_user

logger = logging.getLogger(__name__)


class DjangoMiddleware:
    """Django middleware for automatic error tracking and performance monitoring."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.client = get_client()
        
        if self.client is None:
            logger.warning("RootSense not initialized. Call rootsense.init() first.")
            # Don't raise MiddlewareNotUsed to allow the app to still work

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process each request.
        
        Args:
            request: Django request object
            
        Returns:
            HttpResponse object
        """
        start_time = time.time()
        
        # Set request context
        set_context("request", {
            "url": request.build_absolute_uri(),
            "method": request.method,
            "headers": dict(request.headers),
            "remote_addr": self._get_client_ip(request),
        })

        # Set user context if available
        if hasattr(request, "user") and request.user.is_authenticated:
            set_user({
                "id": request.user.id,
                "email": getattr(request.user, "email", None),
                "username": request.user.username,
            })

        try:
            response = self.get_response(request)
            
            # Track performance metrics
            duration = time.time() - start_time
            set_tag("http.status_code", response.status_code)
            set_tag("http.response_time", duration)
            
            # Track successful request
            if 200 <= response.status_code < 400:
                set_tag("request.success", True)
            
            return response
            
        except Exception as exc:
            # Capture the exception
            if self.client:
                self.client.capture_exception(exc)
            raise

    def process_exception(self, request: HttpRequest, exception: Exception):
        """Process exceptions that occur during request handling.
        
        Args:
            request: Django request object
            exception: The exception that occurred
        """
        if self.client:
            self.client.capture_exception(exception)

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> Optional[str]:
        """Extract client IP from request.
        
        Args:
            request: Django request object
            
        Returns:
            Client IP address or None
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


def init_django(api_key: str, project_id: str, **kwargs):
    """Initialize RootSense for Django.
    
    This should be called in your Django settings.py or apps.py.
    
    Args:
        api_key: Your RootSense API key
        project_id: Your RootSense project ID
        **kwargs: Additional configuration options
        
    Example:
        In settings.py:
        >>> from rootsense.integrations.django import init_django
        >>> 
        >>> init_django(
        ...     api_key=os.environ.get("ROOTSENSE_API_KEY"),
        ...     project_id=os.environ.get("ROOTSENSE_PROJECT_ID"),
        ...     environment="production"
        ... )
        >>> 
        >>> MIDDLEWARE = [
        ...     # ... other middleware
        ...     'rootsense.integrations.django.DjangoMiddleware',
        ... ]
    """
    import rootsense
    rootsense.init(api_key=api_key, project_id=project_id, **kwargs)
