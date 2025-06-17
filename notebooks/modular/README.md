# Modular IDP Pipeline

This directory contains a modular implementation of the Intelligent Document Processing (IDP) pipeline, breaking down the complete workflow into independent, sequential steps.

## Overview

The modular approach allows developers to:
- Run each step independently for testing and debugging
- Experiment with different configurations per step
- Save intermediate results for analysis
- Create custom variations of any step

## Pipeline Steps

The pipeline consists of 7 notebooks that should be run sequentially:

### Step 0: Setup (`step0_setup.ipynb`)
- **Purpose**: Initialize environment and prepare document for processing
- **Inputs**: Sample PDF file, environment configuration
- **Outputs**: Document object, S3 buckets, uploaded sample file
- **Data Directory**: `data/step0_setup/`

### Step 1: OCR (`step1_ocr.ipynb`)
- **Purpose**: Extract text and images from PDF using AWS Textract
- **Inputs**: Document object from Step 0, OCR configuration
- **Outputs**: Document with OCR results, page-level text and images
- **Data Directory**: `data/step1_ocr/`

### Step 2: Classification (`step2_classification.ipynb`)
- **Purpose**: Identify document types and sections using AWS Bedrock
- **Inputs**: Document with OCR results, classification configuration, document classes
- **Outputs**: Document with classification results, identified sections
- **Data Directory**: `data/step2_classification/`

### Step 3: Extraction (`step3_extraction.ipynb`)
- **Purpose**: Extract structured data from classified sections
- **Inputs**: Document with classifications, extraction configuration, attribute definitions
- **Outputs**: Document with extracted structured data
- **Data Directory**: `data/step3_extraction/`

### Step 4: Assessment (`step4_assessment.ipynb`)
- **Purpose**: Evaluate confidence and accuracy of extractions
- **Inputs**: Document with extractions, assessment configuration, confidence thresholds
- **Outputs**: Document with confidence scores and reasoning
- **Data Directory**: `data/step4_assessment/`

### Step 5: Summarization (`step5_summarization.ipynb`)
- **Purpose**: Generate summaries of document content
- **Inputs**: Document with assessments, summarization configuration
- **Outputs**: Document with section and document-level summaries
- **Data Directory**: `data/step5_summarization/`

### Step 6: Evaluation (`step6_evaluation.ipynb`)
- **Purpose**: Final evaluation and comprehensive reporting
- **Inputs**: Complete processed document, evaluation configuration
- **Outputs**: Evaluation report, performance metrics, recommendations
- **Data Directory**: `data/step6_evaluation/`

## Configuration Files

All configuration is stored in modular YAML files in the `config/` directory:

- **`ocr.yaml`**: OCR processing settings and Textract features
- **`classification.yaml`**: Classification models and methods
- **`extraction.yaml`**: Extraction models and settings
- **`assessment.yaml`**: Confidence evaluation parameters
- **`summarization.yaml`**: Summarization models and output formats
- **`evaluation.yaml`**: Evaluation metrics and thresholds
- **`classes.yaml`**: Document classes and attribute definitions

## Data Flow

Each step:
1. Loads the document object from the previous step's `data/` directory
2. Loads configuration from the `config/` YAML files
3. Processes the document using the configured settings
4. Saves the updated document and step-specific results
5. Provides a summary and pointer to the next step

## Getting Started

1. **Run the notebooks sequentially**: Start with `step0_setup.ipynb` and proceed through each step
2. **Check outputs**: Each step saves results to its own `data/stepX_*/` directory
3. **Customize configuration**: Modify YAML files in `config/` to experiment with different settings
4. **Analyze results**: Each step provides detailed output and saves processing metrics

## Experimentation Tips

- **Model Comparison**: Change the `model` parameter in configuration files to compare different LLMs
- **Feature Testing**: Modify OCR features in `ocr.yaml` to test different Textract capabilities
- **Custom Classes**: Add new document types in `classes.yaml` with their own attributes
- **Confidence Tuning**: Adjust thresholds in `assessment.yaml` to optimize accuracy vs. coverage
- **Output Formats**: Experiment with different summary formats in `summarization.yaml`

## Directory Structure

```
notebooks/modular/
├── README.md                     # This file
├── step0_setup.ipynb             # Environment setup
├── step1_ocr.ipynb               # OCR processing
├── step2_classification.ipynb    # Document classification
├── step3_extraction.ipynb        # Information extraction
├── step4_assessment.ipynb        # Confidence assessment
├── step5_summarization.ipynb     # Content summarization
├── step6_evaluation.ipynb        # Final evaluation
├── config/                       # Configuration files
│   ├── ocr.yaml
│   ├── classification.yaml
│   ├── extraction.yaml
│   ├── assessment.yaml
│   ├── summarization.yaml
│   ├── evaluation.yaml
│   └── classes.yaml
└── data/                         # Generated data (created during execution)
    ├── step0_setup/
    ├── step1_ocr/
    ├── step2_classification/
    ├── step3_extraction/
    ├── step4_assessment/
    ├── step5_summarization/
    └── step6_evaluation/
```

## Key Benefits

1. **Modularity**: Each step is independent and can be run separately
2. **Flexibility**: Easy to swap models, adjust parameters, or skip steps
3. **Debugging**: Inspect intermediate results at each step
4. **Experimentation**: Compare different configurations side-by-side
5. **Reusability**: Create custom pipelines by combining different steps
6. **Traceability**: Complete audit trail of processing decisions and results

## Prerequisites

- AWS credentials configured
- Access to AWS Textract and Bedrock services
- IDP common library installed (`idp_common`)
- Jupyter notebook environment

Start your modular IDP journey with `step0_setup.ipynb`!
