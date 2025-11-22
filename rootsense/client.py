"""Core RootSense client."""

import atexit
import logging
import threading
from typing import Any, Dict, Optional

from rootsense.config import Config
from rootsense.collectors.error_collector import ErrorCollector
from rootsense.transport.http_transport import HttpTransport
from rootsense.utils.sanitizer import Sanitizer

logger = logging.getLogger(__name__)


class RootSenseClient:
    """Main RootSense SDK client."""

    def __init__(self, config: Config):
        self.config = config
        self._lock = threading.RLock()
        self._initialized = False
        self._auto_instrumentation = None
       
        # Initialize components
        self.sanitizer = Sanitizer(sanitize_pii=config.sanitize_pii)
        self.transport = HttpTransport(config)
        
        # Initialize error collector (includes metrics)
        self.error_collector = ErrorCollector(config, self.transport)
       
        # Initialize auto-instrumentation if enabled
        if config.enable_auto_instrumentation:
            try:
                from rootsense.instrumentation.auto import AutoInstrumentation
                self._auto_instrumentation = AutoInstrumentation(
                    self.error_collector,
                    self.transport,
                    config
                )
                self._auto_instrumentation.initialize()
            except Exception as e:
                logger.warning(f"Auto-instrumentation not available: {e}")
       
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

    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """Capture an exception.
       
        Args:
            exception: The exception to capture
            context: Additional context (service, endpoint, etc.)
            **kwargs: Additional metadata
           
        Returns:
            Event ID if captured, None otherwise
            
        Example:
            >>> import rootsense
            >>> rootsense.init(api_key="...", project_id="...")
            >>> try:
            ...     1 / 0
            ... except Exception as e:
            ...     event_id = rootsense.capture_exception(e)
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
            
        Example:
            >>> import rootsense
            >>> rootsense.init(api_key="...", project_id="...")
            >>> rootsense.capture_message("User logged in", level="info")
        """
        return self.error_collector.capture_message(message, level, context, **kwargs)

    def close(self):
        """Shutdown the client and flush pending events."""
        if not self._initialized:
            return
           
        try:
            # Shutdown auto-instrumentation
            if self._auto_instrumentation:
                self._auto_instrumentation.shutdown()
            
            # Flush and shutdown collector
            self.error_collector.flush(timeout=5)
            self._initialized = False
           
            if self.config.debug:
                logger.info("RootSense client closed")
        except Exception as e:
            logger.error(f"Error closing RootSense client: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
