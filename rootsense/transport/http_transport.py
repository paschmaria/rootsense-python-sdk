"""HTTP transport for sending events."""

import logging
import time
from typing import List, Dict, Any
import requests

logger = logging.getLogger(__name__)


class HttpTransport:
    """HTTP transport with retry logic and exponential backoff."""

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": config.api_key,
            "Content-Type": "application/json",
            "User-Agent": f"rootsense-python-sdk/0.1.0"
        })

    def send_events(self, events: List[Dict[str, Any]]) -> bool:
        """Send a batch of events with retry logic."""
        if not events:
            return True
            
        url = f"{self.config.events_endpoint}/batch"
       
        for attempt in range(3):
            try:
                response = self.session.post(
                    url,
                    json={"events": events},
                    timeout=10
                )
               
                if response.status_code == 200:
                    if self.config.debug:
                        logger.debug(f"Successfully sent {len(events)} events")
                    return True
               
                if response.status_code < 500:
                    logger.error(f"Client error: {response.status_code}")
                    return False
               
                logger.warning(f"Server error (attempt {attempt + 1}/3): {response.status_code}")
               
            except requests.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}/3): {e}")
           
            if attempt < 2:
                time.sleep(2 ** attempt)
       
        return False

    def send_success_signal(self, fingerprint: str, context: Dict[str, Any]) -> bool:
        """Send success signal for auto-resolution."""
        url = f"{self.config.events_endpoint}/success"
       
        try:
            response = self.session.post(
                url,
                json={
                    "fingerprint": fingerprint,
                    "context": context,
                    "project_id": self.config.project_id
                },
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException as e:
            if self.config.debug:
                logger.debug(f"Error sending success signal: {e}")
            return False

    def close(self):
        """Close the HTTP session."""
        self.session.close()
