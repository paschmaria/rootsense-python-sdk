"""Error event collector with integrated metrics."""

import hashlib
import logging
import queue
import threading
import time
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ErrorCollector:
    """Collects and buffers error events with integrated Prometheus metrics."""

    def __init__(self, config, http_transport):
        self.config = config
        self.http_transport = http_transport
        self._queue = queue.Queue(maxsize=1000)
        self._worker_thread = None
        self._stop_event = threading.Event()
        self._local = threading.local()
       
        # Initialize Prometheus metrics if available
        if PROMETHEUS_AVAILABLE:
            self._init_metrics()
        else:
            self._metrics_enabled = False

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        try:
            self.error_count = Counter(
                'rootsense_errors_total',
                'Total number of errors captured',
                ['error_type', 'environment']
            )
            self.event_queue_size = Gauge(
                'rootsense_event_queue_size',
                'Current size of the event queue'
            )
            self.batch_send_duration = Histogram(
                'rootsense_batch_send_duration_seconds',
                'Time taken to send event batches'
            )
            self._metrics_enabled = True
        except Exception as e:
            logger.warning(f"Failed to initialize Prometheus metrics: {e}")
            self._metrics_enabled = False

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
                   
                    # Update queue size metric
                    if self._metrics_enabled:
                        self.event_queue_size.set(self._queue.qsize())
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
            # Track batch send duration
            if self._metrics_enabled:
                with self.batch_send_duration.time():
                    success = self.http_transport.send_events(batch)
            else:
                success = self.http_transport.send_events(batch)
               
            if success and self.config.debug:
                logger.debug(f"Sent batch of {len(batch)} events")
        except Exception as e:
            logger.error(f"Failed to send batch: {e}")

    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """Capture an exception."""
        event_id = str(uuid.uuid4())
        error_type = type(exception).__name__
       
        # Update metrics
        if self._metrics_enabled:
            self.error_count.labels(
                error_type=error_type,
                environment=self.config.environment
            ).inc()
       
        event = {
            "event_id": event_id,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "exception_type": error_type,
            "message": str(exception),
            "stack_trace": traceback.format_exc(),
            "fingerprint": self._generate_fingerprint(exception, context),
            "environment": self.config.environment,
            "project_id": self.config.project_id,
        }
       
        if context:
            event.update(context)
           
        event.update(kwargs)
       
        # Add to queue
        try:
            self._queue.put_nowait(event)
            if self._metrics_enabled:
                self.event_queue_size.set(self._queue.qsize())
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
       
        try:
            self._queue.put_nowait(event)
            if self._metrics_enabled:
                self.event_queue_size.set(self._queue.qsize())
        except queue.Full:
            logger.warning("Event queue is full, dropping event")
            return None
       
        return event_id

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
