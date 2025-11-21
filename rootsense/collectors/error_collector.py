"""Error event collector and buffer."""

import hashlib
import logging
import queue
import threading
import time
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)


class ErrorCollector:
    """Collects and buffers error events with integrated metrics."""

    def __init__(self, config, http_transport):
        self.config = config
        self.http_transport = http_transport
        self._queue = queue.Queue(maxsize=config.buffer_size)
        self._worker_thread = None
        self._stop_event = threading.Event()
        self._local = threading.local()
        
        # Initialize Prometheus metrics (internal)
        self._init_metrics()

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        try:
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
        except Exception as e:
            if self.config.debug:
                logger.warning(f"Failed to initialize Prometheus metrics: {e}")
            # Set to None if initialization fails
            self.request_count = None
            self.request_duration = None
            self.error_count = None
            self.active_requests = None

    def start(self):
        """Start the background worker."""
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _worker(self):
        """Background worker that batches and sends events."""
        batch = []
        last_flush = time.time()
       
        while not self._stop_event.is_set():
            try:
                # Try to get events with timeout
                try:
                    event = self._queue.get(timeout=0.5)
                    batch.append(event)
                except queue.Empty:
                    pass
               
                # Flush if batch is full or enough time has passed
                should_flush = (
                    len(batch) >= 100 or
                    (len(batch) > 0 and time.time() - last_flush >= 5)
                )
               
                if should_flush:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()
                   
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
       
        # Flush remaining events on shutdown
        if batch:
            self._send_batch(batch)

    def _send_batch(self, batch):
        """Send a batch of events."""
        if not batch:
            return
           
        try:
            self.http_transport.send_events(batch)
            if self.config.debug:
                logger.debug(f"Sent batch of {len(batch)} events")
        except Exception as e:
            logger.error(f"Failed to send batch: {e}")

    def _enrich_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich event with context data."""
        from rootsense.context import get_context
        
        # Get thread-local context
        context = get_context()
        
        # Merge context into event
        if context.get('user'):
            event['user'] = context['user']
        if context.get('tags'):
            event.setdefault('tags', {}).update(context['tags'])
        if context.get('extra'):
            event.setdefault('extra', {}).update(context['extra'])
        if context.get('breadcrumbs'):
            event['breadcrumbs'] = context['breadcrumbs']
        
        return event

    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """Capture an exception."""
        event_id = str(uuid.uuid4())
       
        event = {
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "exception_type": type(exception).__name__,
            "message": str(exception),
            "stack_trace": traceback.format_exc(),
            "fingerprint": self._generate_fingerprint(exception, context),
            "environment": self.config.environment,
            "project_id": self.config.project_id,
        }
       
        if context:
            event.update(context)
           
        event.update(kwargs)
        
        # Auto-enrich with thread-local context
        event = self._enrich_event(event)
        
        # Record error metric
        if self.error_count:
            try:
                self.error_count.labels(
                    error_type=type(exception).__name__,
                    service=context.get('service', 'unknown') if context else 'unknown',
                    endpoint=context.get('endpoint', 'unknown') if context else 'unknown'
                ).inc()
            except Exception as e:
                if self.config.debug:
                    logger.warning(f"Failed to record error metric: {e}")
       
        # Add to queue
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.warning("Event queue is full, dropping event")
            return None
       
        return event_id

    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """Capture a message."""
        event_id = str(uuid.uuid4())
       
        event = {
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "message",
            "level": level,
            "message": message,
            "environment": self.config.environment,
            "project_id": self.config.project_id,
        }
       
        if context:
            event.update(context)
           
        event.update(kwargs)
        
        # Auto-enrich with thread-local context
        event = self._enrich_event(event)
       
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.warning("Event queue is full, dropping event")
            return None
       
        return event_id

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        service: str = "unknown"
    ):
        """Record request metrics."""
        if not self.request_count or not self.request_duration:
            return
            
        try:
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
        except Exception as e:
            if self.config.debug:
                logger.warning(f"Failed to record request metrics: {e}")

    def track_active_request(self, service: str = "unknown"):
        """Context manager for tracking active requests."""
        return ActiveRequestTracker(self.active_requests, service, self.config.debug)

    def _generate_fingerprint(self, exception: Exception, context: Optional[Dict] = None) -> str:
        """Generate fingerprint for incident grouping.
       
        Hash of: error_type + service + endpoint
        """
        error_type = type(exception).__name__
        service = context.get("service", "unknown") if context else "unknown"
        endpoint = context.get("endpoint", "unknown") if context else "unknown"
       
        fingerprint_str = f"{error_type}|{service}|{endpoint}"
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]

    def flush(self, timeout: float = 5):
        """Flush all pending events."""
        deadline = time.time() + timeout
       
        while not self._queue.empty() and time.time() < deadline:
            time.sleep(0.1)
       
        # Send remaining events
        batch = []
        while not self._queue.empty():
            try:
                batch.append(self._queue.get_nowait())
            except queue.Empty:
                break
       
        if batch:
            self._send_batch(batch)

    def stop(self):
        """Stop the worker thread."""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5)


class ActiveRequestTracker:
    """Context manager for tracking active requests."""
   
    def __init__(self, gauge, service, debug=False):
        self.gauge = gauge
        self.service = service
        self.debug = debug
   
    def __enter__(self):
        if self.gauge:
            try:
                self.gauge.labels(service=self.service).inc()
            except Exception as e:
                if self.debug:
                    logger.warning(f"Failed to track active request: {e}")
        return self
   
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.gauge:
            try:
                self.gauge.labels(service=self.service).dec()
            except Exception as e:
                if self.debug:
                    logger.warning(f"Failed to untrack active request: {e}")
