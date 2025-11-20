"""Core RootSense client."""

import atexit
import logging
import threading
from typing import Any, Dict, Optional

from rootsense.config import Config
from rootsense.collectors.prometheus_collector import PrometheusCollector
from rootsense.collectors.error_collector import ErrorCollector
from rootsense.transport.http_transport import HttpTransport
from rootsense.transport.websocket_transport import WebSocketTransport
from rootsense.utils.sanitizer import Sanitizer

logger = logging.getLogger(__name__)


class RootSenseClient:
    """Main RootSense SDK client."""

    def __init__(self, config: Config):
        self.config = config
        self._lock = threading.RLock()
        self._initialized = False
       
        # Initialize components
        self.sanitizer = Sanitizer(send_default_pii=config.send_default_pii)
        self.http_transport = HttpTransport(config)
        self.ws_transport = WebSocketTransport(config)
       
        # Initialize collectors
        if config.enable_prometheus:
            self.prometheus_collector = PrometheusCollector(config)
        else:
            self.prometheus_collector = None
           
        self.error_collector = ErrorCollector(config, self.http_transport)
       
        # Start background workers
        self._start()
       
        # Register cleanup
        atexit.register(self.close)
       
        self._initialized = True
        
        if config.debug:
            logger.info(f"RootSense initialized for project {config.project_id}")

    def _start(self):
        """Start background workers."""
        self.error_collector.start()
        self.ws_transport.start()

    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """Capture an exception.
       
        Args:
            exception: The exception to capture
            context: Additional context
            **kwargs: Additional metadata
           
        Returns:
            Event ID if captured, None otherwise
        """
        return self.error_collector.capture_exception(exception, context, **kwargs)

    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """Capture a message.
       
        Args:
            message: The message to capture
            level: Log level (debug, info, warning, error, critical)
            context: Additional context
            **kwargs: Additional metadata
           
        Returns:
            Event ID if captured, None otherwise
        """
        return self.error_collector.capture_message(message, level, context, **kwargs)

    def close(self):
        """Shutdown the client and flush pending events."""
        if not self._initialized:
            return
           
        try:
            self.error_collector.flush(timeout=5)
            self.ws_transport.close()
            self._initialized = False
           
            if self.config.debug:
                logger.info("RootSense client closed")
        except Exception as e:
            logger.error(f"Error closing RootSense client: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
