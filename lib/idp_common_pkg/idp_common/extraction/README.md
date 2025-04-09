# IDP Extraction Module

This module provides functionality for extracting structured information from document sections using LLMs.

## Overview

The extraction module is designed to process document sections, extract key information based on configured attributes, and return structured results. It supports multimodal extraction using both text and images.

## Components

- **ExtractionService**: Main service class for performing extractions
- **Models**: Data classes for extraction results

## Usage

```python
from idp_common import get_config
from idp_common.extraction.service import ExtractionService

# Initialize the service with configuration
config = get_config()
extraction_service = ExtractionService(config=config)

# Example for processing a document section
result = extraction_service.extract_from_section(
    section=section_data,
    metadata=document_metadata,
    output_bucket="my-output-bucket"
)

# Access extracted fields
for attribute in result.attributes:
    print(f"{attribute.name}: {attribute.value}")
```

## Configuration

The extraction service uses the following configuration structure:

```json
{
    "extraction": {
        "model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "temperature": 0.0,
        "top_k": 0.5,
        "system_prompt": "You are an expert at extracting information from documents...",
        "task_prompt": "Extract the following fields from this {DOCUMENT_CLASS} document: {ATTRIBUTE_NAMES_AND_DESCRIPTIONS}\n\nDocument text:\n{DOCUMENT_TEXT}"
    },
    "classes": [
        {
            "name": "invoice",
            "description": "An invoice document",
            "attributes": [
                {
                    "name": "invoice_number",
                    "description": "The invoice number or ID"
                },
                {
                    "name": "date",
                    "description": "The invoice date"
                }
            ]
        }
    ]
}
```