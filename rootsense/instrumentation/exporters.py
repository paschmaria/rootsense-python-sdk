"""Custom OpenTelemetry exporters for RootSense."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Sequence, Optional, List
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.metrics.export import MetricExporter, MetricExportResult
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.metrics.export import MetricsData

from rootsense.events import SpanEvent, MetricEvent, SpanStatus, SpanEventData, SpanError, MetricDataPoint

logger = logging.getLogger(__name__)


class RootSenseSpanExporter(SpanExporter):
    """Exports OpenTelemetry spans as RootSense events.
    
    Converts OTel spans to our error/metric format and tracks auto-resolution
    for all operation types (HTTP, DB queries, Redis ops, etc.).
    """

    def __init__(self, error_collector, http_transport):
        self.error_collector = error_collector
        self.http_transport = http_transport

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans by converting them to RootSense events."""
        try:
            events = []
            
            for span in spans:
                # Convert span to our event format
                event = self._convert_span_to_event(span)
                
                if event:
                    events.append(event)
                    
                    # Track auto-resolution for successful operations
                    if span.status.is_ok:
                        self._track_success(span)
            
            # Batch send events
            if events:
                self.http_transport.send_events(events)
            
            return SpanExportResult.SUCCESS
            
        except Exception as e:
            logger.error(f"Error exporting spans: {e}")
            return SpanExportResult.FAILURE

    def _convert_span_to_event(self, span: ReadableSpan) -> Optional[SpanEvent]:
        """Convert OTel span to RootSense event format."""
        attributes = dict(span.attributes) if span.attributes else {}
        
        # Determine operation type from span attributes
        operation_type = self._determine_operation_type(span.name, attributes)
        
        # Only create events for errors or important operations
        is_error = not span.status.is_ok
        is_important = operation_type in ['http', 'db', 'redis', 'celery']
        
        if not (is_error or is_important):
            return None
        
        # Get config from error_collector for required fields
        config = self.error_collector.config
        
        # Build status object
        status: SpanStatus = {
            'code': span.status.status_code.name,
        }
        if span.status.description:
            status['description'] = span.status.description
        
        # Build span events list
        span_events: List[SpanEventData] = []
        if span.events:
            for e in span.events:
                span_event: SpanEventData = {
                    'name': e.name,
                    'timestamp': e.timestamp,
                    'attributes': dict(e.attributes) if e.attributes else {}
                }
                span_events.append(span_event)
        
        event: SpanEvent = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'span',
            'operation_type': operation_type,
            'name': span.name,
            'trace_id': format(span.context.trace_id, '032x'),
            'span_id': format(span.context.span_id, '016x'),
            'is_error': is_error,
            'environment': config.environment,
            'project_id': config.project_id,
        }
        
        # Add optional fields
        if span.parent:
            event['parent_span_id'] = format(span.parent.span_id, '016x')
        if span.start_time:
            event['start_time'] = span.start_time
        if span.end_time:
            event['end_time'] = span.end_time
        if span.end_time and span.start_time:
            event['duration_ns'] = span.end_time - span.start_time
        if status:
            event['status'] = status
        if attributes:
            event['attributes'] = attributes
        if span_events:
            event['events'] = span_events
        
        # Add error details if present
        if is_error and span.events:
            for event_obj in span.events:
                if event_obj.name == 'exception':
                    attrs = dict(event_obj.attributes) if event_obj.attributes else {}
                    error: SpanError = {}
                    if attrs.get('exception.type'):
                        error['type'] = attrs.get('exception.type')
                    if attrs.get('exception.message'):
                        error['message'] = attrs.get('exception.message')
                    if attrs.get('exception.stacktrace'):
                        error['stacktrace'] = attrs.get('exception.stacktrace')
                    if error:
                        event['error'] = error
        
        return event

    def _determine_operation_type(self, span_name: str, attributes: dict) -> str:
        """Determine operation type from span attributes."""
        # Check HTTP
        if 'http.method' in attributes or 'http.url' in attributes:
            return 'http'
        
        # Check DB
        if 'db.system' in attributes or 'db.statement' in attributes:
            return 'db'
        
        # Check Redis
        if 'db.system' in attributes and attributes['db.system'] == 'redis':
            return 'redis'
        
        # Check Celery
        if 'celery.task_name' in attributes:
            return 'celery'
        
        # Check messaging
        if 'messaging.system' in attributes:
            return 'messaging'
        
        return 'generic'

    def _track_success(self, span: ReadableSpan):
        """Track successful operation for auto-resolution."""
        attributes = dict(span.attributes) if span.attributes else {}
        operation_type = self._determine_operation_type(span.name, attributes)
        
        # Generate fingerprint based on operation type
        fingerprint = self._generate_fingerprint(operation_type, span.name, attributes)
        
        # Build context
        context = {
            'operation_type': operation_type,
            'operation_name': span.name,
            'attributes': attributes
        }
        
        # Send success signal for auto-resolution
        self.http_transport.send_success_signal(fingerprint, context)

    def _generate_fingerprint(self, operation_type: str, name: str, attributes: dict) -> str:
        """Generate unique fingerprint for operation."""
        if operation_type == 'http':
            method = attributes.get('http.method', 'UNKNOWN')
            route = attributes.get('http.route') or attributes.get('http.target', name)
            return f"http:{method}:{route}"
        
        elif operation_type == 'db':
            db_system = attributes.get('db.system', 'unknown')
            # Use operation name (e.g., SELECT, INSERT) rather than full statement
            operation = name.split()[0] if name else 'query'
            table = attributes.get('db.sql.table', 'unknown')
            return f"db:{db_system}:{operation}:{table}"
        
        elif operation_type == 'redis':
            command = attributes.get('db.operation', name)
            return f"redis:{command}"
        
        elif operation_type == 'celery':
            task_name = attributes.get('celery.task_name', name)
            return f"celery:{task_name}"
        
        else:
            return f"{operation_type}:{name}"

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush pending spans."""
        return True


class RootSenseMetricExporter(MetricExporter):
    """Exports OpenTelemetry metrics as RootSense events."""

    def __init__(self, http_transport):
        self.http_transport = http_transport

    def export(self, metrics_data: MetricsData, timeout_millis: float = 10000, **kwargs) -> MetricExportResult:
        """Export metrics by converting them to RootSense format."""
        try:
            events = []
            
            for resource_metrics in metrics_data.resource_metrics:
                for scope_metrics in resource_metrics.scope_metrics:
                    for metric in scope_metrics.metrics:
                        event = self._convert_metric_to_event(metric, resource_metrics.resource)
                        if event:
                            events.append(event)
            
            # Batch send events
            if events:
                self.http_transport.send_events(events)
            
            return MetricExportResult.SUCCESS
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return MetricExportResult.FAILURE

    def _convert_metric_to_event(self, metric, resource) -> Optional[MetricEvent]:
        """Convert OTel metric to RootSense event format."""
        # Extract resource attributes
        resource_attrs = dict(resource.attributes) if resource.attributes else {}
        
        # Get config from http_transport for required fields
        config = self.http_transport.config
        
        event: MetricEvent = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'type': 'metric',
            'metric_name': metric.name,
            'name': metric.name,  # Also set name for compatibility
            'environment': config.environment,
            'project_id': config.project_id,
        }
        
        # Add optional metric fields
        if metric.description:
            event['description'] = metric.description
        if metric.unit:
            event['unit'] = metric.unit
        if resource_attrs:
            event['resource'] = resource_attrs
        
        # Convert data points based on metric type
        data_points: List[MetricDataPoint] = []
        for data_point in metric.data.data_points:
            dp: MetricDataPoint = {
                'attributes': dict(data_point.attributes) if data_point.attributes else {},
            }
            
            # Add timestamp fields
            if hasattr(data_point, 'start_time_unix_nano'):
                dp['start_time_unix_nano'] = data_point.start_time_unix_nano
            if hasattr(data_point, 'time_unix_nano'):
                dp['time_unix_nano'] = data_point.time_unix_nano
            
            # Add value based on metric type
            if hasattr(data_point, 'value'):
                dp['value'] = data_point.value
            elif hasattr(data_point, 'sum'):
                dp['sum'] = data_point.sum
                if hasattr(data_point, 'count'):
                    dp['count'] = data_point.count
                if hasattr(data_point, 'min'):
                    dp['min'] = data_point.min
                if hasattr(data_point, 'max'):
                    dp['max'] = data_point.max
            
            data_points.append(dp)
        
        if data_points:
            event['data_points'] = data_points
        
        return event

    def shutdown(self, timeout_millis: float = 30000, **kwargs) -> None:
        """Shutdown the exporter."""
        pass

    def force_flush(self, timeout_millis: float = 10000) -> bool:
        """Force flush pending metrics."""
        return True
