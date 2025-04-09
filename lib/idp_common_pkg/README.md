# IDP Common Package

This package contains common utilities and services for the GenAI IDP Accelerator patterns.

## Components

### Core Services

- **OCR**: Document OCR processing with AWS Textract ([README](idp_common/ocr/README.md))
- **Classification**: Document classification using LLMs ([README](idp_common/classification/README.md))
- **Extraction**: Field extraction from documents using LLMs ([README](idp_common/extraction/README.md))

### AWS Service Clients

- Bedrock client with retry logic
- S3 client operations
- CloudWatch metrics

### Configuration

- DynamoDB-based configuration management
- Support for default and custom configuration merging

### Image Processing

- Image resizing and preparation
- Support for multimodal inference with Bedrock

### Utils

- Retry/backoff algorithm
- S3 URI parsing
- Metering data aggregation

## Usage

```python
from idp_common import (
    bedrock,       # Bedrock client and operations
    s3,            # S3 operations
    metrics,       # CloudWatch metrics
    image,         # Image processing
    utils,         # General utilities
    config,        # Configuration module
    get_config,    # Direct access to the configuration function
    ocr,           # OCR service and models
    classification, # Classification service and models
    extraction     # Extraction service and models
)

# Get configuration (merged from Default and Custom records in the DynamoDb Configuration Table)
cfg = get_config()

# OCR Processing
ocr_service = ocr.OcrService()
ocr_result = ocr_service.process_document(pdf_content, output_bucket, prefix)

# Document Classification
classification_service = classification.ClassificationService(config=cfg)
classification_result = classification_service.classify_pages(pages)

# Field Extraction
extraction_service = extraction.ExtractionService(config=cfg)
extraction_result = extraction_service.extract_from_section(section, metadata, output_bucket)

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

## Service Modules

### OCR Service (`ocr`)

Provides OCR processing of documents using AWS Textract:
- Multi-page document processing with thread concurrency
- Image extraction and optimization
- Support for enhanced Textract features (tables, forms)
- Well-structured results for downstream processing

### Classification Service (`classification`)

Document classification using multimodal LLMs:
- Page-level and document-level classification
- Section detection for multi-class documents
- Configurable document types and descriptions
- Multimodal classification with both text and images

### Extraction Service (`extraction`)

Field extraction from documents using multimodal LLMs:
- Extraction of structured data from document sections
- Support for document class-specific attribute definitions
- Multimodal extraction using both text and images
- Flexible prompt templates configurable via the configuration system

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
- Document processing services like OCR, Classification, and Extraction
- Configuration management (formerly in get_config_pkg)

It is designed to be used as a central dependency for all IDP accelerator patterns.