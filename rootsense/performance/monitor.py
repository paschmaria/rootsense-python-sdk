"""Performance monitoring module."""

import time
import functools
import logging
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

from rootsense.config import get_client
from rootsense.context import set_tag, push_breadcrumb

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor performance metrics for operations."""

    def __init__(self, client=None):
        self.client = client or get_client()
        self._spans = {}

    @contextmanager
    def track(self, operation: str, **tags):
        """Track performance of an operation.
        
        Args:
            operation: Name of the operation
            **tags: Additional tags for the operation
            
        Yields:
            Performance span context
            
        Example:
            >>> monitor = PerformanceMonitor()
            >>> with monitor.track("database_query", query_type="SELECT"):
            ...     # Your code here
            ...     pass
        """
        start_time = time.time()
        span_id = f"{operation}_{start_time}"
        
        # Record start
        push_breadcrumb(
            category="performance",
            message=f"Started {operation}",
            level="info",
            data=tags
        )
        
        try:
            yield span_id
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            set_tag(f"performance.{operation}.duration", duration)
            for key, value in tags.items():
                set_tag(f"performance.{operation}.{key}", value)
            
            # Record completion
            push_breadcrumb(
                category="performance",
                message=f"Completed {operation}",
                level="info",
                data={
                    "duration": duration,
                    **tags
                }
            )
            
            # Log slow operations (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow operation detected: {operation} took {duration:.2f}s",
                    extra={"operation": operation, "duration": duration, **tags}
                )

    def measure_function(self, func: Callable) -> Callable:
        """Decorator to measure function execution time.
        
        Args:
            func: Function to measure
            
        Returns:
            Wrapped function
            
        Example:
            >>> monitor = PerformanceMonitor()
            >>> @monitor.measure_function
            ... def slow_operation():
            ...     time.sleep(1)
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            operation_name = f"{func.__module__}.{func.__name__}"
            with self.track(operation_name):
                return func(*args, **kwargs)
        return wrapper


def track_performance(operation: str, **tags):
    """Decorator to track performance of a function.
    
    Args:
        operation: Name of the operation
        **tags: Additional tags
        
    Returns:
        Decorator function
        
    Example:
        >>> @track_performance("api_call", service="external_api")
        ... def call_api():
        ...     # API call code
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor()
            with monitor.track(operation, **tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator
