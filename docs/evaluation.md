# Evaluation Framework

The GenAIIDP solution includes a built-in evaluation framework to assess the accuracy of document processing outputs. This allows you to:

- Compare processing outputs against baseline (ground truth) data
- Generate detailed evaluation reports using configurable methods and thresholds
- Track and improve processing accuracy over time

## How It Works

1. **Baseline Data**
   - Store validated baseline data in a dedicated S3 bucket
   - Use an existing bucket or let the solution create one
   - Can use outputs from another GenAIIDP stack to compare different patterns/prompts

2. **Automatic Evaluation**
   - When enabled, automatically evaluates each processed document
   - Compares against baseline data if available
   - Generates detailed markdown reports using AI analysis

3. **Evaluation Reports**
   - Compare section classification accuracy
   - Analyze extracted field differences 
   - Identify patterns in discrepancies
   - Assess severity of differences (cosmetic vs. substantial)

## Evaluation Methods

The framework supports multiple comparison methods:

- **Exact Match**: Compares values character-by-character
- **Fuzzy Match**: Allows for minor variations in formatting and whitespace
- **Semantic Match**: Evaluates meaning equivalence regardless of phrasing
- **LLM-Powered Analysis**: Uses AI to determine functional equivalence of extracted data

## Configuration

Set the following parameters during stack deployment:

```yaml
EvaluationBaselineBucketName:
  Description: Existing bucket with baseline data, or leave empty to create new bucket
  
EvaluationAutoEnabled:
  Default: true
  Description: Automatically evaluate each document (if baseline exists)
  
EvaluationModelId:
  Default: "us.amazon.nova-pro-v1:0"
  Description: Model to use for evaluation reports (e.g., "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
```

## Viewing Reports

1. In the web UI, select a document from the Documents list
2. Click "View Evaluation Report" button 
3. The report shows:
   - Section classification accuracy
   - Field-by-field comparison 
   - Analysis of differences
   - Overall accuracy assessment

## Creating Baseline Data

There are two main approaches to creating baseline data:

### Method 1: Use Existing Processing Results

1. Process documents through the GenAIIDP solution
2. Review and manually verify the output JSON files
3. Make any necessary corrections
4. Upload the corrected files to the baseline bucket with the same object key as the original document

### Method 2: Create Baseline Data Manually

1. Create a JSON file following the GenAIIDP output schema
2. Include all required fields and values for each document
3. Upload to the baseline bucket with an object key matching the input document

## Baseline Bucket Structure

```
baseline-bucket/
├── document1.pdf.json    # Baseline for document1.pdf
├── document2.pdf.json    # Baseline for document2.pdf
└── subfolder/
    └── document3.pdf.json  # Baseline for subfolder/document3.pdf
```

Each baseline file should match the format of the GenAIIDP output, typically including:

```json
{
  "documentMetadata": { ... },
  "sections": [ ... ],
  "extractedData": { ... }
}
```

## Best Practices

- Enable auto-evaluation during testing/tuning phases
- Disable auto-evaluation in production for cost efficiency 
- Use evaluation reports to:
  - Compare different processing patterns
  - Test effects of prompt changes
  - Monitor accuracy over time
  - Identify areas for improvement

## Metrics and Monitoring

The evaluation framework includes comprehensive monitoring through CloudWatch metrics:

- **Evaluation Success/Failure Rates**: Track evaluation completion and error rates
- **Baseline Data Availability**: Monitor percentage of documents with baseline data for comparison
- **Report Generation Performance**: Track time to generate evaluation reports
- **Model Usage Metrics**: Monitor token consumption and API calls for evaluation models
- **Accuracy Trends**: Historical tracking of processing accuracy over time

## Troubleshooting Evaluation Issues

Common issues and resolutions:

1. **Missing Baseline Data**
   - Verify baseline files exist in the baseline bucket
   - Check that baseline filenames match the input document keys
   - Ensure baseline files are valid JSON

2. **Evaluation Failures**
   - Check Lambda function logs for error details
   - Verify that the evaluation model is available in your region
   - Increase Lambda timeout if needed for complex documents

3. **Low Accuracy Scores**
   - Review document quality and OCR results
   - Examine prompt configurations for classification and extraction
   - Check for processing errors in the workflow execution
