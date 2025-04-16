# Evaluation Service

The Evaluation Service component provides functionality to evaluate document extraction results by comparing extracted attributes against expected values.

## Features

- Compares document extraction results with expected results
- Supports multiple evaluation methods:
  - Exact match
  - Numeric exact match
  - Fuzzy string matching
  - Hungarian algorithm for lists
  - BERT semantic similarity (requires additional dependencies)
- Calculates metrics including precision, recall, F1 score, accuracy
- Generates comprehensive evaluation reports in both JSON and Markdown formats
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

# Evaluate documents
result_document = evaluation_service.evaluate_and_store(
    actual_document=processed_document,
    expected_document=expected_document
)

# Access evaluation report URI
evaluation_report_uri = result_document.evaluation_report_uri
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
- **False Alarm Rate**: Rate of false positives among negatives
- **False Discovery Rate**: Rate of false positives among positive predictions

These metrics are calculated at both the attribute level and document level.