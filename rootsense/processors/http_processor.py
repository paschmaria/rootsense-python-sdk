"""HTTP request context processor."""

import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class HttpContextProcessor:
    """Process and enrich HTTP request context."""

    # Sensitive headers that should be redacted
    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-csrf-token",
    }

    # Query params that should be redacted
    SENSITIVE_PARAMS = {
        "password",
        "token",
        "api_key",
        "secret",
        "access_token",
        "refresh_token",
    }

    def __init__(self, redact_sensitive: bool = True):
        self.redact_sensitive = redact_sensitive

    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process HTTP request data.
        
        Args:
            request_data: Raw request data
            
        Returns:
            Enriched request context
        """
        context = {
            "url": request_data.get("url"),
            "method": request_data.get("method"),
            "headers": self._process_headers(request_data.get("headers", {})),
        }

        # Parse URL components
        if context["url"]:
            parsed_url = urlparse(context["url"])
            context["url_components"] = {
                "scheme": parsed_url.scheme,
                "host": parsed_url.netloc,
                "path": parsed_url.path,
                "query": self._process_query_string(parsed_url.query),
            }

        # Add client information
        if "remote_addr" in request_data:
            context["client"] = {
                "ip": request_data["remote_addr"],
            }

        # Add user agent parsing
        user_agent = request_data.get("headers", {}).get("user-agent")
        if user_agent:
            context["user_agent"] = self._parse_user_agent(user_agent)

        return context

    def _process_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Process and sanitize headers."""
        if not self.redact_sensitive:
            return headers

        processed = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in self.SENSITIVE_HEADERS:
                processed[key] = "[REDACTED]"
            else:
                processed[key] = value

        return processed

    def _process_query_string(self, query_string: str) -> Dict[str, Any]:
        """Parse and sanitize query string."""
        if not query_string:
            return {}

        params = parse_qs(query_string)
        
        if not self.redact_sensitive:
            return params

        # Redact sensitive parameters
        processed = {}
        for key, values in params.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_PARAMS):
                processed[key] = ["[REDACTED]"] * len(values)
            else:
                processed[key] = values

        return processed

    def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """Parse user agent string into components."""
        # Simple user agent parsing
        # For production, consider using a library like user-agents
        context = {
            "string": user_agent,
        }

        # Detect browser
        if "Chrome" in user_agent:
            context["browser"] = "Chrome"
        elif "Firefox" in user_agent:
            context["browser"] = "Firefox"
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            context["browser"] = "Safari"
        elif "Edge" in user_agent:
            context["browser"] = "Edge"
        else:
            context["browser"] = "Unknown"

        # Detect OS
        if "Windows" in user_agent:
            context["os"] = "Windows"
        elif "Mac OS" in user_agent or "Macintosh" in user_agent:
            context["os"] = "macOS"
        elif "Linux" in user_agent:
            context["os"] = "Linux"
        elif "Android" in user_agent:
            context["os"] = "Android"
        elif "iOS" in user_agent or "iPhone" in user_agent or "iPad" in user_agent:
            context["os"] = "iOS"
        else:
            context["os"] = "Unknown"

        # Detect device type
        if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
            context["device_type"] = "mobile"
        elif "Tablet" in user_agent or "iPad" in user_agent:
            context["device_type"] = "tablet"
        else:
            context["device_type"] = "desktop"

        return context

    def extract_request_metadata(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract useful metadata from request.
        
        Args:
            request_data: Request data
            
        Returns:
            Request metadata
        """
        metadata = {}

        # Extract content type
        headers = request_data.get("headers", {})
        content_type = headers.get("content-type", "")
        if content_type:
            metadata["content_type"] = content_type.split(";")[0].strip()

        # Extract request size
        content_length = headers.get("content-length")
        if content_length:
            try:
                metadata["request_size"] = int(content_length)
            except ValueError:
                pass

        # Extract referrer
        referrer = headers.get("referer") or headers.get("referrer")
        if referrer:
            metadata["referrer"] = referrer

        # Extract accept headers
        accept = headers.get("accept")
        if accept:
            metadata["accept"] = accept

        return metadata
