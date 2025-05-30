# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Shared pytest fixtures for idp_common package tests.
"""

import pytest


@pytest.fixture
def sample_text():
    """Return a sample text for testing."""
    return "Hello, World!"
