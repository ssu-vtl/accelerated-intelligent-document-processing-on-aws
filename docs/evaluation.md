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

- **Exact Match (EXACT)**: Compares values character-by-character after normalizing whitespace and punctuation
- **Numeric Exact Match (NUMERIC_EXACT)**: Compares numeric values after normalizing formats (removing currency symbols, commas, etc.)
- **Fuzzy Match (FUZZY)**: Allows for minor variations in formatting and whitespace with configurable similarity thresholds
- **Semantic Match (SEMANTIC)**: Evaluates meaning equivalence using embedding-based similarity with Bedrock Titan embeddings
- **List Matching (HUNGARIAN)**: Uses the Hungarian algorithm for optimal bipartite matching of lists with multiple comparator types:
  - **EXACT**: Default comparator for exact string matching after normalization
  - **FUZZY**: Fuzzy string matching with configurable threshold
  - **NUMERIC**: Numeric comparison after normalizing currency symbols and formats
- **LLM-Powered Analysis (LLM)**: Uses AI to determine functional equivalence of extracted data with detailed explanations

## Configuration

Set the following parameters during stack deployment:

```yaml
EvaluationBaselineBucketName:
  Description: Existing bucket with baseline data, or leave empty to create new bucket
  
EvaluationAutoEnabled:
  Default: true
  Description: Automatically evaluate each document (if baseline exists)
  
EvaluationModelId:
  Default: "anthropic.claude-3-sonnet-20240229-v1:0"
  Description: Model to use for evaluation reports (e.g., "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
```

You can also configure evaluation methods for specific document classes and attributes through the solution's configuration. For example:

```yaml
classes:
  - name: invoice
    attributes:
      - name: invoice_number
        description: The unique identifier for the invoice
        evaluation_method: EXACT  # Use exact string matching
      - name: amount_due
        description: The total amount to be paid
        evaluation_method: NUMERIC_EXACT  # Use numeric comparison
      - name: vendor_name
        description: Name of the vendor
        evaluation_method: FUZZY  # Use fuzzy matching
        evaluation_threshold: 0.8  # Minimum similarity threshold
```

## Viewing Reports

1. In the web UI, select a document from the Documents list
2. Click "View Evaluation Report" button 
3. The report shows:
   - Section classification accuracy
   - Field-by-field comparison with visual indicators (✅/❌)
   - Analysis of differences with detailed reasons
   - Overall accuracy assessment with color-coded metrics (🟢 Excellent, 🟡 Good, 🟠 Fair, 🔴 Poor)
   - Progress bar visualizations for match rates
   - Comprehensive metrics and performance ratings

## Creating Baseline Data

There are two main approaches to creating baseline data:

### Method 1: Use Existing Processing Results (Using Copy to Baseline Feature)

1. Process documents through the GenAIIDP solution
2. Review the output in the web UI
3. Make any necessary corrections
4. For documents with satisfactory results, click "Copy to Baseline"
5. The system will asynchronously copy all processing results to the baseline bucket
6. The document status will update to indicate baseline availability:
   - BASELINE_COPYING: Copy operation in progress
   - BASELINE_AVAILABLE: Document successfully copied to baseline
   - BASELINE_ERROR: Error occurred during the copy operation

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

## Automatic Field Discovery

The evaluation framework automatically discovers and evaluates fields that exist in the data but are not defined in the configuration:

- Detects fields present in actual results, expected results, or both
- Uses LLM evaluation method by default for discovered fields
- Clearly marks discovered fields in the report
- Handles cases where fields are missing from either actual or expected results

This capability is valuable when:
- The complete schema is not yet fully defined
- You're handling variations in extraction outputs
- Identifying potential new fields to add to your configuration
- Ensuring comprehensive evaluation coverage

## Semantic vs LLM Evaluation

The framework offers two approaches for semantic evaluation:

- **SEMANTIC Method**: Uses embedding-based comparison with Bedrock Titan embeddings
  - Faster and more cost-effective than LLM-based evaluation
  - Provides similarity scores without explanations
  - Great for high-volume comparisons where speed is important
  - Configurable threshold for matching sensitivity
  
- **LLM Method**: Uses Bedrock Claude or other LLM models
  - Provides detailed reasoning for why values match or don't match
  - Better at handling implicit/explicit information differences
  - More nuanced understanding of semantic equivalence
  - Ideal for cases where understanding the rationale is important
  - Used as the default method for attributes discovered in the data but not in the configuration

## Metrics and Monitoring

The evaluation framework includes comprehensive monitoring through CloudWatch metrics:

- **Evaluation Success/Failure Rates**: Track evaluation completion and error rates
- **Baseline Data Availability**: Monitor percentage of documents with baseline data for comparison
- **Report Generation Performance**: Track time to generate evaluation reports
- **Model Usage Metrics**: Monitor token consumption and API calls for evaluation models
- **Accuracy Trends**: Historical tracking of processing accuracy over time

The framework calculates the following detailed metrics for each document and section:

- **Precision**: Accuracy of positive predictions (TP / (TP + FP))
- **Recall**: Coverage of actual positive cases (TP / (TP + FN))
- **F1 Score**: Harmonic mean of precision and recall
- **Accuracy**: Overall correctness (TP + TN) / (TP + TN + FP + FN)
- **False Alarm Rate**: Rate of false positives among negatives (FP / (FP + TN))
- **False Discovery Rate**: Rate of false positives among positive predictions (FP / (FP + TP))

The evaluation also tracks different evaluation statuses:
- **RUNNING**: Evaluation is in progress
- **COMPLETED**: Evaluation finished successfully
- **FAILED**: Evaluation encountered errors
- **NO_BASELINE**: No baseline data available for comparison
- **BASELINE_COPYING**: Process of copying document to baseline is in progress
- **BASELINE_AVAILABLE**: Document is available in the baseline
- **BASELINE_ERROR**: Error occurred during the baseline copy operation

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
