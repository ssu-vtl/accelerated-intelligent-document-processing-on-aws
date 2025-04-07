# IDP Common Package

This package contains common utilities for the GenAI IDP Accelerator patterns.

## Components

### AWS Service Clients
- Bedrock client with retry logic
- S3 client operations
- CloudWatch metrics

### Configuration
- DynamoDB-based configuration management
- Support for default and custom configuration merging

### Image Processing
- Image resizing and preparation

### Utils
- Retry/backoff algorithm
- S3 URI parsing
- Metering data aggregation

## Usage

```python
from idp_common import (
    bedrock,  # Bedrock client and operations
    s3,       # S3 operations
    metrics,  # CloudWatch metrics
    image,    # Image processing
    utils,    # General utilities
    config,   # Configuration module
    get_config # Direct access to the configuration function
)

# Publish a metric
metrics.put_metric("MetricName", 1)

# Invoke Bedrock
result = bedrock.invoke_model(...)

# Read from S3
content = s3.get_text_content("s3://bucket/key.json")

# Process an image for model input
image_bytes = image.prepare_image("s3://bucket/image.jpg")

# Parse S3 URI
bucket, key = utils.parse_s3_uri("s3://bucket/key")

# Get configuration (merged from Default and Custom)
cfg = get_config()
```

## Configuration

The configuration module provides a way to retrieve and merge configuration from DynamoDB. It expects:

1. A DynamoDB table with a primary key named 'Configuration'
2. Two configuration items with keys 'Default' and 'Custom'

The `get_config()` function retrieves both configurations and merges them, with custom values taking precedence over default ones.

```python
# Get configuration with default table name from CONFIGURATION_TABLE_NAME environment variable
config = get_config()

# Or specify a table name explicitly
config = get_config(table_name="my-config-table")
```

## Development Notes

This package consolidates functionality that was previously spread across multiple packages:
- Core utilities like S3, Bedrock, metrics, and image processing
- Configuration management (formerly in get_config_pkg)

It is designed to be used as a central dependency for all IDP accelerator patterns.