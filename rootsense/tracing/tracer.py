"""Distributed tracing implementation."""

import time
import uuid
import logging
import functools
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

from rootsense.config import get_client
from rootsense.context import set_context, set_tag, push_breadcrumb

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional['Tracer'] = None


class Span:
    """Represents a single span in a trace."""

    def __init__(
        self,
        span_id: str,
        trace_id: str,
        operation: str,
        parent_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        self.span_id = span_id
        self.trace_id = trace_id
        self.operation = operation
        self.parent_id = parent_id
        self.tags = tags or {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.error: Optional[Exception] = None

    def finish(self):
        """Mark span as finished."""
        self.end_time = time.time()

    @property
    def duration(self) -> Optional[float]:
        """Get span duration in seconds."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    def set_tag(self, key: str, value: Any):
        """Set a tag on the span."""
        self.tags[key] = value

    def set_error(self, error: Exception):
        """Record an error on the span."""
        self.error = error
        self.tags["error"] = True
        self.tags["error.type"] = type(error).__name__
        self.tags["error.message"] = str(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "operation": self.operation,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "error": self.error is not None,
        }


class Tracer:
    """Distributed tracing implementation."""

    def __init__(self, client=None):
        self.client = client or get_client()
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: list[Span] = []

    def start_trace(self, operation: str, **tags) -> str:
        """Start a new trace.
        
        Args:
            operation: Name of the operation
            **tags: Additional tags
            
        Returns:
            Trace ID
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            operation=operation,
            tags=tags
        )
        
        self.active_spans[span_id] = span
        
        # Set trace context
        set_context("trace", {
            "trace_id": trace_id,
            "span_id": span_id,
        })
        
        push_breadcrumb(
            category="trace",
            message=f"Started trace: {operation}",
            level="info",
            data={"trace_id": trace_id, "span_id": span_id}
        )
        
        return trace_id

    @contextmanager
    def trace(
        self,
        operation: str,
        parent_trace_id: Optional[str] = None,
        **tags
    ):
        """Create a traced operation context.
        
        Args:
            operation: Name of the operation
            parent_trace_id: Parent trace ID for nested traces
            **tags: Additional tags
            
        Yields:
            Span object
            
        Example:
            >>> tracer = Tracer()
            >>> with tracer.trace("api_call", service="external") as span:
            ...     # Your code here
            ...     span.set_tag("status_code", 200)
        """
        trace_id = parent_trace_id or str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        
        # Find parent span if it exists
        parent_id = None
        for existing_span in self.active_spans.values():
            if existing_span.trace_id == trace_id:
                parent_id = existing_span.span_id
                break
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            operation=operation,
            parent_id=parent_id,
            tags=tags
        )
        
        self.active_spans[span_id] = span
        
        # Update context
        set_context("trace", {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_id,
        })
        
        try:
            yield span
        except Exception as e:
            span.set_error(e)
            raise
        finally:
            span.finish()
            
            # Move to completed spans
            self.active_spans.pop(span_id, None)
            self.completed_spans.append(span)
            
            # Record span data
            set_tag(f"trace.{operation}.duration", span.duration)
            
            push_breadcrumb(
                category="trace",
                message=f"Completed span: {operation}",
                level="info",
                data=span.to_dict()
            )

    def get_active_trace_id(self) -> Optional[str]:
        """Get the current active trace ID."""
        if self.active_spans:
            return list(self.active_spans.values())[0].trace_id
        return None

    def get_trace_data(self) -> Dict[str, Any]:
        """Get all trace data."""
        return {
            "active_spans": [span.to_dict() for span in self.active_spans.values()],
            "completed_spans": [span.to_dict() for span in self.completed_spans],
        }


def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = Tracer()
    return _tracer


def trace_function(operation: Optional[str] = None, **tags):
    """Decorator to trace a function.
    
    Args:
        operation: Operation name (defaults to function name)
        **tags: Additional tags
        
    Example:
        >>> @trace_function("user_service.get_user")
        ... def get_user(user_id):
        ...     # Function code
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.trace(op_name, **tags) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_tag("success", True)
                    return result
                except Exception as e:
                    span.set_tag("success", False)
                    raise
        
        return wrapper
    return decorator
