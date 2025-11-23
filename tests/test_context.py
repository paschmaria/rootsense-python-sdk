"""Tests for context management."""

import pytest
from rootsense.context import (
    set_context, get_context, clear_context,
    set_user, set_tag, add_breadcrumb
)


class TestContext:
    """Test context management."""

    def test_set_and_get_context(self):
        """Test setting and getting context."""
        clear_context()
        
        set_context("request", {"url": "/test"})
        context = get_context()
        
        assert context["request"]["url"] == "/test"

    def test_set_user(self):
        """Test setting user context."""
        clear_context()
        
        set_user({"id": "123", "email": "test@example.com"})
        context = get_context()
        
        assert context["user"]["id"] == "123"
        assert context["user"]["email"] == "test@example.com"

    def test_set_tag(self):
        """Test setting tags."""
        clear_context()
        
        set_tag("environment", "production")
        set_tag("version", "1.0.0")
        context = get_context()
        
        assert context["tags"]["environment"] == "production"
        assert context["tags"]["version"] == "1.0.0"

    def test_breadcrumbs(self):
        """Test breadcrumb tracking."""
        clear_context()
        
        add_breadcrumb("navigation", "User clicked button", {"button_id": "submit"})
        add_breadcrumb("http", "API call", {"url": "/api/users"})
        
        context = get_context()
        
        assert len(context["breadcrumbs"]) == 2
        assert context["breadcrumbs"][0]["category"] == "navigation"
        assert context["breadcrumbs"][1]["category"] == "http"

    def test_clear_context(self):
        """Test clearing context."""
        set_user({"id": "123"})
        set_tag("env", "test")
        
        clear_context()
        context = get_context()
        
        assert "user" not in context or not context["user"]
        assert "tags" not in context or not context["tags"]
