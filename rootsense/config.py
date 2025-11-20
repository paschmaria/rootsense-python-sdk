"""Configuration and initialization for RootSense SDK."""

import os
import re
from typing import Optional
from urllib.parse import urlparse


class Config:
    """SDK configuration."""

    def __init__(
        self,
        dsn: str,
        environment: str = "production",
        enable_prometheus: bool = True,
        sample_rate: float = 1.0,
        debug: bool = False,
        send_default_pii: bool = False,
        max_breadcrumbs: int = 100,
    ):
        self.dsn = dsn
        self.environment = environment
        self.enable_prometheus = enable_prometheus
        self.sample_rate = sample_rate
        self.debug = debug
        self.send_default_pii = send_default_pii
        self.max_breadcrumbs = max_breadcrumbs
       
        # Parse DSN: https://API_KEY@api.rootsense.ai/PROJECT_ID
        self.api_key, self.base_url, self.project_id = self._parse_dsn(dsn)

    def _parse_dsn(self, dsn: str):
        """Parse Sentry-style DSN."""
        match = re.match(r"https://([^@]+)@([^/]+)/(.+)", dsn)
        if not match:
            raise ValueError(
                f"Invalid DSN format. Expected: https://API_KEY@api.rootsense.ai/PROJECT_ID, got: {dsn}"
            )
       
        api_key = match.group(1)
        host = match.group(2)
        project_id = match.group(3)
       
        base_url = f"https://{host}/v1"
       
        return api_key, base_url, project_id


# Global client instance
_client: Optional["RootSenseClient"] = None


def init(dsn: Optional[str] = None, **options) -> "RootSenseClient":
    """Initialize RootSense SDK.
   
    Args:
        dsn: RootSense DSN (https://API_KEY@api.rootsense.ai/PROJECT_ID)
            Can also be set via ROOTSENSE_DSN environment variable
        **options: Additional configuration options
           
    Returns:
        RootSenseClient instance
    """
    global _client
   
    if dsn is None:
        dsn = os.environ.get("ROOTSENSE_DSN")
   
    if not dsn:
        raise ValueError("DSN must be provided via init() or ROOTSENSE_DSN environment variable")
   
    from rootsense.client import RootSenseClient
   
    config = Config(dsn, **options)
    _client = RootSenseClient(config)
   
    return _client


def get_client() -> Optional["RootSenseClient"]:
    """Get the global RootSense client instance."""
    return _client
