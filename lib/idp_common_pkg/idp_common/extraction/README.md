# IDP Extraction Module

This module provides functionality for extracting structured information from document sections using LLMs.

## Overview

The extraction module is designed to process document sections, extract key information based on configured attributes, and return structured results. It supports multimodal extraction using both text and images.

## Components

- **ExtractionService**: Main service class for performing extractions
- **Models**: Data classes for extraction results

## Usage

### Document-Based Approach (Recommended)

The recommended approach is to use the Document model-based interface, which simplifies integration with the entire IDP pipeline:

```python
from idp_common import get_config
from idp_common.extraction.service import ExtractionService
from idp_common.models import Document

# Initialize the service with configuration
config = get_config()
extraction_service = ExtractionService(config=config)

# Load your document
document = Document(...)  # Document with sections already classified

# Process a specific section in the document
document = extraction_service.process_document_section(
    document=document,
    section_id="section-123"
)

# Access extracted attributes on the section
section = next(s for s in document.sections if s.section_id == "section-123")
for attribute_name, attribute_value in section.attributes.items():
    print(f"{attribute_name}: {attribute_value}")
```

### Legacy Approach

The service also supports a lower-level interface for direct section processing:

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

## Error Handling

The Document-based approach has built-in error handling:

1. If a section ID is not found in the document, an error is added to `document.errors`
2. If extraction fails for any reason, the error is captured in `document.errors`
3. All errors are logged for debugging

## Thread Safety

The extraction service is designed to be thread-safe when using the Document model interface, supporting concurrent processing of multiple sections.