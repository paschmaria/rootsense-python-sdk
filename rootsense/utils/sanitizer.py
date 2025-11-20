"""PII sanitization utilities."""

import re
from typing import Any, Dict, List


class Sanitizer:
    """Sanitizes sensitive data from requests and responses."""

    SENSITIVE_KEYS = [
        "password", "passwd", "pwd",
        "secret", "api_key", "apikey", "token", "auth",
        "authorization", "cookie", "session",
        "credit_card", "card_number", "cvv", "ssn",
        "private_key", "access_token", "refresh_token"
    ]
   
    # Regex patterns for PII
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')

    def __init__(self, send_default_pii: bool = False):
        self.send_default_pii = send_default_pii

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary recursively."""
        if not isinstance(data, dict):
            return data
       
        sanitized = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self.sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, str) and not self.send_default_pii:
                sanitized[key] = self._sanitize_string(value)
            else:
                sanitized[key] = value
       
        return sanitized

    def sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize HTTP headers."""
        sanitized = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in ['authorization', 'cookie', 'x-api-key']:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if key is sensitive."""
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS)

    def _sanitize_string(self, text: str) -> str:
        """Sanitize PII patterns in strings."""
        if not text:
            return text
       
        # Mask email addresses
        text = self.EMAIL_PATTERN.sub(lambda m: self._mask_email(m.group()), text)
       
        # Mask phone numbers
        text = self.PHONE_PATTERN.sub("XXX-XXX-XXXX", text)
       
        # Mask SSN
        text = self.SSN_PATTERN.sub("XXX-XX-XXXX", text)
       
        # Mask credit cards
        text = self.CREDIT_CARD_PATTERN.sub("XXXX-XXXX-XXXX-XXXX", text)
       
        return text

    def _mask_email(self, email: str) -> str:
        """Mask email address."""
        parts = email.split('@')
        if len(parts) != 2:
            return "[EMAIL]"
       
        username = parts[0]
        domain = parts[1]
       
        if len(username) <= 2:
            masked_username = "**"
        else:
            masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
       
        return f"{masked_username}@{domain}"
