"""
A simple "Hello World" test for the idp_common package.
"""
import pytest


@pytest.mark.unit
def test_hello_world(sample_text):
    """A simple test that always passes."""
    assert sample_text == "Hello, World!"
    assert len(sample_text) > 0
    assert "Hello" in sample_text


@pytest.mark.unit
def test_idp_common_import():
    """Test that the idp_common package can be imported."""
    import idp_common
    assert idp_common is not None
    assert hasattr(idp_common, "__version__")
