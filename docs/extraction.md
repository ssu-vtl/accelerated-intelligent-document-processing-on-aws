# Customizing Extraction

Information extraction is a central capability of the GenAIIDP solution, transforming unstructured document content into structured data. This guide explains how to customize extraction for your specific use cases, including few-shot prompting and CachePoint optimization.

## Extraction Configuration

Configure extraction behavior through several components:

### Document Classes and Attributes

Specify document classes and the fields to extract from each:

```yaml
classes:
  - name: "invoice"
    description: "A billing document listing items/services, quantities, prices, payment terms, and transaction totals"
    attributes:
      - name: "invoice_number"
        description: "The unique identifier for this invoice, typically labeled as 'Invoice #', 'Invoice Number', or similar"
      - name: "invoice_date"
        description: "The date when the invoice was issued, typically labeled as 'Date', 'Invoice Date', or similar"
      - name: "due_date"
        description: "The date by which payment is due, typically labeled as 'Due Date', 'Payment Due', or similar"
```

### Extraction Instructions

### Model and Prompt Configuration

Configure the extraction model and prompting strategy:

```yaml
extraction:
  # Model selection and parameters
  model: us.amazon.nova-pro-v1:0
  temperature: 0.0
  top_p: 0.1
  top_k: 5
  max_tokens: 4096
  
  # Prompts for extraction
  system_prompt: |
    You are an expert in extracting structured information from documents.
    Focus on accuracy in identifying key fields based on their descriptions.
    For each field, look for both the field label and the associated value.
    Pay attention to formatting patterns common in business documents.
    When a field is not present, indicate this explicitly rather than guessing.
    
  task_prompt: |
    Extract the following fields from this {DOCUMENT_CLASS} document:
    
    {ATTRIBUTE_NAMES_AND_DESCRIPTIONS}
    
    <few_shot_examples>
    {FEW_SHOT_EXAMPLES}
    </few_shot_examples>
    
    <<CACHEPOINT>>
    
    Here is the document to analyze:
    {DOCUMENT_TEXT}
    
    Format your response as valid JSON:
    {
      "field_name": "extracted value",
      ...
    }
```

The extraction service parses the JSON response and makes it available for downstream processing.

## Using CachePoint for Extraction

CachePoint is a feature of select Bedrock models that caches partial computations to improve performance and reduce costs. When used with extraction, it provides:

- Cached processing for portions of the prompt
- Improved consistency across similar document types
- Reduced processing costs and latency
- Faster inference times

### Enabling CachePoint

CachePoint is enabled by placing special `<<CACHEPOINT>>` tags in your prompt templates. These indicate where the model should cache preceding components of the prompt:

```yaml
extraction:
  model: us.amazon.nova-pro-v1:0  # Must be a CachePoint-compatible model
  task_prompt: |
    <background>
    You are an expert in business document analysis and information extraction.
    </background>
    
    <<CACHEPOINT>>  # Cache the instruction portion
    
    Here is the document to analyze:
    {DOCUMENT_TEXT}
```

### Supported Models

CachePoint is currently supported by the following models:

- `us.anthropic.claude-3-5-haiku-20241022-v1:0`
- `us.anthropic.claude-3-7-sonnet-20250219-v1:0`
- `us.amazon.nova-lite-v1:0`
- `us.amazon.nova-pro-v1:0`

### Cost Benefits

CachePoint significantly reduces token costs for cached portions:

```yaml
pricing:
  - name: bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0
    units:
      - name: inputTokens
        price: '8.0E-7'
      - name: outputTokens
        price: '4.0E-6'
      - name: cacheReadInputTokens  # Reduced rate for cached content
        price: '8.0E-8'             # 10x cheaper than standard input tokens
      - name: cacheWriteInputTokens
        price: '1.0E-6'
```

### Optimal CachePoint Placement

For extraction tasks, place CachePoint tags to separate:
1. **Static content** (system instructions, few-shot examples) - cacheable
2. **Dynamic content** (document text, specific attributes) - not cacheable

This ensures the expensive parts of your prompt that remain unchanged across documents are efficiently cached.

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

Improve extraction accuracy by providing examples within each document class configuration:

```yaml
classes:
  - name: "invoice"
    description: "A billing document for goods or services"
    attributes:
      - name: "invoice_number"
        description: "The unique identifier for this invoice"
      # Other attributes...
    examples:
      - name: "SampleInvoice1"
        attributesPrompt: |
          Expected attributes are:
            "invoice_number": "INV-12345"
            "invoice_date": "2023-04-15"
            "total_amount": "$1,234.56"
        imagePath: "config_library/pattern-2/examples/invoice-samples/invoice1.jpg"
      # Additional examples...
```

The extraction service will use these examples as context when processing similar documents. To use few-shot examples in your extraction prompts, include the `{FEW_SHOT_EXAMPLES}` placeholder:

```yaml
extraction:
  task_prompt: |
    Extract the following fields from this {DOCUMENT_CLASS} document:
    
    {ATTRIBUTE_NAMES_AND_DESCRIPTIONS}
    
    <few_shot_examples>
    {FEW_SHOT_EXAMPLES}
    </few_shot_examples>
    
    Now extract the attributes from this document:
    {DOCUMENT_TEXT}
```

Examples are class-specific - only examples from the same document class being processed will be included in the prompt.

## Best Practices

1. **Clear Attribute Descriptions**: Include detail on where and how information appears in the document. More specific descriptions lead to better extraction results.

2. **Balance Precision and Recall**: Decide whether false positives or false negatives are more problematic for your use case and adjust the prompt accordingly.

3. **Optimize Few-Shot Examples**: Select diverse, representative examples that cover common variations in your document formats and challenging edge cases.

4. **Use CachePoint Strategically**: Position CachePoint tags to maximize caching of static content while isolating dynamic content, placing them right before document text is introduced.

5. **Leverage Image Examples**: When providing few-shot examples with `imagePath`, ensure the images highlight the key fields to extract, especially for visually complex documents.

6. **Monitor Evaluation Results**: Use the evaluation framework to identify extraction issues and iteratively refine your prompts and examples.

7. **Choose Appropriate Models**: Select models based on your task requirements:
   - `us.amazon.nova-pro-v1:0` - Best for complex extraction with few-shot learning
   - `us.anthropic.claude-3-5-haiku-20241022-v1:0` - Good balance of performance vs. cost
   - `us.anthropic.claude-3-7-sonnet-20250219-v1:0` - Highest accuracy for specialized tasks

8. **Handle Document Variations**: Consider creating separate document classes for significantly different layouts of the same document type rather than trying to handle all variations with a single class.

9. **Test Extraction Pipeline End-to-End**: Validate your extraction configuration with the full pipeline including OCR, classification, and extraction to ensure components work together effectively.
