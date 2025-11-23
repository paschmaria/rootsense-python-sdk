"""Tests for PII sanitization."""

import pytest
from rootsense.utils.sanitizer import Sanitizer


class TestSanitizer:
    """Test PII sanitization."""

    def test_sanitize_enabled(self):
        """Test sanitization when enabled."""
        sanitizer = Sanitizer(sanitize_pii=True)
        
        data = {
            "password": "secret123",
            "api_key": "key-12345",
            "token": "bearer-token",
            "credit_card": "1234-5678-9012-3456",
            "safe_data": "visible"
        }
        
        result = sanitizer.sanitize_dict(data)
        
        assert result["password"] == "[Filtered]"
        assert result["api_key"] == "[Filtered]"
        assert result["token"] == "[Filtered]"
        assert result["credit_card"] == "[Filtered]"
        assert result["safe_data"] == "visible"

    def test_sanitize_disabled(self):
        """Test that sanitization can be disabled."""
        sanitizer = Sanitizer(sanitize_pii=False)
        
        data = {
            "password": "secret123",
            "api_key": "key-12345"
        }
        
        result = sanitizer.sanitize_dict(data)
        
        assert result["password"] == "secret123"
        assert result["api_key"] == "key-12345"

    def test_nested_sanitization(self):
        """Test sanitization of nested structures."""
        sanitizer = Sanitizer(sanitize_pii=True)
        
        data = {
            "user": {
                "password": "secret",
                "name": "John"
            },
            "metadata": {
                "token": "abc123"
            }
        }
        
        result = sanitizer.sanitize_dict(data)
        
        assert result["user"]["password"] == "[Filtered]"
        assert result["user"]["name"] == "John"
        assert result["metadata"]["token"] == "[Filtered]"

    def test_list_sanitization(self):
        """Test sanitization of lists."""
        sanitizer = Sanitizer(sanitize_pii=True)
        
        data = [
            {"password": "secret1"},
            {"password": "secret2"},
            {"name": "visible"}
        ]
        
        result = sanitizer.sanitize_list(data)
        
        assert result[0]["password"] == "[Filtered]"
        assert result[1]["password"] == "[Filtered]"
        assert result[2]["name"] == "visible"
