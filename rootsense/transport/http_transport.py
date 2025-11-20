"""HTTP transport for sending events."""

import logging
import time
from typing import List, Dict, Any
import requests

logger = logging.getLogger(__name__)


class HttpTransport:
    """HTTP transport with retry logic."""

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
        url = f"{self.config.base_url}/events/batch"
       
        for attempt in range(3):
            try:
                response = self.session.post(
                    url,
                    json={"events": events},
                    timeout=10
                )
               
                if response.status_code == 200:
                    return True
               
                if response.status_code < 500:
                    # Client error, don't retry
                    logger.error(f"Client error sending events: {response.status_code} {response.text}")
                    return False
               
                # Server error, retry
                logger.warning(f"Server error (attempt {attempt + 1}/3): {response.status_code}")
               
            except requests.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}/3): {e}")
           
            # Exponential backoff
            if attempt < 2:
                time.sleep(2 ** attempt)
       
        return False

    def send_success_signal(self, fingerprint: str, context: Dict[str, Any]) -> bool:
        """Send success signal for auto-resolution."""
        url = f"{self.config.base_url}/events/success"
       
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
            logger.error(f"Error sending success signal: {e}")
            return False
