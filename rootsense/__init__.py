"""RootSense Python SDK."""

__version__ = "0.1.0"

from rootsense.client import RootSenseClient
from rootsense.config import Config

# Global client instance
_client = None


def init(**kwargs):
    """Initialize RootSense SDK.
    
    Args:
        **kwargs: Configuration options passed to Config
        
    Example:
        >>> import rootsense
        >>> rootsense.init(
        ...     api_key="your-api-key",
        ...     project_id="your-project",
        ...     environment="production"
        ... )
        >>> 
        >>> # Or with connection string
        >>> rootsense.init(
        ...     connection_string="rootsense://key@api.rootsense.ai/project"
        ... )
    """
    global _client
    config = Config(**kwargs)
    _client = RootSenseClient(config)
    
    # Auto-install instrumentation if requested
    if kwargs.get("auto_instrumentation", True):
        try:
            from rootsense.instrumentation import install_auto_instrumentation
            install_auto_instrumentation()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to install auto-instrumentation: {e}"
            )
    
    return _client


def get_client():
    """Get the global RootSense client instance.
    
    Returns:
        RootSenseClient instance or None if not initialized
    """
    return _client


def capture_exception(exception, **kwargs):
    """Capture an exception.
    
    Args:
        exception: The exception to capture
        **kwargs: Additional context
        
    Returns:
        Event ID if captured, None otherwise
    """
    if _client:
        return _client.capture_exception(exception, **kwargs)
    return None


def capture_message(message, level="info", **kwargs):
    """Capture a message.
    
    Args:
        message: The message to capture
        level: Log level (debug, info, warning, error, critical)
        **kwargs: Additional context
        
        Returns:
        Event ID if captured, None otherwise
    """
    if _client:
        return _client.capture_message(message, level=level, **kwargs)
    return None


__all__ = [
    "init",
    "get_client",
    "capture_exception",
    "capture_message",
    "Config",
    "RootSenseClient",
]
