# Amazon Q Development Guidelines

Always follow these guidelines when assisting in development for the Amazon Q CLI.

## AmazonQ.md

DO NOT create or modify an AmazonQ.md file unless I explicitly tell you to do so.

## Python Best Practices

* Use `dedent()` where possible for formatting multiline strings.
* If Pydantic is used, be sure to use version 2.

## Pytest Best Practices

### Test Organization

* Tests are organized into two categories:
  * **Unit tests**: Located in `lib/idp_common_pkg/tests/unit/`
    * Unit tests should be self contained and run with no infrastructure or external system dependencies (database, s3 etc.)
  * **Integration tests**: Located in `lib/idp_common_pkg/tests/integration/`

### Test Annotations

* Always mark unit tests with `@pytest.mark.unit` decorator
* Always mark integration tests with `@pytest.mark.integration` decorator
* Example:
  ```python
  import pytest
  
  @pytest.mark.unit
  def test_my_unit_test():
      # Unit test implementation
      assert True
      
  @pytest.mark.integration
  def test_my_integration_test():
      # Integration test implementation
      assert True
  ```

### Test Fixtures

* Shared fixtures should be placed in `conftest.py`
* Fixtures should be well-documented with docstrings
* Example:
  ```python
  @pytest.fixture
  def sample_document():
      """Provides a sample document for testing."""
      return Document(id="test-doc", input_key="test.pdf")
  ```
### Developing Tests
* Unit and integration tests use the PyTest framework.
* Tests should be sensible and the minimum necessary to verify critical logic.
* Where possible, try to make tests easy to maintain.
* After generating unit tests, the AI agent should verify unit tests by running them all.
* To run all unit tests, the AI agent can execute the `make test -C lib/idp_common_pkg` command and observe that all tests pass.
* If all tests don't pass, then fix the test(s) that are failing.
* Tests should not throw warnings, if warnings are found, fix these.
* Integration tests should not be run by the AI agent during development.

### CI/CD Integration

* Tests are run automatically in CI/CD pipeline
* Unit tests run on all branches in the `develop_tests` stage
* Integration tests run on develop branch automatically and on feature branches manually
* Both test results and coverage reports are collected as artifacts
