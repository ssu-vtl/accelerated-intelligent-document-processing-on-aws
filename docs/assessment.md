# Assessment Feature

Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

## Overview

The Assessment feature provides automated confidence evaluation of document extraction results using Large Language Models (LLMs). This feature analyzes extraction outputs against source documents to provide confidence scores and explanations for each extracted attribute, helping users understand the reliability of automated extractions.

## Key Features

- **Multimodal Analysis**: Combines text analysis with document images for comprehensive confidence assessment
- **Per-Attribute Scoring**: Provides individual confidence scores and explanations for each extracted attribute
- **Token-Optimized Processing**: Uses condensed text confidence data for 80-90% token reduction compared to full OCR results
- **UI Integration**: Seamlessly displays assessment results in the web interface with explainability information
## Confidence Thresholds

### Overview

The assessment feature supports flexible confidence threshold configuration to help users identify extraction results that may require review. Thresholds can be set globally or per-attribute, with the UI providing immediate visual feedback through color-coded displays.

### Configuration Options

#### Global Thresholds
Set system-wide confidence requirements for all attributes:

```json
{
  "inference_result": {
    "YTDNetPay": "75000",
    "PayPeriodStartDate": "2024-01-01"
  },
  "explainability_info": [
    {
      "global_confidence_threshold": 0.85,
      "YTDNetPay": {
        "confidence": 0.92,
        "confidence_reason": "Clear match found in document"
      },
      "PayPeriodStartDate": {
        "confidence": 0.75,
        "confidence_reason": "Moderate OCR confidence"
      }
    }
  ]
}
```

#### Per-Attribute Thresholds
Override global settings for specific fields requiring different confidence levels:

```json
{
  "explainability_info": [
    {
      "YTDNetPay": {
        "confidence": 0.92,
        "confidence_threshold": 0.95,
        "confidence_reason": "Financial data requires high confidence"
      },
      "PayPeriodStartDate": {
        "confidence": 0.75,
        "confidence_threshold": 0.70,
        "confidence_reason": "Date fields can accept moderate confidence"
      }
    }
  ]
}
```

#### Mixed Configuration
Combine global defaults with attribute-specific overrides:

```json
{
  "explainability_info": [
    {
      "global_confidence_threshold": 0.80,
      "CriticalField": {
        "confidence": 0.85,
        "confidence_threshold": 0.95,
        "confidence_reason": "Override: higher threshold for critical data"
      },
      "StandardField": {
        "confidence": 0.82,
        "confidence_reason": "Uses global threshold of 0.80"
      }
    }
  ]
}
```

### Assessment Prompt Integration

Include threshold guidance in your assessment prompts to ensure consistent confidence evaluation:

```yaml
assessment:
  task_prompt: |
    Assess extraction confidence using these thresholds as guidance:
    - Financial data (amounts, taxes): 0.90+ confidence required
    - Personal information (names, addresses): 0.85+ confidence required  
    - Dates and standard fields: 0.75+ confidence acceptable
    
    Provide confidence scores between 0.0 and 1.0 with explanatory reasoning:
    {
      "attribute_name": {
        "confidence": 0.85,
        "confidence_threshold": 0.90,
        "confidence_reason": "Explanation of confidence assessment"
      }
    }
```

## UI Integration

Assessment results automatically appear in the web interface with enhanced visual indicators:

### Visual Feedback System

The UI provides immediate confidence feedback through color-coded displays:

#### Color Coding
- 🟢 **Green**: Confidence meets or exceeds threshold (high confidence)
- 🔴 **Red**: Confidence falls below threshold (requires review)
- ⚫ **Black**: Confidence available but no threshold for comparison

#### Display Modes

**1. With Threshold (Color-Coded)**
```
YTDNetPay: 75000
Confidence: 92.0% / Threshold: 95.0% [RED - Below Threshold]

PayPeriodStartDate: 2024-01-01  
Confidence: 85.0% / Threshold: 70.0% [GREEN - Above Threshold]
```

**2. Confidence Only (Black Text)**
```
EmployeeName: John Smith
Confidence: 88.5% [BLACK - No Threshold Set]
```

**3. No Display**
When neither confidence nor threshold data is available, no confidence indicator is shown.

### Interface Coverage

**1. Form View (JSONViewer)**
- Color-coded confidence display in the editable form interface
- Supports nested data structures (arrays, objects)
- Real-time visual feedback during data editing

**2. Visual Editor Modal**
- Same confidence indicators in the document image overlay editor
- Visual connection between form fields and document bounding boxes
- Confidence display for deeply nested extraction results

