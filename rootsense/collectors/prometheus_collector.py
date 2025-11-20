"""Prometheus metrics collector."""

from prometheus_client import Counter, Histogram, Gauge
import time


class PrometheusCollector:
    """Collects Prometheus metrics for requests."""

    def __init__(self, config):
        self.config = config
       
        # Define metrics
        self.request_count = Counter(
            'rootsense_requests_total',
            'Total requests',
            ['method', 'endpoint', 'status_code', 'service']
        )
       
        self.request_duration = Histogram(
            'rootsense_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint', 'service']
        )
       
        self.error_count = Counter(
            'rootsense_errors_total',
            'Total errors',
            ['error_type', 'service', 'endpoint']
        )
       
        self.active_requests = Gauge(
            'rootsense_active_requests',
            'Currently active requests',
            ['service']
        )

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float, service: str = "unknown"):
        """Record a request."""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            service=service
        ).inc()
       
        self.request_duration.labels(
            method=method,
            endpoint=endpoint,
            service=service
        ).observe(duration)

    def record_error(self, error_type: str, service: str, endpoint: str):
        """Record an error."""
        self.error_count.labels(
            error_type=error_type,
            service=service,
            endpoint=endpoint
        ).inc()

    def track_active_request(self, service: str = "unknown"):
        """Context manager for tracking active requests."""
        return ActiveRequestTracker(self.active_requests, service)


class ActiveRequestTracker:
    """Context manager for tracking active requests."""
   
    def __init__(self, gauge, service):
        self.gauge = gauge
        self.service = service
   
    def __enter__(self):
        self.gauge.labels(service=self.service).inc()
        return self
   
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.gauge.labels(service=self.service).dec()
