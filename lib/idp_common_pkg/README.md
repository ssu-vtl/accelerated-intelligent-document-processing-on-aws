# IDP Common Package

This package contains common utilities for the GenAI IDP Accelerator patterns.

## Components

### AWS Service Clients
- Bedrock client with retry logic
- S3 client operations
- CloudWatch metrics

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
    utils     # General utilities
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
```