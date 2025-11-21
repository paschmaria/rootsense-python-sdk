"""Configuration and initialization for RootSense SDK."""

import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """SDK configuration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        backend_url: Optional[str] = None,
        connection_string: Optional[str] = None,
        environment: str = "production",
        sample_rate: float = 1.0,
        debug: bool = False,
        sanitize_pii: bool = True,
        max_breadcrumbs: int = 100,
        transport_type: str = "http",
    ):
        """Initialize RootSense configuration.
        
        Args:
            api_key: RootSense API key
            project_id: RootSense project ID
            backend_url: Backend API URL (default: https://api.rootsense.ai)
            connection_string: Alternative format: rootsense://API_KEY@HOST/PROJECT_ID
            environment: Environment name (e.g., production, staging)
            sample_rate: Error sampling rate (0.0 to 1.0)
            debug: Enable debug logging
            sanitize_pii: Automatically sanitize PII from events (default: True)
            max_breadcrumbs: Maximum number of breadcrumbs to store
            transport_type: Transport type ('http' or 'websocket', default: 'http')
        
        Examples:
            # Using separate parameters
            Config(
                api_key="abc123",
                project_id="proj-456",
                backend_url="https://api.rootsense.ai"
            )
            
            # Using connection string
            Config(connection_string="rootsense://abc123@api.rootsense.ai/proj-456")
        """
        # Parse connection string if provided
        if connection_string:
            api_key, backend_url, project_id = self._parse_connection_string(connection_string)
        
        # Validate required parameters
        if not api_key:
            raise ValueError("api_key is required (provide via api_key parameter or connection_string)")
        if not project_id:
            raise ValueError("project_id is required (provide via project_id parameter or connection_string)")
        
        self.api_key = api_key
        self.project_id = project_id
        self.backend_url = backend_url or "https://api.rootsense.ai"
        self.environment = environment
        self.sample_rate = sample_rate
        self.debug = debug
        self.sanitize_pii = sanitize_pii
        self.max_breadcrumbs = max_breadcrumbs
        self.transport_type = transport_type
        
        # Internal configuration
        self._enable_prometheus = True  # Always enabled internally
        self._enable_tracing = True  # Always enabled internally

    def _parse_connection_string(self, connection_string: str):
        """Parse RootSense connection string.
        
        Format: rootsense://API_KEY@HOST/PROJECT_ID
        Example: rootsense://abc123@api.rootsense.ai/proj-456
        
        Returns:
            Tuple of (api_key, base_url, project_id)
        """
        match = re.match(r"rootsense://([^@]+)@([^/]+)/(.+)", connection_string)
        if not match:
            raise ValueError(
                f"Invalid connection string format. "
                f"Expected: rootsense://API_KEY@HOST/PROJECT_ID, "
                f"got: {connection_string}"
            )
        
        api_key = match.group(1)
        host = match.group(2)
        project_id = match.group(3)
        
        base_url = f"https://{host}"
        
        return api_key, base_url, project_id


# Global client instance
_client: Optional["RootSenseClient"] = None


def init(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    backend_url: Optional[str] = None,
    connection_string: Optional[str] = None,
    **options
) -> "RootSenseClient":
    """Initialize RootSense SDK.
    
    Args:
        api_key: RootSense API key (can also use ROOTSENSE_API_KEY env var)
        project_id: RootSense project ID (can also use ROOTSENSE_PROJECT_ID env var)
        backend_url: Backend API URL (default: https://api.rootsense.ai)
        connection_string: Alternative format: rootsense://API_KEY@HOST/PROJECT_ID
            (can also use ROOTSENSE_CONNECTION_STRING env var)
        **options: Additional configuration options (environment, debug, etc.)
        
    Returns:
        RootSenseClient instance
    
    Examples:
        # Using separate parameters
        rootsense.init(
            api_key="abc123",
            project_id="proj-456",
            environment="production"
        )
        
        # Using connection string
        rootsense.init(
            connection_string="rootsense://abc123@api.rootsense.ai/proj-456"
        )
        
        # Using environment variables
        # Set ROOTSENSE_API_KEY, ROOTSENSE_PROJECT_ID, ROOTSENSE_BACKEND_URL
        rootsense.init()
    """
    global _client
    
    # Try environment variables if not provided
    if not connection_string:
        connection_string = os.environ.get("ROOTSENSE_CONNECTION_STRING")
    
    if not api_key:
        api_key = os.environ.get("ROOTSENSE_API_KEY")
    
    if not project_id:
        project_id = os.environ.get("ROOTSENSE_PROJECT_ID")
    
    if not backend_url:
        backend_url = os.environ.get("ROOTSENSE_BACKEND_URL")
    
    # Validate that we have either connection_string or api_key+project_id
    if not connection_string and not (api_key and project_id):
        raise ValueError(
            "Must provide either connection_string or (api_key + project_id). "
            "Can also set ROOTSENSE_CONNECTION_STRING or "
            "(ROOTSENSE_API_KEY + ROOTSENSE_PROJECT_ID) environment variables."
        )
    
    from rootsense.client import RootSenseClient
    
    config = Config(
        api_key=api_key,
        project_id=project_id,
        backend_url=backend_url,
        connection_string=connection_string,
        **options
    )
    _client = RootSenseClient(config)
    
    return _client


def get_client() -> Optional["RootSenseClient"]:
    """Get the global RootSense client instance."""
    return _client
