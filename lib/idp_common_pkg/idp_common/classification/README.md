# Document Classification for IDP Accelerator

This module provides document classification capabilities for the IDP Accelerator project, allowing classification of documents based on their text and image content.

## Features

- Classification of documents using LLMs
- Support for both text and image content
- Concurrent processing of multiple pages
- Structured data models for results
- Grouping of pages into sections by classification
- Integration with `idp_common.bedrock` for model invocation

## Usage Example

```python
from idp_common import classification, get_config

# Load configuration
config = get_config()

# Initialize classification service
service = classification.ClassificationService(
    model_id=config["classification"]["model"],
    region="us-east-1",
    config=config
)

# Classify a single page
page_result = service.classify_page(
    page_id="1",
    text_uri="s3://bucket/document/pages/1/result.json",
    image_uri="s3://bucket/document/pages/1/image.jpg"
)

# Print the classification result
print(f"Page classified as: {page_result.classification.doc_type}")

# Classify multiple pages concurrently
pages = {
    "1": {"parsedTextUri": "s3://bucket/document/pages/1/result.json", "imageUri": "s3://bucket/document/pages/1/image.jpg"},
    "2": {"parsedTextUri": "s3://bucket/document/pages/2/result.json", "imageUri": "s3://bucket/document/pages/2/image.jpg"}
}

result = service.classify_pages(pages)

# Print the sections
for section in result.sections:
    print(f"Section {section.section_id}: {section.classification.doc_type}")
    for page in section.pages:
        print(f"  - Page {page.page_id}")

# Convert to dictionary for API response
api_response = result.to_dict()
```

## Configuration

The classification service uses the following configuration structure:

```json
{
  "classes": [
    {
      "name": "invoice",
      "description": "An invoice that specifies an amount of money to be paid."
    },
    {
      "name": "financial_statement",
      "description": "Documents that summarize financial performance, such as income statements, balance sheets, or cash flow statements."
    }
  ],
  "classification": {
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "temperature": 0,
    "top_k": 0.5,
    "system_prompt": "You are a document classification expert...",
    "task_prompt": "Classify the following document into one of these types: {CLASS_NAMES_AND_DESCRIPTIONS}...\n\nDocument text:\n{DOCUMENT_TEXT}"
  }
}
```

## Integration with Lambda Functions

To use this module in a Lambda function:

1. Add it as a dependency:
   ```
   ../../lib/idp_common_pkg  # common utilities package
   ```

2. Import and use the service:
   ```python
   from idp_common import classification, get_config
   
   # Initialize service
   config = get_config()
   service = classification.ClassificationService(config=config)
   
   # Use in Lambda handler
   def handler(event, context):
       # Get OCR results from event
       pages = event.get("OCRResult", {}).get("pages")
       
       # Classify pages
       result = service.classify_pages(pages)
       
       # Return API response
       return result.to_dict()
   ```

## Data Models

- `DocumentType`: Definition of a document type with name and description
- `DocumentClassification`: Classification result with document type and confidence
- `PageClassification`: Classification result for a single page
- `DocumentSection`: A section of consecutive pages with the same classification
- `ClassificationResult`: Overall result of a classification operation

## Future Enhancements

- Support for confidence scores
- More advanced document structure analysis
- Integration with custom models
- Multi-model classification for improved accuracy