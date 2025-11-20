"""WebSocket transport for real-time streaming."""

import asyncio
import json
import logging
import threading
from typing import Optional

try:
    import websockets
except ImportError:
    websockets = None

logger = logging.getLogger(__name__)


class WebSocketTransport:
    """WebSocket transport for real-time data streaming."""

    def __init__(self, config):
        self.config = config
        self._ws = None
        self._loop = None
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Start WebSocket connection in background thread."""
        if websockets is None:
            logger.warning("websockets library not installed, WebSocket transport disabled")
            return
       
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        """Run async event loop in thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
       
        try:
            self._loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self._loop.close()

    async def _connect_and_listen(self):
        """Connect to WebSocket and listen for events."""
        ws_url = self.config.base_url.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/stream?project_id={self.config.project_id}"
       
        try:
            async with websockets.connect(
                ws_url,
                extra_headers={"X-API-Key": self.config.api_key}
            ) as websocket:
                self._ws = websocket
               
                while not self._stop_event.is_set():
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=1.0
                        )
                        self._handle_message(message)
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        break
                       
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")

    def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            # Handle different message types
            if self.config.debug:
                logger.debug(f"Received WebSocket message: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")

    def close(self):
        """Close WebSocket connection."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
