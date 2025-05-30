Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

# Changelog

## 2025-05-03: Refactored Bedrock Module

### Changes
- Refactored the `idp_common.bedrock` module from a function-based approach to a class-based design
- Created a new `BedrockClient` class in `bedrock/client.py` that encapsulates all Bedrock functionality
- Made the `BedrockClient` instances callable to maintain backward compatibility with the original function signature
- Implemented recursive retry logic for API calls
- Updated `bedrock/__init__.py` to export a default client instance as `invoke_model` for backward compatibility
- Re-exported key functions from the default client for backward compatibility

### Rationale
The refactoring was done to address several issues with the original implementation:

1. **Improved Code Organization**: The original implementation had approximately 400 lines of code in the `__init__.py` file, which is against Python's conventional module organization patterns. The refactoring moves this code to a dedicated class in a separate file.

2. **Better State Management**: The original implementation used global variables for state management (like `_bedrock_client`), which can lead to issues in more complex applications. The class-based approach properly encapsulates state in instance attributes.

3. **Enhanced Testability**: The class-based design makes it easier to mock the Bedrock client for testing and enables better isolation of components during testing.

4. **More Flexible Configuration**: The class-based approach allows for creating multiple client instances with different configurations, which wasn't possible with the global function-based approach.

5. **Cleaner Retry Logic**: The recursive approach for retry logic makes the code more readable and maintainable compared to the loop-based implementation.

6. **Backward Compatibility**: Despite the significant refactoring, backward compatibility is maintained through the callable interface of the `BedrockClient` class and re-exporting key functions, ensuring existing code continues to work without changes.

### Usage Examples

#### Original usage (still supported)
```python
from idp_common.bedrock import invoke_model

result = invoke_model(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    system_prompt="You are a helpful assistant.",
    content=[{"text": "Tell me a joke"}]
)
```

#### New class-based usage
```python
from idp_common.bedrock import BedrockClient

# Create a custom client with specific configuration
custom_client = BedrockClient(
    region="us-east-1",
    max_retries=5,
    metrics_enabled=False
)

# Use as a callable (function-like)
result = custom_client(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    system_prompt="You are a helpful assistant.",
    content=[{"text": "Tell me a joke"}]
)

# Or use the method directly
result = custom_client.invoke_model(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    system_prompt="You are a helpful assistant.",
    content=[{"text": "Tell me a joke"}]
)
```