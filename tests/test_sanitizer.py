"""Tests for data sanitizer."""

import pytest
from rootsense.utils.sanitizer import Sanitizer


class TestSanitizer:
    """Test Sanitizer functionality."""

    def test_sanitize_removes_sensitive_keys(self):
        """Test that sensitive keys are removed."""
        sanitizer = Sanitizer(send_default_pii=False)
        
        data = {
            "username": "john_doe",
            "password": "secret123",
            "email": "john@example.com",
            "credit_card": "4111111111111111",
            "api_key": "abc123",
            "normal_field": "normal_value"
        }
        
        sanitized = sanitizer.sanitize(data)
        
        assert "password" not in sanitized
        assert "credit_card" not in sanitized
        assert "api_key" not in sanitized
        assert sanitized["normal_field"] == "normal_value"

    def test_sanitize_with_pii_enabled(self):
        """Test sanitization with PII enabled."""
        sanitizer = Sanitizer(send_default_pii=True)
        
        data = {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secret123"
        }
        
        sanitized = sanitizer.sanitize(data)
        
        # Email and username should be kept when PII is enabled
        assert sanitized.get("username") == "john_doe"
        assert sanitized.get("email") == "john@example.com"
        # But password should still be removed
        assert "password" not in sanitized

    def test_sanitize_nested_data(self):
        """Test sanitizing nested data structures."""
        sanitizer = Sanitizer(send_default_pii=False)
        
        data = {
            "user": {
                "id": 123,
                "password": "secret",
                "profile": {
                    "email": "test@example.com",
                    "api_key": "key123"
                }
            }
        }
        
        sanitized = sanitizer.sanitize(data)
        
        assert "password" not in sanitized["user"]
        assert "api_key" not in sanitized["user"]["profile"]
        assert sanitized["user"]["id"] == 123

    def test_sanitize_lists(self):
        """Test sanitizing data in lists."""
        sanitizer = Sanitizer(send_default_pii=False)
        
        data = {
            "users": [
                {"id": 1, "password": "pass1"},
                {"id": 2, "password": "pass2"}
            ]
        }
        
        sanitized = sanitizer.sanitize(data)
        
        for user in sanitized["users"]:
            assert "password" not in user
            assert "id" in user

    def test_sanitize_custom_patterns(self):
        """Test sanitizing with custom patterns."""
        sanitizer = Sanitizer(
            send_default_pii=False,
            custom_patterns=[r"secret_.*"]
        )
        
        data = {
            "secret_token": "abc123",
            "secret_key": "def456",
            "public_data": "visible"
        }
        
        sanitized = sanitizer.sanitize(data)
        
        assert "secret_token" not in sanitized
        assert "secret_key" not in sanitized
        assert sanitized["public_data"] == "visible"