**3. Nested Data Support**
Confidence indicators work with complex document structures:
```
FederalTaxes[0]:
  ├── YTD: 2111.2 [Confidence: 67.6% / Threshold: 85.0% - RED]
  └── Period: 40.6 [Confidence: 75.8% - BLACK]

StateTaxes[0]:
  ├── YTD: 438.36 [Confidence: 84.4% / Threshold: 80.0% - GREEN]
  └── Period: 8.43 [Confidence: 83.2% / Threshold: 80.0% - GREEN]
```

## Cost Optimization

### Token Reduction Strategy

The assessment feature implements several cost optimization techniques:

1. **Text Confidence Data**: Uses condensed OCR confidence information instead of full raw OCR results (80-90% token reduction)
2. **Conditional Image Processing**: Images only processed when `{DOCUMENT_IMAGE}` placeholder is present
3. **Optional Deployment**: Assessment infrastructure only deployed when `IsAssessmentEnabled=true`
4. **Efficient Prompting**: Optimized prompt templates minimize token usage while maintaining accuracy


## Testing and Validation

### End-to-End Testing

Use the provided notebook for comprehensive testing:

```bash
# Open the assessment testing notebook
jupyter notebook notebooks/e2e-example-with-assessment.ipynb
```

The notebook demonstrates:
- Document processing with assessment enabled
- Confidence score interpretation
- Integration with existing extraction workflows
- Performance and cost analysis

### Configuration Validation

Assessment enforces strict configuration requirements:

```python
# Missing prompt template
ValueError: "Assessment task_prompt is required in configuration but not found"

# Invalid DOCUMENT_IMAGE usage
ValueError: "Invalid DOCUMENT_IMAGE placeholder usage: found 2 occurrences, but exactly 1 is required"

# Template formatting error
ValueError: "Assessment prompt template formatting failed: missing required placeholder"
```

## Best Practices

### 1. Prompt Design

- **Be Specific**: Clearly define what constitutes high vs. low confidence
- **Include Examples**: Provide examples of confidence reasoning in system prompts
- **Use Structured Output**: Request consistent JSON format for programmatic processing

### 2. Cost Management

- **Enable Selectively**: Only enable assessment for critical document types
- **Text-First**: Start with text-only assessment before adding images
- **Monitor Usage**: Track token consumption and adjust prompts accordingly

### 3. Model Selection

- **Claude 3.5 Sonnet**: Recommended for balanced performance and cost
- **Claude 3 Haiku**: Consider for high-volume, cost-sensitive scenarios
- **Temperature 0**: Use deterministic output for consistent confidence scoring

### 4. Confidence Threshold Configuration

- **Risk-Based Thresholds**: Set higher thresholds (0.90+) for critical financial or personal data
- **Field-Specific Requirements**: Use per-attribute thresholds for different data types
- **Global Defaults**: Establish reasonable global thresholds (0.75-0.85) as baselines
- **Incremental Tuning**: Start with conservative thresholds and adjust based on accuracy analysis

### 5. Integration Patterns

- **Conditional Logic**: Implement business rules based on confidence scores and thresholds
- **Human Review**: Route low-confidence extractions (below threshold) for manual review
- **Quality Metrics**: Track confidence distributions to identify improvement opportunities
- **Visual Feedback**: Leverage color-coded UI indicators for immediate quality assessment

## Troubleshooting

### Common Issues

1. **Assessment Not Running**
   - Verify `IsAssessmentEnabled=true` in deployment
   - Check state machine definition includes assessment step
   - Confirm assessment Lambda function deployed successfully

2. **Template Errors**
   - Ensure `task_prompt` is defined in assessment configuration
   - Validate placeholder syntax and formatting
   - Check for exactly one `{DOCUMENT_IMAGE}` placeholder if using images

3. **Poor Confidence Scores**
   - Review prompt templates for clarity and specificity
   - Consider adding domain-specific guidance in system prompts
   - Validate OCR quality and text confidence data

4. **High Costs**
   - Monitor token usage in CloudWatch logs
   - Consider text-only assessment without images
   - Optimize prompt templates to reduce unnecessary context

5. **Confidence Threshold Issues**
   - Verify `confidence_threshold` values are between 0.0 and 1.0
   - Check explainability_info structure includes threshold data
   - Ensure UI displays match expected color coding (green/red/black)
   - Validate nested data confidence display for complex structures

### Monitoring

Key metrics to monitor:

- `InputDocumentsForAssessment`: Number of documents assessed
- `assessment_time_seconds`: Processing time per assessment
- `assessment_parsing_succeeded`: Success rate of JSON parsing
- Token consumption logs in CloudWatch

## Related Documentation

- [Pattern 2 Documentation](./pattern-2.md) - Assessment integration details
- [Configuration Guide](./configuration.md) - Configuration schema details
- [Extraction Documentation](./extraction.md) - Base extraction functionality
- [Web UI Documentation](./web-ui.md) - UI integration and display
