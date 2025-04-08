# OCR Service for IDP Accelerator

This module provides OCR (Optical Character Recognition) capabilities for processing documents within the IDP Accelerator project.

## Overview

The OCR service is designed to process PDF documents and extract text using AWS Textract. It supports both basic text detection and enhanced document analysis with tables and forms recognition.

## Features

- PDF processing with page-by-page OCR
- Concurrent processing of pages for improved performance
- Support for basic text detection (faster) or enhanced document analysis
- Structured result objects for easy integration with other systems
- S3 storage of intermediate and final results
- Metering data collection for usage tracking

## Usage Example

```python
import boto3
from idp_common import ocr

# Get document from S3
s3_client = boto3.client('s3')
response = s3_client.get_object(Bucket='input-bucket', Key='document.pdf')
pdf_content = response['Body'].read()

# Initialize OCR service
ocr_service = ocr.OcrService(
    region='us-east-1',
    max_workers=20,
    enhanced_features=False  # Set to True for tables, forms recognition
)

# Process document
result = ocr_service.process_document(
    pdf_content=pdf_content,
    output_bucket='output-bucket',
    prefix='document/output'
)

# Use the results
print(f"Processed {result.num_pages} pages")
for page_num, page_result in result.pages.items():
    print(f"Page {page_num}: Image at {page_result.image_uri}")
    print(f"Page {page_num}: Text at {page_result.parsed_text_uri}")
```


## Roadmap

### Phase 1: Current Implementation (Basic Integration)
- ✅ Basic OCR service with PyMuPDF for PDF processing
- ✅ Support for Textract's text detection
- ✅ Compatible with existing Pattern workflow
- ✅ Structured result objects for easier integration

### Phase 2: Enhanced Features (Future)
- 🔲 Support for table extraction and form recognition
- 🔲 Markdown output format for richer text representation
- 🔲 PDF processing options (resolution, format)
