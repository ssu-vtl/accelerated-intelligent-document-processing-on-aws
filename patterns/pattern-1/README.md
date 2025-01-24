# Pattern 1: UDOP Classification with Claude Extraction

This pattern implements an intelligent document processing workflow that uses UDOP (Unified Document Processing) for page classification and grouping, followed by Claude for information extraction.

<img src="../../images/IDP-Pattern1-UDOP.drawio.png" alt="Architecture" width="800">


## Table of Contents

- [Architecture Overview](#architecture-overview)
  - [State Machine Workflow](#state-machine-workflow)
  - [Lambda Functions](#lambda-functions)
    - [OCR Function](#ocr-function)
    - [Classification Function](#classification-function)
    - [Extraction Function](#extraction-function)
  - [UDOP Model on SageMaker](#udop-model-on-sagemaker)
  - [Monitoring and Metrics](#monitoring-and-metrics)
    - [Performance Metrics](#performance-metrics)
    - [Error Tracking](#error-tracking)
    - [Lambda Function Metrics](#lambda-function-metrics)
  - [Template Outputs](#template-outputs)
  - [Configuration](#configuration)
- [Testing](#testing)
- [Best Practices](#best-practices)

## Architecture Overview

The workflow consists of three main processing steps:
1. OCR processing using Amazon Textract
2. Page classification and grouping using a UDOP model deployed on SageMaker
3. Field extraction using Claude via Amazon Bedrock

### State Machine Workflow

The Step Functions state machine (`workflow.asl.json`) orchestrates the following flow:

```
OCRStep → ClassificationStep → ProcessPageGroups (Map State for Extraction)
```

Each step includes comprehensive retry logic for handling transient errors:
- Initial retry after 2 seconds
- Exponential backoff with rate of 2
- Maximum of 10 retry attempts

### Lambda Functions

#### OCR Function
- **Purpose**: Processes input PDFs using Amazon Textract
- **Input**:
  ```json
  {
    "execution_arn": "<ARN>",
    "working_bucket": "<BUCKET>",
    "input": {
      "detail": {
        "bucket": { "name": "<BUCKET>" },
        "object": { "key": "<KEY>" }
      }
    }
  }
  ```
- **Output**:
  ```json
  {
    "metadata": {
      "input_bucket": "<BUCKET>",
      "object_key": "<KEY>",
      "working_bucket": "<BUCKET>",
      "working_prefix": "<PREFIX>",
      "num_pages": "<NUMBER OF PAGES>"
    },
    "pages": {
      "<PAGE_NUMBER>": {
        "textract_document_text_raw_path": "<S3_URI>",
        "textract_document_text_parsed_path": "<S3_URI>",
        "image_path": "<S3_URI>"
      }
    }
  }
  ```

#### Classification Function 
- **Purpose**: Classifies pages using UDOP model on SageMaker
- **Input**: Output from OCR function plus output bucket
- **Output**: 
  ```json
  {
    "metadata": "<FROM_OCR>",
    "pagegroups": [
      {
        "id": "<GROUP_ID>",
        "document_type": "<CLASS>",
        "pages": [...]
      }
    ]
  }
  ```

#### Extraction Function
- **Purpose**: Extracts fields using Claude via Amazon Bedrock
- **Input**: Individual pagegroup from Classification output
- **Output**:
  ```json
  {
    "metadata": "<ORIGINAL_METADATA>",
    "extracted_entities": "<JSON_STRING>",
    "output_location": "s3://<bucket>/<prefix>/<id>_Pages_<N>_to_<M>.json"
  }
  ```

### UDOP Model on SageMaker

The pattern includes a complete UDOP model deployment:

- **Model Packaging**: `udop_model/package_model.py` handles:
  - Downloading UDOP model
  - Packaging with inference code
  - Creating SageMaker model archive

- **Inference Code**: `udop_model/inference_code/` contains:
  - `inference.py`: SageMaker entry points
  - `udop.py`: Model implementation
  - `utils.py`: Helper functions for preprocessing

- **SageMaker Endpoint**: `sagemaker_classifier_endpoint.yaml` provisions:
  - SageMaker model 
  - Endpoint configuration
  - Endpoint with auto-scaling
  - IAM roles and permissions

### Monitoring and Metrics

The pattern includes a dedicated CloudWatch dashboard with:

#### Performance Metrics
- Document and page counts
- Token usage (input/output/total)
- Bedrock request statistics
- Processing latencies

#### Error Tracking
- Lambda function errors
- Long-running invocations
- Classification/extraction failures

#### Lambda Function Metrics
- Duration
- Memory usage
- Error rates

### Template Outputs

The pattern exports these outputs to the parent stack:

- `StateMachineName`: Name of Step Functions state machine
- `StateMachineArn`: ARN of Step Functions state machine
- `StateMachineLogGroup`: CloudWatch log group for state machine
- `DashboardName`: Name of pattern-specific dashboard
- `DashboardArn`: ARN of pattern-specific dashboard

### Configuration

Key configurable parameters:

- `UDOPModelArtifactPath`: S3 path to UDOP model artifacts
- `ExtractionModel`: Bedrock model ID for extraction (Claude)
- `MaxConcurrentWorkflows`: Workflow concurrency limit
- `LogRetentionDays`: CloudWatch log retention period
- `ExecutionTimeThresholdMs`: Latency threshold for alerts

## Testing

Use the provided test events in `testing/`:

```bash
# Test OCR function
sam local invoke OCRFunction -e testing/OCRFunction-event.json

# Test classification
sam local invoke ClassificationFunction -e testing/ClassificationFunction-event.json

# Test extraction
sam local invoke ExtractionFunction -e testing/ExtractionFunction-event.json
```

## Best Practices

1. **Retry Handling**: All functions implement exponential backoff with jitter
2. **Metrics**: Comprehensive CloudWatch metrics for monitoring
3. **Error Tracking**: Detailed error logging with context
4. **Resource Management**: Efficient handling of memory and connections
5. **Security**: KMS encryption and least privilege IAM roles