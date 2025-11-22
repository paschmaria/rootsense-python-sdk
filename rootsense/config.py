"""Configuration and initialization for RootSense SDK."""

import os
import re
from typing import Optional
from urllib.parse import urlparse


class Config:
    """SDK configuration.
   
    Can be initialized in multiple ways:
   
    1. Connection string:
        Config(connection_string="rootsense://key@api.rootsense.ai/project")
   
    2. Individual parameters:
        Config(api_key="key", project_id="project", base_url="https://api.rootsense.ai")
   
    3. Environment variables:
        Config()  # Reads from ROOTSENSE_API_KEY, ROOTSENSE_PROJECT_ID, etc.
    """
   
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
        connection_string: Optional[str] = None,
        environment: str = "production",
        sanitize_pii: bool = True,
        debug: bool = False
    ):
        # Try connection string first
        if connection_string:
            parsed = self._parse_connection_string(connection_string)
            self.api_key = parsed["api_key"]
            self.project_id = parsed["project_id"]
            self.base_url = parsed["base_url"]
        else:
            # Try environment variables, then parameters
            self.api_key = api_key or os.getenv("ROOTSENSE_API_KEY")
            self.project_id = project_id or os.getenv("ROOTSENSE_PROJECT_ID")
            self.base_url = base_url or os.getenv("ROOTSENSE_BASE_URL", "https://api.rootsense.ai")
       
        self.environment = environment or os.getenv("ROOTSENSE_ENVIRONMENT", "production")
        self.sanitize_pii = sanitize_pii
        self.debug = debug or os.getenv("ROOTSENSE_DEBUG", "false").lower() == "true"
       
        self._validate()
   
    def _parse_connection_string(self, conn_str: str) -> dict:
        """Parse connection string.
       
        Format: rootsense://api_key@host/project_id
        Example: rootsense://abc123@api.rootsense.ai/my-project
        """
        match = re.match(r"rootsense://([^@]+)@([^/]+)/(.+)", conn_str)
        if not match:
            raise ValueError(
                "Invalid connection string format. "
                "Expected: rootsense://api_key@host/project_id"
            )
       
        api_key, host, project_id = match.groups()
        return {
            "api_key": api_key,
            "project_id": project_id,
            "base_url": f"https://{host}"
        }
   
    def _validate(self):
        """Validate configuration."""
        if not self.api_key:
            raise ValueError("API key is required")
        if not self.project_id:
            raise ValueError("Project ID is required")
        if not self.base_url:
            raise ValueError("Base URL is required")
