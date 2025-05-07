# IDP Common Package Tests

This directory contains tests for the `idp_common` package, organized into unit tests and integration tests.

## Test Structure

- `unit/`: Contains unit tests that don't require external services
- `integration/`: Contains integration tests that may require external services or resources
- `conftest.py`: Shared pytest fixtures for all tests

## Running Tests

### Default Behavior

By default, running `pytest` will execute all tests **except** integration tests. This is configured in the `pytest.ini` file with the `addopts = -m "not integration"` setting.

### Running All Tests

To run all tests (both unit and integration):

```bash
cd lib/idp_common_pkg
pytest -m ""  # Override the default filter
```

### Running Only Unit Tests

To run only unit tests (this is the default):

```bash
cd lib/idp_common_pkg
pytest
```

Or explicitly:

```bash
cd lib/idp_common_pkg
pytest -m "unit"
```

Or by directory:

```bash
cd lib/idp_common_pkg
pytest tests/unit
```

### Running Only Integration Tests

To run only integration tests:

```bash
cd lib/idp_common_pkg
pytest -m "integration"
```

Or by directory:

```bash
cd lib/idp_common_pkg
pytest tests/integration
```

## Adding New Tests

### Unit Tests

Add new unit tests to the `tests/unit` directory. Unit tests should:
- Be marked with the `@pytest.mark.unit` decorator
- Be fast and not depend on external services
- Test individual components in isolation
- Use mocks for external dependencies

Example:

```python
# tests/unit/test_example.py
import pytest

@pytest.mark.unit
def test_my_function():
    # Test implementation here
    assert True
```

### Integration Tests

Add new integration tests to the `tests/integration` directory. Integration tests should:
- Be marked with the `@pytest.mark.integration` decorator
- Test interactions between components or with external services
- Include proper setup and teardown of test resources

Example:

```python
# tests/integration/test_example.py
import pytest

@pytest.mark.integration
def test_my_integration():
    # Integration test implementation here
    assert True
```

## Test Configuration

The `pytest.ini` file in the root directory defines:
- Markers for categorizing tests:
  - `unit`: For unit tests
  - `integration`: For integration tests
- Default options to exclude integration tests

## Fixtures

Shared test fixtures are defined in `conftest.py`. These fixtures are available to all tests.

To add a new fixture:

```python
# conftest.py
import pytest

@pytest.fixture
def my_fixture():
    # Setup code
    data = {"key": "value"}
    yield data
    # Teardown code (if needed)
```
