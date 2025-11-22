"""Pytest configuration and fixtures."""

import pytest
from rootsense.context import clear_context


@pytest.fixture(autouse=True)
def clean_context():
    """Clear context before each test."""
    clear_context()
    yield
    clear_context()
