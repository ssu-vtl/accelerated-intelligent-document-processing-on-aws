# Bedrock Integration

The GenAIIC IDP Accelerator includes a robust client for Amazon Bedrock that provides resilient model invocation with built-in retry handling, metrics collection, and helpful utilities. This integration supports all document processing patterns that utilize Bedrock models.

## Using the Bedrock Client

### Simple Function Approach

For quick, straightforward use cases, you can use the function-style interface:

```python
from idp_common.bedrock import invoke_model

# Basic model invocation
response = invoke_model(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    system_prompt="You are a helpful assistant.",
    content=[{"text": "What are the main features of AWS Bedrock?"}],
    temperature=0.0,
    top_k=250
)

# Process the response
output_text = response["response"]["output"]["message"]["content"][0]["text"]
print(output_text)
```

### Class-Based Interface

For more control and advanced features, use the BedrockClient class directly:

```python
from idp_common.bedrock.client import BedrockClient

# Create a custom client
client = BedrockClient(
    region="us-east-1",
    max_retries=5,
    initial_backoff=1.5,
    max_backoff=300,
    metrics_enabled=True
)

# Invoke a model
response = client.invoke_model(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="You are a helpful assistant.",
    content=[{"text": "How does document processing work?"}],
    temperature=0.0
)

# Extract text using the helper method
output_text = client.extract_text_from_response(response)
print(output_text)
```

## Working with Embeddings

Generate text embeddings for semantic search or document comparison:

```python
from idp_common.bedrock.client import BedrockClient

client = BedrockClient()
embedding = client.generate_embedding(
    text="This document contains information about loan applications.",
    model_id="amazon.titan-embed-text-v1"
)

# Use embedding for vector search, clustering, etc.
```

## Helper Methods

The BedrockClient provides useful utilities for common tasks:

### Prompt Formatting

```python
from idp_common.bedrock.client import BedrockClient

client = BedrockClient()

template = """
Please analyze this {DOCUMENT_TYPE}:

<document>
{CONTENT}
</document>

Extract the following fields: {FIELDS}
"""

substitutions = {
    "DOCUMENT_TYPE": "invoice",
    "CONTENT": "Invoice #12345\nDate: 2023-05-15\nAmount: $1,250.00",
    "FIELDS": "invoice_number, date, amount"
}

formatted_prompt = client.format_prompt(template, substitutions)
```

### Response Text Extraction

```python
# Extract text from a complex response structure
text = client.extract_text_from_response(response)
```

## Guardrail Support

This module includes built-in support for Amazon Bedrock Guardrails, which help enforce content safety, security, and policy compliance across all Bedrock model interactions.

### Configuring Guardrails

Guardrails are configured via environment variables:

- `GUARDRAIL_ID_AND_VERSION`: Contains the Guardrail ID and Version in format `id:version`

When properly configured, the `get_guardrail_config()` function will automatically include guardrail parameters in Bedrock API calls.

### How Guardrail Integration Works

1. The `invoke_model` function checks if `GUARDRAIL_ID_AND_VERSION` is set
2. If configured, guardrail parameters are parsed from the environment variable
3. Appropriate guardrail parameters are added to Bedrock API calls:
   - For `converse` API: Uses `guardrailIdentifier`, `guardrailVersion`, and `trace`
4. Debug logs show when guardrails are being applied

### Example with Guardrails

```python
import os
from idp_common.bedrock import invoke_model

# Set the environment variable (typically configured in Lambda environment)
os.environ["GUARDRAIL_ID_AND_VERSION"] = "your-guardrail-id:Draft"

# Call invoke_model normally - guardrails are applied automatically
response = invoke_model(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="You are a helpful assistant.",
    content=[{"text": "Tell me about security best practices."}],
    temperature=0.0
)
```

## Resilience Features

The BedrockClient automatically handles common failure scenarios:

- Exponential backoff with jitter for rate limits and transient errors
- Intelligent classification of retryable vs. non-retryable errors
- Detailed logging with appropriate content sanitization
- Metrics collection for request counts, latencies, and token usage

## Configuration Options

When creating a BedrockClient instance, you can customize:

- `region`: AWS region for Bedrock (default: AWS_REGION env var or us-west-2)
- `max_retries`: Maximum retry attempts for throttled requests (default: 8)
- `initial_backoff`: Starting backoff time in seconds (default: 2)
- `max_backoff`: Maximum backoff time in seconds (default: 300)
- `metrics_enabled`: Whether to publish CloudWatch metrics (default: True)

This integration provides the foundation for reliable, scalable document processing with Amazon Bedrock models throughout the accelerator.