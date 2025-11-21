"""FastAPI integration for RootSense."""

import time
import logging
from typing import Callable, Optional

try:
    from fastapi import FastAPI, Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.types import ASGIApp
except ImportError:
    raise ImportError("FastAPI is not installed. Install with: pip install rootsense[fastapi]")

from rootsense.config import get_client
from rootsense.context import set_context, set_tag

logger = logging.getLogger(__name__)


class FastAPIMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic error tracking and performance monitoring."""

    def __init__(self, app: ASGIApp, client=None):
        super().__init__(app)
        self.client = client or get_client()
        
        if self.client is None:
            logger.warning("RootSense not initialized. Call rootsense.init() first.")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process each request.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware in chain
            
        Returns:
            Response object
        """
        start_time = time.time()
        
        # Set request context
        set_context("request", {
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
            "client": request.client.host if request.client else None,
        })

        # Set user context if available
        if hasattr(request.state, "user") and request.state.user:
            from rootsense.context import set_user
            user = request.state.user
            set_user({
                "id": getattr(user, "id", None),
                "email": getattr(user, "email", None),
                "username": getattr(user, "username", None),
            })

        try:
            response = await call_next(request)
            
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


class FastAPIIntegration:
    """FastAPI integration for RootSense."""

    def __init__(self, app: Optional[FastAPI] = None, client=None):
        self.client = client
        if app is not None:
            self.init_app(app)

    def init_app(self, app: FastAPI):
        """Initialize the FastAPI app with RootSense.
        
        Args:
            app: FastAPI application instance
        """
        if self.client is None:
            self.client = get_client()

        if self.client is None:
            logger.warning("RootSense not initialized. Call rootsense.init() first.")
            return

        # Add middleware
        app.add_middleware(FastAPIMiddleware, client=self.client)

        logger.info("RootSense FastAPI integration initialized")


def capture_fastapi_errors(app: FastAPI, client=None):
    """Convenience function to add RootSense to a FastAPI app.
    
    Args:
        app: FastAPI application instance
        client: Optional RootSense client instance
        
    Returns:
        FastAPIIntegration instance
        
    Example:
        >>> from fastapi import FastAPI
        >>> import rootsense
        >>> from rootsense.integrations.fastapi import capture_fastapi_errors
        >>> 
        >>> rootsense.init(api_key="your-api-key", project_id="your-project-id")
        >>> app = FastAPI()
        >>> capture_fastapi_errors(app)
    """
    integration = FastAPIIntegration(app, client)
    return integration
