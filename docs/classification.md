# Customizing Classification

Document classification is a key component of the GenAIIDP solution that categorizes each document or page into predefined classes. This guide explains how to customize classification to best suit your document processing needs.

## Classification Methods

The solution supports multiple classification approaches:

### 1. Page-Level Classification

- Classifies each page independently
- Works well for single-page documents or clearly distinct multi-page documents
- Faster processing time compared to holistic classification
- Available in Pattern 2 and Pattern 3

### 2. Holistic Packet Classification

- Analyzes entire document packets to identify logical boundaries
- Better suited for multi-document packets where context spans multiple pages
- Can identify document boundaries within large PDFs
- Available in Pattern 2

### 3. Few Shot Classification

- Uses example documents to improve classification accuracy
- Particularly useful for specialized document types
- Requires sample documents and expected classifications
- Available in Pattern 2 and Pattern 3

## Classification Prompts

You can customize classification behavior through various prompt components:

### System Prompts

Define overall model behavior and constraints:

```yaml
system_prompt: |
  You are an expert document classifier specializing in financial and business documents.
  Your task is to analyze document images and classify them into predefined categories.
  Focus on visual layout, textual content, and common patterns found in each document type.
  When in doubt, analyze the most prominent features like headers, logos, and form fields.
```

### Task Prompts

Specify classification instructions and formatting:

```yaml
task_prompt: |
  Analyze the following document page and classify it into one of these categories: 
  {{document_classes}}
  
  Return ONLY the document class name without additional explanations.
  If the document doesn't fit any of the provided classes, classify it as "other".
```

### Class Descriptions

Provide detailed descriptions for each document category:

```yaml
document_classes:
  invoice:
    description: "A commercial document issued by a seller to a buyer, related to a sale transaction and indicating the products, quantities, and agreed prices for products or services."
  receipt:
    description: "A document acknowledging that something of value has been received, often as proof of payment."
  bank_statement:
    description: "A document issued by a bank showing transactions and balances for a specific account over a defined period."
```

## Using CachePoint for Classification

The solution integrates with Amazon Bedrock CachePoint for improved performance:

- Caches frequently used prompts and responses
- Reduces latency for similar classification requests
- Optimizes costs through response reuse
- Automatic cache management and expiration

To enable CachePoint for classification:

```yaml
classification_settings:
  use_cache_point: true
  cache_ttl_seconds: 86400  # 24 hours
```

## Document Classes

### Standard Document Classes

The solution includes standard document classes based on the RVL-CDIP dataset:

- `letter`: Formal written correspondence
- `form`: Structured documents with fields
- `email`: Digital messages with headers
- `handwritten`: Documents with handwritten content
- `advertisement`: Marketing materials
- `scientific_report`: Research documents
- `scientific_publication`: Academic papers
- `specification`: Technical specifications
- `file_folder`: Organizational documents
- `news_article`: Journalistic content
- `budget`: Financial planning documents
- `invoice`: Commercial billing documents
- `presentation`: Slide-based documents
- `questionnaire`: Survey forms
- `resume`: Employment documents
- `memo`: Internal communications

### Custom Document Classes

You can define custom document classes through the Web UI configuration:

1. Navigate to the Configuration section
2. Select the Document Classes tab
3. Click "Add New Class"
4. Provide:
   - Class name (machine-readable identifier)
   - Display name (human-readable name)
   - Detailed description (to guide the classification model)
5. Save changes

## Setting Up Few Shot Examples

To improve classification using examples:

1. Prepare representative sample documents for each class
2. Process these documents through the system
3. Verify correct classification or manually update as needed
4. In the Web UI configuration:
   - Navigate to Few Shot Examples section
   - Upload or select example documents
   - Specify which classes these examples represent

### Few Shot Example Format

```yaml
few_shot_examples:
  - class: "invoice"
    examples:
      - "s3://example-bucket/samples/invoice1.pdf"
      - "s3://example-bucket/samples/invoice2.pdf"
  - class: "receipt"
    examples:
      - "s3://example-bucket/samples/receipt1.pdf"
```

## Best Practices for Classification

1. **Provide Clear Class Descriptions**: Include distinctive features and common elements
2. **Use Few Shot Examples**: Include 2-3 diverse examples per class
3. **Choose the Right Method**: Use page-level for simple documents, holistic for complex packets
4. **Balance Class Coverage**: Ensure all expected document types have classes
5. **Monitor and Refine**: Use the evaluation framework to track classification accuracy
6. **Consider Visual Elements**: Describe visual layout and design patterns in class descriptions
7. **Test with Real Documents**: Validate classification against actual document samples
