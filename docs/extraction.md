# Customizing Extraction

Information extraction is a central capability of the GenAIIDP solution, transforming unstructured document content into structured data. This guide explains how to customize extraction for your specific use cases.

## Extraction Prompts

Configure extraction behavior through several components:

### Attribute Definitions

Specify fields to extract per document class:

```yaml
extraction_attributes:
  invoice:
    - name: "invoice_number"
      description: "The unique identifier for this invoice, typically labeled as 'Invoice #', 'Invoice Number', or similar"
    - name: "invoice_date"
      description: "The date when the invoice was issued, typically labeled as 'Date', 'Invoice Date', or similar"
    - name: "due_date"
      description: "The date by which payment is due, typically labeled as 'Due Date', 'Payment Due', or similar"
```

### Extraction Instructions

Provide detailed guidance for field identification:

```yaml
system_prompt: |
  You are an expert in extracting structured information from documents.
  Focus on accuracy in identifying key fields based on their descriptions.
  For each field, look for both the field label and the associated value.
  Pay attention to formatting patterns common in business documents.
  When a field is not present, indicate this explicitly rather than guessing.
```

### Output Formatting

Define structure and validation requirements:

```yaml
task_prompt: |
  Extract the following fields from this {{document_class}} document:
  {{attribute_list}}
  
  For each field, provide:
  1. The exact extracted value
  2. The confidence level (HIGH, MEDIUM, LOW)
  3. The location where the information was found
  
  Format your response as valid JSON:
  {
    "field_name": {
      "value": "extracted value",
      "confidence": "HIGH|MEDIUM|LOW",
      "location": "page 1, top section"
    },
    ...
  }
```

### Error Handling

Configure fallback behavior for missing or unclear data:

```yaml
extraction_settings:
  missing_field_behavior: "RETURN_EMPTY"  # Options: RETURN_EMPTY, RETURN_NOT_FOUND, ATTEMPT_INFERENCE
  low_confidence_threshold: 0.4
  require_validation_for_low_confidence: true
```

## Using CachePoint for Extraction

CachePoint integration for extraction provides:

- Cached extraction results for similar documents
- Improved consistency across similar document types
- Reduced processing costs and latency
- Automatic cache invalidation when prompts change

To enable CachePoint for extraction:

```yaml
extraction_settings:
  use_cache_point: true
  cache_ttl_seconds: 86400  # 24 hours
  similarity_threshold: 0.85  # Higher values require more document similarity for cache hits
```

## Extraction Attributes

The solution comes with predefined extraction attributes for common document types:

### Invoice Documents

- `invoice_number`: Unique invoice identifier
- `invoice_date`: Date of invoice issuance
- `vendor_name`: Name of the invoicing company
- `vendor_address`: Full address of vendor
- `customer_name`: Name of customer/account holder
- `customer_address`: Full address of customer
- `total_amount`: Final amount due
- `subtotal`: Amount before tax/shipping
- `tax_amount`: Tax or VAT amount
- `due_date`: Payment deadline
- `payment_terms`: Payment term details
- `line_items`: Individual items with quantity, description, and price

### Form Documents

- `form_type`: Type or title of the form
- `applicant_name`: Name of person filling the form
- `application_date`: Date form was completed
- `date_submitted`: Form submission date
- `reference_number`: Form tracking number
- `form_status`: Current status of the form
- `signature_present`: Whether form is signed

### Letter Documents

- `sender_name`: Name of letter writer
- `sender_address`: Address of sender
- `recipient_name`: Name of letter recipient
- `recipient_address`: Address of recipient
- `date`: Letter date
- `subject`: Letter subject or topic
- `greeting`: Opening greeting
- `closing`: Closing phrase
- `signature`: Signature information

### Bank Statements

- `account_number`: Bank account identifier
- `account_holder`: Name of account owner
- `statement_period`: Date range of statement
- `opening_balance`: Balance at start of period
- `closing_balance`: Balance at end of period
- `total_deposits`: Sum of all credits
- `total_withdrawals`: Sum of all debits
- `transactions`: List of individual transactions

## Adding Custom Attributes

You can define custom extraction attributes through the Web UI:

1. Navigate to the Configuration section
2. Select the Extraction Attributes tab
3. Choose the document class to modify
4. Click "Add New Attribute"
5. Provide:
   - Attribute name (machine-readable identifier)
   - Display name (human-readable name)
   - Detailed description (to guide extraction)
   - Optional formatting hints (e.g., date format)
6. Save changes

## Advanced Extraction Techniques

### Few-Shot Extraction

Improve extraction with examples:

```yaml
few_shot_examples:
  - document_class: "invoice"
    document_path: "s3://example-bucket/samples/invoice1.pdf"
    extracted_values:
      invoice_number: "INV-12345"
      invoice_date: "2023-04-15"
      total_amount: "$1,234.56"
```

### Hierarchical Extraction

Extract nested or hierarchical data:

```yaml
extraction_attributes:
  invoice:
    - name: "line_items"
      description: "The individual items listed on the invoice"
      type: "array"
      items:
        - name: "item_description"
          description: "Description of the item or service"
        - name: "quantity"
          description: "Number of items"
        - name: "unit_price"
          description: "Price per unit"
        - name: "total_price"
          description: "Total price for this line item"
```

### Conditional Extraction

Configure attributes that only apply in certain contexts:

```yaml
extraction_attributes:
  invoice:
    - name: "late_fee"
      description: "Fee applied for late payment"
      conditional:
        field: "payment_status"
        value: "OVERDUE"
    - name: "discount_amount"
      description: "Discount applied to the total"
      conditional:
        field: "has_discount"
        value: "true"
```

## Best Practices

1. **Clear Attribute Descriptions**: Include detail on where and how information appears
2. **Balance Precision and Recall**: Decide whether false positives or false negatives are more problematic
3. **Consider Data Validation**: Include format guidance (e.g., date format, currency)
4. **Test with Real Documents**: Validate extraction across representative samples
5. **Group Related Attributes**: Organize attributes logically for better model understanding
6. **Iterative Refinement**: Use the evaluation framework to identify and address extraction issues
7. **Document Variants**: Consider different layouts and formats for the same document types
