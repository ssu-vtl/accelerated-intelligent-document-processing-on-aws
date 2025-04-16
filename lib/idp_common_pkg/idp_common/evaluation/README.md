# Evaluation Service

The Evaluation Service component provides functionality to evaluate document extraction results by comparing extracted attributes against expected values.

## Features

- Compares document extraction results with expected (ground truth) results
- Supports multiple evaluation methods:
  - Exact match - Character-for-character comparison after normalizing whitespace and punctuation
  - Numeric exact match - Value-based comparison after normalizing numeric formats
  - Fuzzy string matching - Similarity-based matching with configurable thresholds
  - Hungarian algorithm - Optimal matching for lists of values
  - BERT semantic similarity - Meaning-based comparison (requires additional dependencies)
- Calculates key metrics including:
  - Precision, Recall, and F1 score
  - Accuracy and Error rates
  - False alarm rate and False discovery rate
- Generates rich, visual evaluation reports with:
  - Color-coded status indicators
  - Performance ratings
  - Progress bar visualizations
  - Detailed attribute comparisons
- Supports both JSON and Markdown report formats
- Fully integrated with the Document model architecture

## Usage

```python
from idp_common.models import Document, Status
from idp_common import ocr, classification, extraction, evaluation

# Get configuration (with evaluation methods specified)
config = {
    "classes": [
        {
            "name": "invoice",
            "attributes": [
                {
                    "name": "invoice_number",
                    "description": "The unique identifier for the invoice",
                    "evaluation_method": "EXACT"  # Use exact string matching
                },
                {
                    "name": "amount_due",
                    "description": "The total amount to be paid",
                    "evaluation_method": "NUMERIC_EXACT"  # Use numeric comparison
                },
                {
                    "name": "vendor_name",
                    "description": "Name of the vendor",
                    "evaluation_method": "FUZZY",  # Use fuzzy matching
                    "threshold": 0.8  # Minimum similarity threshold
                }
            ]
        }
    ]
}

# Create evaluation service
evaluation_service = evaluation.EvaluationService(config=config)

# Evaluate documents (stores results in S3 by default)
result_document = evaluation_service.evaluate_document(
    actual_document=processed_document,
    expected_document=expected_document
)

# Access evaluation report URI
evaluation_report_uri = result_document.evaluation_report_uri

# You can also access the evaluation result directly
evaluation_result = result_document.evaluation_result
overall_metrics = evaluation_result.overall_metrics
section_results = evaluation_result.section_results

# Or skip storage if needed (for quick memory-only evaluations)
memory_only_document = evaluation_service.evaluate_document(
    actual_document=processed_document,
    expected_document=expected_document,
    store_results=False
)
```

## Evaluation Methods

The service supports multiple evaluation methods that can be configured for each attribute:

- `EXACT`: Exact string match (after normalizing whitespace and punctuation)
- `NUMERIC_EXACT`: Exact match for numeric values (after normalizing currency symbols)
- `FUZZY`: Fuzzy string matching with configurable threshold
- `HUNGARIAN`: Optimal matching for lists of values using the Hungarian algorithm
- `BERT`: Semantic similarity comparison using BERT embeddings

## Output

The evaluation produces:

1. **JSON Results**: Detailed evaluation results with metrics
2. **Markdown Report**: Human-readable report with tables and summaries

## Metrics

The evaluation calculates the following metrics:

- **Precision**: Accuracy of positive predictions (TP / (TP + FP))
- **Recall**: Coverage of actual positive cases (TP / (TP + FN))
- **F1 Score**: Harmonic mean of precision and recall
- **Accuracy**: Overall correctness (TP + TN) / (TP + TN + FP + FN)
- **False Alarm Rate (FAR)**: Rate of false positives among negatives (FP / (FP + TN))
  - Measures how often the system extracts information that wasn't present in the document
- **False Discovery Rate (FDR)**: Rate of false positives among positive predictions (FP / (FP + TP))
  - Measures what proportion of the extracted information is incorrect

These metrics are calculated at both the attribute level (per field), section level (per document class), and document level (overall performance).

## Visual Reporting

The evaluation module produces richly formatted Markdown reports with:

1. **Summary Dashboard**:
   - Overall match rate with visual progress bar
   - Color-coded indicators for key metrics (🟢 Excellent, 🟡 Good, 🟠 Fair, 🔴 Poor)
   - Fraction of matched attributes (e.g., 8/10 attributes matched)

2. **Performance Tables**:
   - Metrics tables with value ratings
   - First-column status indicators (✅/❌) for immediate identification of matches
   - Detailed attribution of evaluation methods used for each field

3. **Method Explanations**:
   - Clear documentation of evaluation methods
   - Descriptions of scoring mechanisms
   - Guidance on interpreting results

The reports are designed to provide both at-a-glance performance assessment and detailed diagnostic information.