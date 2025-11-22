"""Configuration and initialization for RootSense SDK."""

import os
import re
from typing import Optional
from urllib.parse import urlparse


class Config:
    """SDK configuration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        backend_url: Optional[str] = None,
        connection_string: Optional[str] = None,
        environment: str = "production",
        service_name: Optional[str] = None,
        service_version: Optional[str] = None,
        sample_rate: float = 1.0,
        debug: bool = False,
        sanitize_pii: bool = True,
        max_breadcrumbs: int = 100,
        buffer_size: int = 1000,
        enable_auto_instrumentation: bool = True,
    ):
        """Initialize SDK configuration.
        
        Args:
            api_key: Your RootSense API key
            project_id: Your RootSense project ID
            backend_url: RootSense backend URL (default: https://api.rootsense.ai)
            connection_string: Alternative format: rootsense://API_KEY@HOST/PROJECT_ID
            environment: Environment name (production, staging, development, etc.)
            service_name: Service name for tracing (auto-detected if not provided)
            service_version: Service version for tracing
            sample_rate: Error sampling rate (0.0-1.0)
            debug: Enable debug logging
            sanitize_pii: Automatically sanitize PII in requests/responses (default: True)
            max_breadcrumbs: Maximum breadcrumbs to store
            buffer_size: Event buffer size
            enable_auto_instrumentation: Enable OpenTelemetry auto-instrumentation (default: True)
        """
        # Parse connection string if provided
        if connection_string:
            api_key, backend_url, project_id = self._parse_connection_string(connection_string)
        
        # Validate required parameters
        if not api_key:
            api_key = os.environ.get("ROOTSENSE_API_KEY")
        if not project_id:
            project_id = os.environ.get("ROOTSENSE_PROJECT_ID")
        if not backend_url:
            backend_url = os.environ.get("ROOTSENSE_BACKEND_URL", "https://api.rootsense.ai")
        
        if not api_key:
            raise ValueError(
                "api_key is required. Provide via api_key parameter, connection_string, "
                "or ROOTSENSE_API_KEY environment variable"
            )
        if not project_id:
            raise ValueError(
                "project_id is required. Provide via project_id parameter, connection_string, "
                "or ROOTSENSE_PROJECT_ID environment variable"
            )
        
        self.api_key = api_key
        self.project_id = project_id
        self.backend_url = backend_url.rstrip('/')  
        self.base_url = self.backend_url  # Alias for compatibility
        self.environment = environment
        self.service_name = service_name
        self.service_version = service_version
        self.sample_rate = sample_rate
        self.debug = debug
        self.sanitize_pii = sanitize_pii
        self.max_breadcrumbs = max_breadcrumbs
        self.buffer_size = buffer_size
        self.enable_auto_instrumentation = enable_auto_instrumentation
        
        # Construct API endpoints
        self.events_endpoint = f"{self.backend_url}/v1/projects/{self.project_id}/events"
        self.traces_endpoint = f"{self.backend_url}/v1/projects/{self.project_id}/traces"

    def _parse_connection_string(self, connection_string: str):
        """Parse RootSense connection string.
        
        Format: rootsense://API_KEY@HOST/PROJECT_ID
        Example: rootsense://abc123@api.rootsense.ai/proj-456
        """
        match = re.match(r"rootsense://([^@]+)@([^/]+)/(.+)", connection_string)
        if not match:
            raise ValueError(
                f"Invalid connection string format. Expected: rootsense://API_KEY@HOST/PROJECT_ID, "
                f"got: {connection_string}"
            )
        
        api_key = match.group(1)
        host = match.group(2)
        project_id = match.group(3)
        
        # Determine protocol (default to https)
        backend_url = f"https://{host}"
        
        return api_key, backend_url, project_id
