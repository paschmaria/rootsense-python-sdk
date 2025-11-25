"""Unified event type definitions for RootSense SDK."""

from typing import TypedDict, Optional, Dict, Any, List, Union
from datetime import datetime


class BaseEvent(TypedDict):
    """Base event fields that are common to all event types."""
    # Required fields
    event_id: str
    timestamp: str  # ISO format datetime string
    type: str  # "error", "message", "metric", "span"
    environment: str
    project_id: str


class BaseEventOptional(TypedDict, total=False):
    """Optional base event fields."""
    tags: Dict[str, Any]
    extra: Dict[str, Any]
    user: Dict[str, Any]
    breadcrumbs: List[Dict[str, Any]]


class ErrorEventRequired(TypedDict):
    """Required error event fields."""
    exception_type: str
    message: str
    stack_trace: str
    fingerprint: str


class ErrorEventOptional(TypedDict, total=False):
    """Optional error-specific fields."""
    service: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    request_id: Optional[str]
    trace_id: Optional[str]
    span_id: Optional[str]


class ErrorEvent(BaseEvent, BaseEventOptional, ErrorEventRequired, ErrorEventOptional):
    """Error event structure."""
    pass


class MessageEventRequired(TypedDict):
    """Required message event fields."""
    level: str  # "info", "warning", "error", "debug", "critical"
    message: str


class MessageEventOptional(TypedDict, total=False):
    """Optional message-specific fields."""
    category: Optional[str]
    logger: Optional[str]
    module: Optional[str]
    function: Optional[str]
    line_number: Optional[int]


class MessageEvent(BaseEvent, BaseEventOptional, MessageEventRequired, MessageEventOptional):
    """Message/log event structure."""
    pass


class MetricDataPoint(TypedDict, total=False):
    """Metric data point structure."""
    attributes: Dict[str, Any]
    value: Union[int, float]
    sum: Optional[Union[int, float]]
    count: Optional[int]
    min: Optional[Union[int, float]]
    max: Optional[Union[int, float]]
    start_time_unix_nano: Optional[int]
    time_unix_nano: Optional[int]


class MetricEventRequired(TypedDict):
    """Required metric event fields."""
    metric_name: str  # Base metric name


class MetricEventOptional(TypedDict, total=False):
    """Optional metric fields (used by different metric sources)."""
    metric_type: Optional[str]  # "counter", "gauge", "histogram", "summary"
    sample_name: Optional[str]  # Full sample name with suffix (_total, _count, _bucket, etc)
    name: Optional[str]  # Alternative name field (used by OTel exporter)
    description: Optional[str]
    unit: Optional[str]
    labels: Optional[Dict[str, str]]  # Prometheus-style labels
    value: Optional[Union[int, float]]  # Single value (Prometheus-style)
    time_unix_nano: Optional[int]  # Timestamp in nanoseconds (Prometheus-style)
    
    # OTel-style metric fields
    resource: Optional[Dict[str, Any]]  # Resource attributes
    data_points: Optional[List[MetricDataPoint]]  # OTel-style data points


class MetricEvent(BaseEvent, BaseEventOptional, MetricEventRequired, MetricEventOptional):
    """Metric event structure."""
    pass


class SpanStatus(TypedDict, total=False):
    """Span status structure."""
    code: str
    description: Optional[str]


class SpanEventData(TypedDict, total=False):
    """Span event data structure."""
    name: str
    timestamp: int
    attributes: Dict[str, Any]


class SpanError(TypedDict, total=False):
    """Span error details structure."""
    type: Optional[str]
    message: Optional[str]
    stacktrace: Optional[str]


class SpanEventRequired(TypedDict):
    """Required span event fields."""
    operation_type: str  # "http", "db", "redis", "celery", "messaging", "generic"
    name: str
    trace_id: str
    span_id: str
    is_error: bool


class SpanEventOptional(TypedDict, total=False):
    """Optional span fields."""
    parent_span_id: Optional[str]
    start_time: Optional[int]
    end_time: Optional[int]
    duration_ns: Optional[int]
    status: Optional[SpanStatus]
    attributes: Optional[Dict[str, Any]]
    events: Optional[List[SpanEventData]]  # Span events (not RootSense events)
    error: Optional[SpanError]


class SpanEvent(BaseEvent, BaseEventOptional, SpanEventRequired, SpanEventOptional):
    """Span/trace event structure."""
    pass


# Union type for all event types
RootSenseEvent = Union[ErrorEvent, MessageEvent, MetricEvent, SpanEvent]

