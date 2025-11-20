"""ASGI middleware for RootSense."""

import time
import logging
from typing import Callable, Awaitable

from rootsense.config import get_client
from rootsense.context import set_context, set_tag

logger = logging.getLogger(__name__)


class ASGIMiddleware:
    """Generic ASGI middleware for automatic error tracking.
    
    This middleware works with any ASGI application (Starlette, FastAPI, Quart, etc.)
    """

    def __init__(self, app, client=None):
        self.app = app
        self.client = client or get_client()
        
        if self.client is None:
            logger.warning("RootSense not initialized. Call rootsense.init() first.")

    async def __call__(self, scope, receive, send):
        """Process ASGI request.
        
        Args:
            scope: ASGI scope dict
            receive: Receive callable
            send: Send callable
        """
        if scope["type"] != "http":
            # Only handle HTTP requests
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        
        # Extract request information
        headers = dict(scope.get("headers", []))
        set_context("request", {
            "method": scope.get("method"),
            "path": scope.get("path"),
            "query_string": scope.get("query_string", b"").decode("utf-8"),
            "headers": {k.decode("utf-8"): v.decode("utf-8") for k, v in headers.items()},
        })

        status_code = None

        async def send_wrapper(message):
            """Wrapper to capture response status."""
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status")
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            
            # Track metrics
            duration = time.time() - start_time
            if status_code:
                set_tag("http.status_code", status_code)
                set_tag("http.response_time", duration)
                
                if 200 <= status_code < 400:
                    set_tag("request.success", True)
                    
        except Exception as exc:
            if self.client:
                self.client.capture_exception(exc)
            raise
