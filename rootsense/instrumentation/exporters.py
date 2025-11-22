"""Custom OpenTelemetry exporters for RootSense."""

import logging
from typing import Sequence, Optional
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.metrics.export import MetricExporter, MetricExportResult
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.metrics.export import MetricsData

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

    def _convert_span_to_event(self, span: ReadableSpan) -> Optional[dict]:
        """Convert OTel span to RootSense event format."""
        attributes = dict(span.attributes) if span.attributes else {}
        
        # Determine operation type from span attributes
        operation_type = self._determine_operation_type(span.name, attributes)
        
        # Only create events for errors or important operations
        is_error = not span.status.is_ok
        is_important = operation_type in ['http', 'db', 'redis', 'celery']
        
        if not (is_error or is_important):
            return None
        
        event = {
            'type': 'span',
            'operation_type': operation_type,
            'name': span.name,
            'trace_id': format(span.context.trace_id, '032x'),
            'span_id': format(span.context.span_id, '016x'),
            'parent_span_id': format(span.parent.span_id, '016x') if span.parent else None,
            'start_time': span.start_time,
            'end_time': span.end_time,
            'duration_ns': span.end_time - span.start_time if span.end_time else None,
            'status': {
                'code': span.status.status_code.name,
                'description': span.status.description
            },
            'attributes': attributes,
            'events': [{
                'name': e.name,
                'timestamp': e.timestamp,
                'attributes': dict(e.attributes) if e.attributes else {}
            } for e in span.events] if span.events else [],
            'is_error': is_error
        }
        
        # Add error details if present
        if is_error and span.events:
            for event_obj in span.events:
                if event_obj.name == 'exception':
                    attrs = dict(event_obj.attributes) if event_obj.attributes else {}
                    event['error'] = {
                        'type': attrs.get('exception.type'),
                        'message': attrs.get('exception.message'),
                        'stacktrace': attrs.get('exception.stacktrace')
                    }
        
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

    def _convert_metric_to_event(self, metric, resource) -> Optional[dict]:
        """Convert OTel metric to RootSense event format."""
        # Extract resource attributes
        resource_attrs = dict(resource.attributes) if resource.attributes else {}
        
        event = {
            'type': 'metric',
            'name': metric.name,
            'description': metric.description,
            'unit': metric.unit,
            'resource': resource_attrs,
            'data_points': []
        }
        
        # Convert data points based on metric type
        for data_point in metric.data.data_points:
            dp = {
                'attributes': dict(data_point.attributes) if data_point.attributes else {},
                'start_time_unix_nano': data_point.start_time_unix_nano,
                'time_unix_nano': data_point.time_unix_nano
            }
            
            # Add value based on metric type
            if hasattr(data_point, 'value'):
                dp['value'] = data_point.value
            elif hasattr(data_point, 'sum'):
                dp['sum'] = data_point.sum
                dp['count'] = data_point.count
                if hasattr(data_point, 'min'):
                    dp['min'] = data_point.min
                    dp['max'] = data_point.max
            
            event['data_points'].append(dp)
        
        return event

    def shutdown(self, timeout_millis: float = 30000, **kwargs) -> None:
        """Shutdown the exporter."""
        pass

    def force_flush(self, timeout_millis: float = 10000) -> bool:
        """Force flush pending metrics."""
        return True
