# Reporting Module

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

## Overview

The Reporting module provides functionality for saving document data to reporting storage in structured formats for analytics and reporting purposes. It currently supports saving evaluation results as Parquet files in S3, with a flexible architecture that can be extended to support additional data types in the future.

## Key Components

### SaveReportingData Class

The `SaveReportingData` class is the main component of the reporting module. It provides methods to save different types of document data to a reporting bucket in Parquet format.

```python
from idp_common.reporting import SaveReportingData
from idp_common.models import Document

# Initialize the SaveReportingData class with a reporting bucket
reporter = SaveReportingData(reporting_bucket="my-reporting-bucket")

# Save specific data types for a document
results = reporter.save(document, data_to_save=["evaluation_results"])
```

## Features

- **Modular Design**: Each data type has its own processing method, making it easy to add support for new data types
- **Parquet Format**: Data is saved in Parquet format, which is optimized for analytics workloads
- **Hierarchical Storage**: Data is organized in a hierarchical structure by year/month/day/document
- **Flexible Schema**: Each data type has its own schema definition, allowing for specialized data structures
- **Error Handling**: Comprehensive error handling with detailed logging

## Supported Data Types

### Evaluation Results

The module currently supports saving document evaluation results, which include:

1. **Document-level metrics**: Overall accuracy, precision, recall, F1 score, etc.
2. **Section-level metrics**: Metrics for each document section
3. **Attribute-level details**: Detailed information about each attribute, including expected vs. actual values, match status, and confidence

```python
# Save evaluation results for a document
result = reporter.save_evaluation_results(document)
```

## Storage Structure

Data is stored in S3 with the following structure:

```
reporting-bucket/
├── evaluation_metrics/
│   ├── document_metrics/
│   │   └── year=YYYY/
│   │       └── month=MM/
│   │           └── day=DD/
│   │               └── document=doc-id/
│   │                   └── results.parquet
│   ├── section_metrics/
│   │   └── year=YYYY/
│   │       └── month=MM/
│   │           └── day=DD/
│   │               └── document=doc-id/
│   │                   └── results.parquet
│   └── attribute_metrics/
│       └── year=YYYY/
│           └── month=MM/
│               └── day=DD/
│                   └── document=doc-id/
│                       └── results.parquet
```

This structure is designed to be compatible with AWS Glue and Amazon Athena for analytics.

## Extending the Module

To add support for a new data type:

1. Add a new method to the `SaveReportingData` class:

```python
def save_document_metadata(self, document: Document) -> Optional[Dict[str, Any]]:
    """
    Save document metadata to the reporting bucket.
    
    Args:
        document: Document object containing metadata
        
    Returns:
        Dict with status and message, or None if no metadata
    """
    # Define schema specific to document metadata
    metadata_schema = pa.schema([
        ('document_id', pa.string()),
        ('input_key', pa.string()),
        ('created_at', pa.timestamp('ms')),
        ('page_count', pa.int32()),
        ('file_size', pa.int64()),
        # Add other metadata fields as needed
    ])
    
    # Implementation for saving document metadata
    # ...
    
    return {
        'statusCode': 200,
        'body': "Successfully saved document metadata"
    }
```

2. Update the `save` method to call this new method when the data type is requested:

```python
if 'document_metadata' in data_to_save:
    logger.info("Processing document metadata")
    result = self.save_document_metadata(document)
    if result:
        results.append(result)
```

## Usage in Lambda Functions

The module is designed to be used in Lambda functions for saving document data to reporting storage:

```python
from idp_common.models import Document
from idp_common.reporting import SaveReportingData

def handler(event, context):
    # Extract parameters from the event
    document_dict = event.get('document')
    reporting_bucket = event.get('reporting_bucket')
    data_to_save = event.get('data_to_save', [])
    
    # Convert document dict to Document object
    document = Document.from_dict(document_dict)
    
    # Use the SaveReportingData class to save the data
    reporter = SaveReportingData(reporting_bucket)
    results = reporter.save(document, data_to_save)
    
    # Return success if all operations completed
    return {
        'statusCode': 200,
        'body': "Successfully saved data to reporting bucket"
    }
```

## Dependencies

The reporting module has the following dependencies:

- `boto3`: For AWS S3 operations
- `pyarrow`: For Parquet file creation and schema definition
- `idp_common.models`: For the Document data model

When deploying Lambda functions that use this module, ensure that these dependencies are included in the deployment package.
