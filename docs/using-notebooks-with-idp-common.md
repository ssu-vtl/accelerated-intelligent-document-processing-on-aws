Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

# Using Notebooks with IDP Common Library

This guide provides detailed instructions on how to use existing notebooks and create new notebooks for experimentation with the IDP Common Library.

<<<<<<< HEAD
## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Setting Up Your Environment](#setting-up-your-environment)
  - [Installing the IDP Common Package](#installing-the-idp-common-package)
  - [Configuring Environment Variables](#configuring-environment-variables)
- [Using Existing Notebooks](#using-existing-notebooks)
  - [Available Example Notebooks](#available-example-notebooks)
  - [Running Example Notebooks](#running-example-notebooks)
- [Creating New Notebooks](#creating-new-notebooks)
  - [Basic Structure](#basic-structure)
  - [Common Patterns](#common-patterns)
  - [Best Practices](#best-practices)
- [Common Use Cases](#common-use-cases)
  - [Working with Bedrock Client](#working-with-bedrock-client)
  - [OCR Processing](#ocr-processing)
  - [Document Classification](#document-classification)
  - [Information Extraction](#information-extraction)
  - [Evaluation](#evaluation)
  - [Bedrock Data Automation (BDA)](#business-document-analysis-bda)
- [Tips and Troubleshooting](#tips-and-troubleshooting)
- [Advanced Topics](#advanced-topics)
  - [Working with Custom Models](#working-with-custom-models)
  - [Performance Optimization](#performance-optimization)
  - [Integration with Other AWS Services](#integration-with-other-aws-services)

## Introduction

Jupyter Notebooks provide an interactive environment for experimenting with and testing the IDP Common Library. They allow you to:

- Test individual components of the IDP pipeline
- Experiment with different configurations and parameters
- Process documents end-to-end in a controlled environment
- Evaluate extraction results and calculate accuracy metrics
- Visualize outputs and debug issues

The IDP Common Library provides a unified Document model and modular services for OCR, classification, extraction, and evaluation, making it ideal for notebook-based experimentation.

## Getting Started

### Setting Up Your Environment

1. Ensure you have Jupyter installed in your environment:
   ```bash
   pip install jupyter
   ```

2. Navigate to the notebooks directory:
   ```bash
   cd notebooks
   ```

3. Launch Jupyter:
   ```bash
   jupyter notebook
   ```

### Installing the IDP Common Package

The IDP Common package should be installed in development mode to make changes immediately available without reinstallation:

```python
# First uninstall any existing version
%pip uninstall -y idp_common

# Install in development mode with all components
%pip install -q -e "../lib/idp_common_pkg[dev, all]"
```

For specific components only:

```python
# Install only specific components
%pip install -q -e "../lib/idp_common_pkg[ocr,classification,extraction]"
```

### Configuring Environment Variables

Create a `.env` file in the notebooks directory to store your AWS configuration:

```bash
# Sample .env file
AWS_REGION=us-east-1
METRIC_NAMESPACE=IDP-Notebook-Example
IDP_INPUT_BUCKET_NAME=my-input-bucket
IDP_OUTPUT_BUCKET_NAME=my-output-bucket
```

Load these variables in your notebook:

```python
try:
    from dotenv import load_dotenv
    load_dotenv()  
except ImportError:
    pass  
```

## Using Existing Notebooks

### Available Example Notebooks

The IDP Accelerator provides several example notebooks:

| Notebook | Description |
|----------|-------------|
| `evaluation_methods_demo.ipynb` | Demonstrates various evaluation methods for comparing extraction results |
| `e2e-example-with-multimodal-page-classification.ipynb` | End-to-end document processing example using multimodal page classification |
| `e2e-example-with-multimodal-page-classification-few-shot-prompting.ipynb` | Example using few-shot prompting with multimodal page classification |
| `e2e-holistic-packet-classification.ipynb` | End-to-end processing using holistic document classification |
| `e2e-holistic-packet-classification-summarization.ipynb` | Document classification and summarization example |
| `test_few_shot_classification.ipynb` | Demonstrates few-shot learning for document classification |
| `test_few_shot_extraction.ipynb` | Demonstrates few-shot learning for information extraction |
| `bedrock_client_test.ipynb` | Test notebook for the Bedrock client |
| `bedrock_client_cachepoint_test.ipynb` | Test notebook for the Bedrock client with caching functionality |
| `bda/kie-bda-happy-path.ipynb` | Example using Bedrock Data Automation (BDA) for key information extraction |

### Running Example Notebooks

1. Open the desired notebook in Jupyter.
2. Review the notebook documentation and structure.
3. Execute the cells sequentially to understand the workflow.
4. Modify parameters as needed for your use case.

## Creating New Notebooks

### Basic Structure

A typical IDP notebook follows this structure:

1. **Setup and Imports**
   ```python
   %load_ext autoreload
   %autoreload 2
   
   # Install the IDP common package
   %pip install -q -e "../lib/idp_common_pkg[dev, all]"
   
   # Import core libraries
   import os
   import json
   import boto3
   import logging
   from idp_common.models import Document, Status, Section
   from idp_common import ocr, classification, extraction, evaluation
   
   # Configure logging
   logging.basicConfig(level=logging.INFO)
   ```

2. **Environment Configuration**
   ```python
   # Load environment variables
   from dotenv import load_dotenv
   load_dotenv()
   
   # Set up AWS environment
   region = os.environ.get('AWS_REGION', 'us-east-1')
   input_bucket = os.environ.get('IDP_INPUT_BUCKET_NAME')
   output_bucket = os.environ.get('IDP_OUTPUT_BUCKET_NAME')
   ```

3. **IDP Configuration**
   ```python
   # Define configuration similar to what would be in DynamoDB
   CONFIG = {
       "classes": [...],
       "classification": {...},
       "extraction": {...},
       "evaluation": {...}
   }
   ```

4. **Document Processing**
   ```python
   # Initialize document
   document = Document(
       id="my-document",
       input_bucket=input_bucket,
       input_key="document.pdf",
       output_bucket=output_bucket
   )
   
   # Process with OCR
   ocr_service = ocr.OcrService()
   document = ocr_service.process_document(document)
   
   # Classify document
   classification_service = classification.ClassificationService(config=CONFIG)
   document = classification_service.classify_document(document)
   
   # Extract information
   extraction_service = extraction.ExtractionService(config=CONFIG)
   for section in document.sections:
       document = extraction_service.process_document_section(document, section.section_id)
   ```

5. **Results Analysis**
   ```python
   # Display results
   for section in document.sections:
       print(f"Section: {section.section_id}, Class: {section.classification}")
       if section.attributes:
           print(json.dumps(section.attributes, indent=2))
   ```

### Common Patterns

1. **Document Creation Pattern**
   ```python
   document = Document(
       id="doc-id",
       input_bucket="my-bucket",
       input_key="document.pdf",
       output_bucket="output-bucket"
   )
   ```

2. **Service Initialization Pattern**
   ```python
   # OCR with enhanced features
   ocr_service = ocr.OcrService(
       enhanced_features=["TABLES", "FORMS", "LAYOUT"]
   )
   
   # Classification with Bedrock backend
   classification_service = classification.ClassificationService(
       config=CONFIG,
       backend="bedrock"  # or "sagemaker"
   )
   
   # Extraction service
   extraction_service = extraction.ExtractionService(config=CONFIG)
   
   # Evaluation service
   evaluation_service = evaluation.EvaluationService(config=CONFIG)
   ```

3. **Processing Pattern**
   ```python
   # Each service operation takes a document and returns an updated document
   document = ocr_service.process_document(document)
   document = classification_service.classify_document(document)
   document = extraction_service.process_document_section(document, "section-1")
   ```

4. **Evaluation Pattern**
   ```python
   # Create expected document
   expected_document = Document.from_s3(bucket="baseline", input_key=document.input_key)
   
   # Evaluate results
   document = evaluation_service.evaluate_document(document, expected_document)
   
   # Access evaluation report
   report_uri = document.evaluation_report_uri
   ```

### Best Practices

1. **Use Autoreload**
   ```python
   %load_ext autoreload
   %autoreload 2
   ```
   This ensures that code changes in the library are automatically reloaded.

2. **Modular Configuration**
   Keep configuration sections separate for easy modification:
   ```python
   OCR_CONFIG = {...}
   CLASSIFICATION_CONFIG = {...}
   EXTRACTION_CONFIG = {...}
   ```

3. **Error Handling**
   ```python
   try:
       document = ocr_service.process_document(document)
   except Exception as e:
       print(f"OCR processing failed: {str(e)}")
       # Handle failure
   ```

4. **Performance Metrics**
   ```python
   import time
   
   start_time = time.time()
   document = ocr_service.process_document(document)
   ocr_time = time.time() - start_time
   
   print(f"OCR processing completed in {ocr_time:.2f} seconds")
   ```

5. **Resource Cleanup**
   ```python
   def cleanup_s3_objects(bucket, prefix):
       s3_client = boto3.client('s3')
       response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
       if 'Contents' in response:
           for obj in response['Contents']:
               s3_client.delete_object(Bucket=bucket, Key=obj['Key'])
   
   # Clean up at the end of the notebook
   cleanup_s3_objects(output_bucket, document.id)
   ```

## Common Use Cases

### Working with Bedrock Client

The IDP Common Library provides a robust Bedrock client implementation with built-in retry logic and caching capabilities. Two example notebooks demonstrate these features:

```python
# Import the Bedrock client functionality
from idp_common.bedrock import get_bedrock_client, invoke_model, get_model_id

# Get a configured Bedrock client
bedrock_client = get_bedrock_client()

# Basic model invocation
response = invoke_model(
    model_id="us.amazon.nova-lite-v1:0",
    prompt="Summarize the following document: {text}",
    temperature=0.0,
    top_k=5,
    max_tokens=1000
)

# With caching for improved performance
# The cachepoint tag in the prompt marks where the prompt should be split for caching
prompt = """System: You are a document classifier.
User: Classify this document as either invoice, letter, or form.

<<CACHEPOINT>>

Document content: {document_text}
"""

# The invoke_model function automatically handles caching when it detects the CACHEPOINT tag
response = invoke_model(
    model_id="us.amazon.nova-lite-v1:0",
    prompt=prompt.format(document_text="Sample document content..."),
    temperature=0.0,
    top_k=5,
    max_tokens=100
)
```

The `bedrock_client_test.ipynb` notebook demonstrates basic Bedrock client usage, while `bedrock_client_cachepoint_test.ipynb` shows how to leverage the caching functionality using the CACHEPOINT marker in prompts.

Benefits of the idp_common Bedrock client:
- Automatic retries with exponential backoff for transient errors
- Response caching for improved performance and cost reduction
- Support for streaming responses
- Standardized error handling
- Track token usage for cost monitoring

### OCR Processing

Example for extracting text from documents:

```python
# For basic text extraction
ocr_service = ocr.OcrService()
document = ocr_service.process_document(document)

# For enhanced features
ocr_service = ocr.OcrService(
    enhanced_features=["TABLES", "FORMS", "SIGNATURES", "LAYOUT"]
)
document = ocr_service.process_document(document)

# Access extracted text
for page_id, page in document.pages.items():
    print(f"Page {page_id}:")
    
    # Load text from S3
    raw_text = s3.get_json_content(page.raw_text_uri)
    print(raw_text)
    
    # Access tables if extracted
    for table in page.tables:
        print(f"Table: {json.dumps(table, indent=2)}")
```

### Document Classification

Example for classifying documents:

```python
# Text-based classification
classification_service = classification.ClassificationService(
    config=CONFIG,
    backend="bedrock"
)
document = classification_service.classify_document(document)

# Multimodal classification (text + images)
config = {
    "classification": {
        "classificationMethod": "multimodalPageLevelClassification",
        "model": "us.amazon.nova-pro-v1:0"
        # other configuration...
    }
}
classification_service = classification.ClassificationService(
    config=config,
    backend="bedrock"
)
document = classification_service.classify_document(document)

# Access classification results
for section in document.sections:
    print(f"Section {section.section_id}: {section.classification} (confidence: {section.confidence})")
    print(f"  Pages: {section.page_ids}")
```

### Information Extraction

Example for extracting structured data:

```python
# Configure extraction
extraction_service = extraction.ExtractionService(config=CONFIG)

# Process each section
for section in document.sections:
    document = extraction_service.process_document_section(
        document=document,
        section_id=section.section_id
    )

# Access extracted attributes
for section in document.sections:
    if section.extraction_result_uri:
        # Load extraction results from S3
        extraction_results = s3.get_json_content(section.extraction_result_uri)
        print(f"Section {section.section_id} ({section.classification}):")
        print(json.dumps(extraction_results, indent=2))
```

### Evaluation

Example for evaluating extraction results:

```python
# Define expected results
expected_results = {
    "section-1": {
        "customer_name": "John Smith",
        "invoice_number": "INV-12345",
        "total_amount": 1250.00
    }
}

# Create expected document
expected_document = create_ground_truth_document(document, expected_results)

# Evaluate results
evaluation_service = evaluation.EvaluationService(config=CONFIG)
document = evaluation_service.evaluate_document(document, expected_document)

# Display results
print(f"Evaluation report: {document.evaluation_report_uri}")
print(f"Overall metrics: {document.evaluation_result.overall_metrics}")
```

### Bedrock Data Automation (BDA)

The IDP Common Library provides integration with Amazon Bedrock Data Automation (BDA) capabilities, which offers built-in extraction for common business document types like invoices, receipts, and more.

Example for using BDA for key information extraction:

```python
# Import BDA modules
from idp_common.bda import BDAService
from idp_common.models import Document

# Create a document
document = Document(
    id="invoice-doc-001",
    input_bucket="my-input-bucket",
    input_key="invoices/sample.pdf",
    output_bucket="my-output-bucket"
)

# Initialize BDA service
bda_service = BDAService(
    region="us-east-1",
    analyze_expense=True,  # For receipts/expense documents
    analyze_lending=True   # For lending documents (W2, paystubs, etc.)
)

# Process document with BDA
document = bda_service.process_document(document)

# Access extracted BDA data
for page_id, page in document.pages.items():
    # Access expense fields
    if hasattr(page, 'expense_fields'):
        print(f"Expense fields for page {page_id}:")
        for field in page.expense_fields:
            print(f"{field['Type']['Text']}: {field['ValueDetection']['Text']}")
    
    # Access lending fields
    if hasattr(page, 'lending_fields'):
        print(f"Lending fields for page {page_id}:")
        for field in page.lending_fields:
            print(f"{field['Type']['Text']}: {field['ValueDetection']['Text']}")
```

The `bda/kie-bda-happy-path.ipynb` notebook demonstrates a complete workflow using BDA for key information extraction:

1. Setting up the necessary AWS resources and permissions
2. Processing documents with BDA
3. Parsing and normalizing BDA results
4. Storing and visualizing the structured data

Key benefits of using BDA:

- Built-in extractors for common business documents
- No need for training custom models
- High accuracy for supported document types
- Integration with the Document model for consistent workflows
- Support for a wide range of document types:
  - Invoices and receipts
  - Tax documents (W-2, 1099)
  - Bank statements
  - Paystubs
  - ID documents

## Tips and Troubleshooting

### Common Issues

1. **Missing Dependencies**
   
   If you encounter import errors, ensure you have installed the correct components:
   ```python
   %pip install -q -e "../lib/idp_common_pkg[dev, all]"
   ```

2. **S3 Access Issues**
   
   Ensure your AWS credentials have permission to access the specified buckets:
   ```python
   # Check bucket access
   s3_client = boto3.client('s3')
   try:
       s3_client.head_bucket(Bucket=bucket_name)
       print("Bucket access confirmed")
   except Exception as e:
       print(f"Bucket access error: {str(e)}")
   ```

3. **Bedrock Model Access**
   
   Verify you have access to the Bedrock models:
   ```python
   # List available models
   from idp_common.bedrock import get_bedrock_client
   
   bedrock_client = get_bedrock_client()
   response = bedrock_client.list_foundation_models()
   for model in response['modelSummaries']:
       print(f"{model['modelId']}: {model['modelName']}")
   ```

4. **Debug Logging**
   
   Enable detailed logging:
   ```python
   import logging
   
   # Configure logging
   logging.basicConfig(level=logging.DEBUG)
   logging.getLogger('idp_common').setLevel(logging.DEBUG)
   ```

### Debugging Techniques

1. **Inspect Document State**
   
   Print the document's state at different stages:
   ```python
   print(f"Status: {document.status.value}")
   print(f"Pages: {len(document.pages)}")
   print(f"Sections: {len(document.sections)}")
   
   # Convert to dictionary for easier inspection
   document_dict = document.to_dict()
   print(json.dumps(document_dict, indent=2))
   ```

2. **Examine S3 Content**
   
   Inspect files stored in S3:
   ```python
   def view_s3_content(uri):
       bucket, key = parse_s3_uri(uri)
       response = s3_client.get_object(Bucket=bucket, Key=key)
       content = response['Body'].read().decode('utf-8')
       try:
           return json.loads(content)
       except:
           return content
   
   # View extraction results
   for section in document.sections:
       if section.extraction_result_uri:
           print(view_s3_content(section.extraction_result_uri))
   ```

3. **Test Individual Components**
   
   Isolate components for testing:
   ```python
   # Test OCR only
   ocr_document = Document(input_bucket=bucket, input_key=key, output_bucket=output_bucket)
   ocr_document = ocr_service.process_document(ocr_document)
   
   # Test classification only with pre-processed text
   classification_document = Document(input_bucket=bucket, input_key=key, output_bucket=output_bucket)
   classification_document.pages = ocr_document.pages  # Copy pages with OCR results
   classification_document = classification_service.classify_document(classification_document)
   ```

## Advanced Topics

### Working with Custom Models

Example for using your own models:

```python
# SageMaker classification
classification_service = classification.ClassificationService(
    config=CONFIG,
    backend="sagemaker",
    endpoint_name="my-custom-classifier"
)

# Custom model configuration
custom_config = {
    "classification": {
        "classificationMethod": "textbasedHolisticClassification",
        "endpoint_name": "my-custom-endpoint",
        "region": "us-east-1"
    }
}
```

### Performance Optimization

Tips for optimizing performance:

```python
# Parallel processing for multiple documents
from concurrent.futures import ThreadPoolExecutor

def process_document(doc_key):
    doc = Document(input_bucket=bucket, input_key=doc_key, output_bucket=output_bucket)
    doc = ocr_service.process_document(doc)
    doc = classification_service.classify_document(doc)
    return doc

document_keys = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_document, document_keys))
```

### Integration with Other AWS Services

Example for integrating with other AWS services:

```python
# Amazon Comprehend for entity extraction
def extract_entities(text):
    comprehend = boto3.client('comprehend')
    response = comprehend.detect_entities(
        Text=text,
        LanguageCode='en'
    )
    return response['Entities']

# Process each page
for page_id, page in document.pages.items():
    text = s3.get_text_content(page.raw_text_uri)
    entities = extract_entities(text)
    print(f"Entities in page {page_id}:")
    print(entities)
```

## Conclusion

Notebooks provide an excellent environment for experimenting with the IDP Common Library. By following the patterns and best practices outlined in this guide, you can:

- Test various components of the IDP pipeline
- Develop custom processing workflows
- Evaluate accuracy and performance
- Iterate quickly on improvements

The modular architecture of the IDP Common Library makes it easy to experiment with different configurations and approaches, while the unified Document model ensures consistent data flow throughout the processing pipeline.
=======
The /notebooks/examples directory contains a complete set of modular Jupyter notebooks that demonstrate the Intelligent Document Processing (IDP) pipeline using the `idp_common` library. Each notebook represents a distinct step in the IDP workflow and can be run independently or sequentially.

## 🏗️ Architecture Overview

The modular approach breaks down the IDP pipeline into discrete, manageable steps:

```
Step 0: Setup → Step 1: OCR → Step 2: Classification → Step 3: Extraction → Step 4: Assessment → Step 5: Summarization → Step 6: Evaluation
```

### Key Benefits

- **Independent Execution**: Each step can be run and tested independently
- **Modular Configuration**: Separate YAML configuration files for different components
- **Data Persistence**: Each step saves results for the next step to consume
- **Easy Experimentation**: Modify configurations without changing code
- **Comprehensive Evaluation**: Professional-grade evaluation with the EvaluationService
- **Debugging Friendly**: Isolate issues to specific processing steps

## 📁 Directory Structure

```
notebooks/examples/
├── README.md                          # This file
├── step0_setup.ipynb                  # Environment setup and document initialization
├── step1_ocr.ipynb                    # OCR processing using Amazon Textract
├── step2_classification.ipynb         # Document classification 
├── step3_extraction.ipynb             # Structured data extraction
├── step4_assessment.ipynb             # Confidence assessment and explainability
├── step5_summarization.ipynb          # Content summarization
├── step6_evaluation.ipynb             # Final evaluation and reporting
├── config/                            # Modular configuration files
│   ├── main.yaml                      # Main pipeline configuration
│   ├── classes.yaml                   # Document classification definitions
│   ├── ocr.yaml                       # OCR service configuration
│   ├── classification.yaml            # Classification method configuration
│   ├── extraction.yaml                # Extraction method configuration
│   ├── assessment.yaml                # Assessment method configuration
│   ├── summarization.yaml             # Summarization method configuration
│   └── evaluation.yaml                # Evaluation method configuration
└── data/                              # Step-by-step processing results
    ├── step0_setup/                   # Setup outputs
    ├── step1_ocr/                     # OCR results
    ├── step2_classification/          # Classification results
    ├── step3_extraction/              # Extraction results
    ├── step4_assessment/              # Assessment results
    ├── step5_summarization/           # Summarization results
    └── step6_evaluation/              # Final evaluation results
```

## 🚀 Quick Start

### Prerequisites

1. **AWS Credentials**: Ensure your AWS credentials are configured
2. **Required Libraries**: Install the `idp_common` package
3. **Sample Document**: Place a PDF file in the project samples directory

### Running the Complete Pipeline

Execute the notebooks in sequence:

```bash
# 1. Setup environment and document
jupyter notebook step0_setup.ipynb

# 2. Process OCR
jupyter notebook step1_ocr.ipynb

# 3. Classify document sections
jupyter notebook step2_classification.ipynb

# 4. Extract structured data
jupyter notebook step3_extraction.ipynb

# 5. Assess confidence and explainability
jupyter notebook step4_assessment.ipynb

# 6. Generate summaries
jupyter notebook step5_summarization.ipynb

# 7. Evaluate results and generate reports
jupyter notebook step6_evaluation.ipynb
```

### Running Individual Steps

Each notebook can be run independently by ensuring the required input data exists:

```python
# Each notebook loads its inputs from the previous step's data directory
previous_step_dir = Path("data/step{n-1}_{previous_step_name}")
```

## ⚙️ Configuration Management

### Modular Configuration Files

Configuration is split across multiple YAML files for better organization:

- **`config/main.yaml`**: Overall pipeline settings and AWS configuration
- **`config/classes.yaml`**: Document type definitions and attributes to extract
- **`config/ocr.yaml`**: Textract features and OCR-specific settings  
- **`config/classification.yaml`**: Classification model and method configuration
- **`config/extraction.yaml`**: Extraction model and prompting configuration
- **`config/assessment.yaml`**: Assessment model and confidence thresholds
- **`config/summarization.yaml`**: Summarization models and output formats
- **`config/evaluation.yaml`**: Evaluation metrics and reporting settings

### Configuration Loading

Each notebook automatically merges all configuration files:

```python
# Automatic configuration loading in each notebook
CONFIG = load_and_merge_configs("config/")
```

### Experimentation with Configurations

To experiment with different settings:

1. **Backup Current Config**: Copy the config directory
2. **Modify Settings**: Edit the relevant YAML files
3. **Run Specific Steps**: Execute only the affected notebooks
4. **Compare Results**: Review outputs in the data directories

## 📊 Data Flow

### Input/Output Structure

Each step follows a consistent pattern:

```python
# Input (from previous step)
input_data_dir = Path("data/step{n-1}_{previous_name}")
document = Document.from_json((input_data_dir / "document.json").read_text())
config = json.load(open(input_data_dir / "config.json"))

# Processing
# ... step-specific processing ...

# Output (for next step)
output_data_dir = Path("data/step{n}_{current_name}")
output_data_dir.mkdir(parents=True, exist_ok=True)
(output_data_dir / "document.json").write_text(document.to_json())
json.dump(config, open(output_data_dir / "config.json", "w"))
```

### Serialized Artifacts

Each step produces:
- **`document.json`**: Updated Document object with step results
- **`config.json`**: Complete merged configuration  
- **`environment.json`**: Environment settings and metadata
- **Step-specific result files**: Detailed processing outputs

## 🔬 Detailed Step Descriptions

### Step 0: Setup (`step0_setup.ipynb`)
- **Purpose**: Initialize the Document object and prepare the processing environment
- **Inputs**: PDF file path, configuration files
- **Outputs**: Document object with pages and metadata
- **Key Features**: Multi-page PDF support, metadata extraction

### Step 1: OCR (`step1_ocr.ipynb`)
- **Purpose**: Extract text and analyze document structure using Amazon Textract
- **Inputs**: Document object with PDF pages
- **Outputs**: OCR results with text blocks, tables, and forms
- **Key Features**: Textract API integration, feature selection, result caching

### Step 2: Classification (`step2_classification.ipynb`)
- **Purpose**: Identify document types and create logical sections
- **Inputs**: Document with OCR results
- **Outputs**: Classified sections with confidence scores
- **Key Features**: Multi-modal classification, few-shot prompting, custom classes

### Step 3: Extraction (`step3_extraction.ipynb`)
- **Purpose**: Extract structured data from each classified section
- **Inputs**: Document with classified sections
- **Outputs**: Structured data for each section based on class definitions
- **Key Features**: Class-specific extraction, JSON schema validation

### Step 4: Assessment (`step4_assessment.ipynb`)
- **Purpose**: Evaluate extraction confidence and provide explainability
- **Inputs**: Document with extraction results
- **Outputs**: Confidence scores and reasoning for each extracted attribute
- **Key Features**: Confidence assessment, hallucination detection, explainability

### Step 5: Summarization (`step5_summarization.ipynb`)
- **Purpose**: Generate human-readable summaries of processing results
- **Inputs**: Document with assessed extractions
- **Outputs**: Section and document-level summaries in multiple formats
- **Key Features**: Multi-format output (JSON, Markdown, HTML), customizable templates

### Step 6: Evaluation (`step6_evaluation.ipynb`)
- **Purpose**: Comprehensive evaluation of pipeline performance and accuracy
- **Inputs**: Document with complete processing results
- **Outputs**: Evaluation reports, accuracy metrics, performance analysis
- **Key Features**: EvaluationService integration, ground truth comparison, detailed reporting

## 🧪 Experimentation Guide

### Modifying Document Classes

To add new document types or modify existing ones:

1. **Edit `config/classes.yaml`**:
```yaml
classes:
  new_document_type:
    description: "Description of the new document type"
    attributes:
      - name: "attribute_name"
        description: "What this attribute represents"
        type: "string"  # or "number", "date", etc.
```

2. **Run from Step 2**: Classification onwards to process with new classes

### Changing Models

To experiment with different AI models:

1. **Edit relevant config files**:
```yaml
# In config/extraction.yaml
llm_method:
  model: "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Change model
  temperature: 0.1  # Adjust parameters
```

2. **Run affected steps**: Only the steps that use the changed configuration

### Adjusting Confidence Thresholds

To experiment with confidence thresholds:

1. **Edit `config/assessment.yaml`**:
```yaml
assessment:
  confidence_threshold: 0.7  # Lower threshold = more permissive
```

2. **Run Steps 4-6**: Assessment, Summarization, and Evaluation

### Performance Optimization

- **Parallel Processing**: Modify extraction/assessment to process sections in parallel
- **Caching**: Results are automatically cached between steps
- **Batch Processing**: Process multiple documents by running the pipeline multiple times

## 🐛 Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure proper AWS configuration
```bash
aws configure list
```

2. **Missing Dependencies**: Install required packages
```bash
pip install boto3 jupyter ipython
```

3. **Memory Issues**: For large documents, consider processing sections individually

4. **Configuration Errors**: Validate YAML syntax
```bash
python -c "import yaml; yaml.safe_load(open('config/main.yaml'))"
```

### Debug Mode

Enable detailed logging in any notebook:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Data Inspection

Each step saves detailed results that can be inspected:
```python
# Inspect intermediate results
import json
with open("data/step3_extraction/extraction_summary.json") as f:
    results = json.load(f)
    print(json.dumps(results, indent=2))
```

## 📈 Performance Monitoring

### Metrics Tracked

Each step automatically tracks:
- **Processing Time**: Total time for the step
- **Throughput**: Pages per second
- **Memory Usage**: Peak memory consumption
- **API Calls**: Number of service calls made
- **Error Rates**: Failed operations

### Performance Analysis

The evaluation step provides comprehensive performance analysis:
- Step-by-step timing breakdown
- Bottleneck identification  
- Resource utilization metrics
- Cost analysis (for AWS services)

## 🔒 Security and Best Practices

### AWS Security
- Use IAM roles with minimal required permissions
- Enable CloudTrail for API logging
- Store sensitive data in S3 with appropriate encryption

### Data Privacy
- Documents are processed in your AWS account
- No data is sent to external services (except configured AI models)
- Temporary files are cleaned up automatically

### Configuration Management
- Version control your configuration files
- Use environment-specific configurations for different deployments
- Document any custom modifications

## 🤝 Contributing

To extend or modify the notebooks:

1. **Follow the Pattern**: Maintain the input/output structure for compatibility
2. **Update Configurations**: Add new configuration options to appropriate YAML files
3. **Document Changes**: Update this README and add inline documentation
4. **Test Thoroughly**: Verify that changes work across the entire pipeline

## 📚 Additional Resources

- [IDP Common Library Documentation](../docs/using-notebooks-with-idp-common.md)
- [Configuration Guide](../docs/configuration.md)
- [Evaluation Methods](../docs/evaluation.md)
- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

---

**Happy Document Processing! 🚀**

For questions or support, refer to the main project documentation or create an issue in the project repository.
>>>>>>> origin/develop
