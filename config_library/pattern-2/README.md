# Pattern 2 Configurations

This directory contains configurations for Pattern 2 of the GenAI IDP Accelerator, which uses Amazon Bedrock with Nova or Claude models for both page classification/grouping and information extraction.

## Pattern 2 Overview

Pattern 2 implements an intelligent document processing workflow that uses Amazon Bedrock with Nova or Claude models for both page classification/grouping and information extraction.

Key components of Pattern 2:
- OCR processing using Amazon Textract
- Document classification using Claude via Amazon Bedrock (with two available methods):
  - Page-level classification: Classifies individual pages and groups them
  - Holistic packet classification: Analyzes multi-document packets to identify document boundaries
- Field extraction using Claude via Amazon Bedrock

## Adding Configurations

To add a new configuration for Pattern 2:

1. Create a new directory with a descriptive name
2. Include a config.json file with the appropriate settings
3. Add a README.md file using the template from `../TEMPLATE_README.md`
4. Include sample documents in a samples/ directory

See the main [README.md](../README.md) for more detailed instructions on creating and contributing configurations.

## Available Configurations

- [default](./default/): Default configuration for general document processing
- [medical_records_summarization](./medical_records_summarization/): Specialized configuration for processing and summarizing medical records
