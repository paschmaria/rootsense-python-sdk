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

logger = logging.getLogger(__name__)


class ErrorCollector:
    """Collects and buffers error events."""

    def __init__(self, config, http_transport):
        self.config = config
        self.http_transport = http_transport
        self._queue = queue.Queue(maxsize=1000)
        self._worker_thread = None
        self._stop_event = threading.Event()
        self._local = threading.local()

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
       
        try:
            self._queue.put_nowait(event)
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
