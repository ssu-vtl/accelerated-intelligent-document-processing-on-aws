Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

# Medical Records Summarization Configuration

This directory contains a specialized configuration for processing and summarizing medical records using the GenAI IDP Accelerator. This configuration is optimized for healthcare documents and provides enhanced summarization capabilities specifically for medical content.

## Pattern Association

**Pattern**: Pattern-2 - Uses Amazon Bedrock with Claude models for both page classification/grouping and information extraction

## Validation Level

**Level**: 1 - Basic Testing

- **Testing Evidence**: This configuration has been tested with a limited set of medical record documents. Initial results show promising performance in organizing and summarizing medical information.
- **Known Limitations**: Performance may vary with specialized medical document types or documents with complex medical terminology not represented in the test set.

## Overview

The medical records summarization configuration is designed to handle various types of healthcare documents, including:

- Visit summaries
- Medical histories
- Medical diagnoses
- Test results
- Televisit notes

It includes specialized document classes, attributes, and a medical-focused summarization prompt that organizes information into clinically relevant sections.

## Key Differences from Default Configuration

### 1. Document Classes

This configuration replaces the general business document classes with healthcare-specific document types:

- **Visit Summary**: Documentation of healthcare visits including reason, findings, and treatment plans
- **Medical History**: Patient health history and physical examination findings
- **Medical Diagnoses**: Lists of patient's current medical problems or diagnoses
- **Test Results**: Laboratory test or diagnostic procedure results
- **Televisit**: Documentation of telephone-based healthcare interactions

### 2. Model Selection

- Uses Claude 3.5 Sonnet (us.anthropic.claude-3-5-sonnet-20241022-v2:0) for classification, extraction, and summarization
- Provides higher accuracy for medical terminology and context compared to the default models

### 3. Summarization Prompt

The summarization prompt has been completely redesigned for medical documents:

- Organizes information into clinically relevant sections:
  - Patient Snapshot
  - Healthcare Providers
  - Impairments & Health Status
  - Encounters
  - Medications
  - Laboratory Results
  - Clinical Testing
  - Age-Related Screening
  - Administrative Forms
  - Health Metrics Trending

- Adds medical-specific features:
  - Medical code enrichment for conditions
  - Chronological ordering of encounters
  - Separation of current vs. discontinued medications
  - Linking of lab results to conditions
  - Age-appropriate screening highlights
  - Health metrics trending

## Sample Documents

Sample documents for this configuration will be added in a future update. These will demonstrate the configuration's effectiveness with various types of medical records.

## Key Benefits

- **Structured Medical Summaries**: Creates well-organized summaries with clinically relevant sections
- **Enhanced Medical Context**: Better understanding of medical terminology and relationships
- **Improved Information Linking**: Connects medications to conditions, lab results to encounters, etc.
- **Medical Code Integration**: Enriches conditions with standard medical codes when possible
- **Comprehensive Patient View**: Provides a holistic view of patient health information

## Example Output

The summarization output will be a JSON object with a comprehensive medical summary in markdown format, including:

- Color-coded sections for different types of medical information
- Hyperlinks to relevant sections of the original document
- Hover functionality for detailed source information
- Medical codes for conditions when available
- Chronological organization of encounters and results
- Trending information for key health metrics

This structured format makes it easy to quickly understand a patient's medical history and current status.

## Contributors

- GenAI IDP Accelerator Team
