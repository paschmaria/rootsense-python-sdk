"""PII sanitization utilities."""

import re
from typing import Any, Dict, List


class Sanitizer:
    """Sanitize PII from data before sending."""

    # Common PII patterns
    PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'credit_card': re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b'),
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'phone': re.compile(r'\b(?:\+?1[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b'),
        'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    }

    # Sensitive field names
    SENSITIVE_FIELDS = {
        'password', 'passwd', 'pwd', 'secret', 'api_key', 'apikey',
        'token', 'auth', 'authorization', 'credit_card', 'creditcard',
        'ssn', 'social_security', 'cvv', 'pin'
    }

    def __init__(self, sanitize_pii: bool = True):
        self.sanitize_pii = sanitize_pii

    def sanitize(self, data: Any) -> Any:
        """Sanitize PII from data."""
        if not self.sanitize_pii:
            return data

        if isinstance(data, dict):
            return self._sanitize_dict(data)
        elif isinstance(data, list):
            return [self.sanitize(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data

    def _sanitize_dict(self, data: Dict) -> Dict:
        """Sanitize dictionary."""
        result = {}
        for key, value in data.items():
            # Check if key is sensitive
            if key.lower() in self.SENSITIVE_FIELDS:
                result[key] = '[REDACTED]'
            else:
                result[key] = self.sanitize(value)
        return result

    def _sanitize_string(self, text: str) -> str:
        """Sanitize string content."""
        result = text
        for pattern_name, pattern in self.PATTERNS.items():
            result = pattern.sub(f'[{pattern_name.upper()}_REDACTED]', result)
        return result
