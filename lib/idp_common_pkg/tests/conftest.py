"""
Shared pytest fixtures for idp_common package tests.
"""

import pytest


@pytest.fixture
def sample_text():
    """Return a sample text for testing."""
    return "Hello, World!"
