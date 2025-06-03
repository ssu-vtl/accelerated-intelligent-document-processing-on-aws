Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

# Few-Shot Examples in Pattern-2: Classification and Extraction

## Overview

Pattern-2 supports few-shot example prompting, a powerful feature that allows you to provide concrete document examples with expected outputs to significantly improve model accuracy, consistency, and reduce hallucination for both document classification and attribute extraction tasks.

## What is Few-Shot Learning?

Few-shot learning enhances AI model performance by providing concrete examples alongside prompts. Instead of relying solely on text descriptions, the model can see actual document images paired with expected outputs, leading to better understanding of document patterns and more accurate results.

## Key Benefits

- **🎯 Improved Accuracy**: Models understand document patterns and expected formats better through concrete examples
- **📏 Consistent Output**: Examples establish exact JSON structure and formatting standards
- **🚫 Reduced Hallucination**: Examples reduce likelihood of made-up classification or attribute values
- **🔧 Domain Adaptation**: Examples help models understand domain-specific terminology and conventions
- **💡 Better Edge Case Handling**: Visual examples clarify ambiguous cases that text descriptions might miss
- **💰 Cost Effectiveness with Caching**: Using prompt caching with few-shot examples can significantly reduce costs for repeated processing

## When to Use Few-Shot Examples

Consider using few-shot examples when:
- Your document types have subtle visual differences that are hard to describe in text
- You need consistent attribute extraction formats across documents
- You're working with domain-specific documents with specialized terminology
- Standard prompting doesn't achieve the accuracy you need
- You want to reduce the amount of prompt engineering required
- You process similar documents repeatedly and can benefit from prompt caching

## Configuration Structure

Few-shot examples are configured within document class definitions in your Pattern-2 configuration:

```yaml
classes:
  - name: letter
    description: "A formal written correspondence..."
    attributes:
      - name: sender_name
        description: "The name of the person who wrote the letter..."
      - name: sender_address
        description: "The physical address of the sender..."
    examples:
      - classPrompt: "This is an example of the class 'letter'"
        name: "Letter1"
        attributesPrompt: |
          expected attributes are:
              "sender_name": "Will E. Clark",
              "sender_address": "206 Maple Street P.O. Box 1056 Murray Kentucky 42071-1056",
              "recipient_name": "The Honorable Wendell H. Ford",
              "date": "10/31/1995",
              "subject": null
        imagePath: "config_library/pattern-2/few_shot_example/example-images/letter1.jpg"
      - classPrompt: "This is an example of the class 'letter'"
        name: "Letter2"
        attributesPrompt: |
          expected attributes are:
              "sender_name": "William H. W. Anderson",
              "sender_address": "P O. BOX 12046 CAMERON VILLAGE STATION RALEIGH N. c 27605",
              "recipient_name": "Mr. Addison Y. Yeaman",
              "date": "10/14/1970",
              "subject": "Invitation to the Twelfth Annual Meeting of the TGIC"
        imagePath: "config_library/pattern-2/few_shot_example/example-images/letter2.png"
```

### Example Fields Explained

Each example includes four key components:

- **`classPrompt`**: A brief description identifying this as an example of the document class (used for classification). Can include sample OCR text output to show the model what text content looks like for this class.
- **`name`**: A unique identifier for the example (for reference and debugging)
- **`attributesPrompt`**: The expected attribute extraction results in exact JSON format (used for extraction). Can include sample OCR text output to demonstrate the text from which attributes should be extracted.
- **`imagePath`**: Path to example document image(s) - supports single files, local directories, or S3 prefixes (optional but recommended for better visual understanding)

### Example Processing Rules

**Important**: Examples are only processed if they contain the required prompt field for the specific task:

- **For Classification**: Examples are only included if they have a non-empty `classPrompt` field
  - Examples with only `attributesPrompt` or `imagePath` (but no `classPrompt`) are automatically skipped
  - Images from `imagePath` are still included if the example has a valid `classPrompt`

- **For Extraction**: Examples are only included if they have a non-empty `attributesPrompt` field
  - Examples with only `classPrompt` or `imagePath` (but no `attributesPrompt`) are automatically skipped
  - Images from `imagePath` are still included if the example has a valid `attributesPrompt`

This ensures that examples are only used when they have the appropriate content for their respective tasks, maintaining consistency and preventing irrelevant examples from being included in the prompts.

**Example Configurations**:

```yaml
# Valid for both classification and extraction
- classPrompt: "This is an example of the class 'invoice'"
  attributesPrompt: |
    expected attributes are:
        "invoice_number": "INV-001"
  imagePath: "invoice1.jpg"

# Valid only for classification (skipped during extraction)
- classPrompt: "This is an example of the class 'invoice'"
  # No attributesPrompt - will be skipped during extraction
  imagePath: "invoice2.jpg"

# Valid only for extraction (skipped during classification)
- attributesPrompt: |
    expected attributes are:
        "invoice_number": "INV-002"
  # No classPrompt - will be skipped during classification
  imagePath: "invoice3.jpg"

# Invalid for both (will be skipped entirely)
- name: "InvalidExample"
  # No classPrompt or attributesPrompt - will be skipped for both tasks
  imagePath: "invoice4.jpg"
```

#### Enhanced Image Path Support

The `imagePath` field now supports multiple formats for maximum flexibility:

**Single Image File (Original functionality)**:
```yaml
imagePath: "config_library/pattern-2/few_shot_example/example-images/letter1.jpg"
```

**Local Directory with Multiple Images (New)**:
```yaml
imagePath: "config_library/pattern-2/few_shot_example/example-images/"
```

**S3 Prefix with Multiple Images (New)**:
```yaml
imagePath: "s3://my-config-bucket/few-shot-examples/letter/"
```

**Direct S3 Image URI**:
```yaml
imagePath: "s3://my-config-bucket/few-shot-examples/letter/example1.jpg"
```

When pointing to a directory or S3 prefix, the system automatically:
- Discovers all image files with supported extensions (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`)
- Sorts them alphabetically by filename for consistent ordering
- Includes each image as a separate content item in the few-shot examples
- Gracefully handles individual image loading failures without breaking the entire process

#### Environment Variables for Path Resolution

The system uses these environment variables for resolving relative paths:

- **`CONFIGURATION_BUCKET`**: S3 bucket name for configuration files
  - Used when `imagePath` doesn't start with `s3://`
  - The path is treated as a key within this bucket

- **`ROOT_DIR`**: Root directory for local file resolution
  - Used when `CONFIGURATION_BUCKET` is not set
  - The path is treated as relative to this directory

### Multimodal vs Text-Only Examples

Few-shot examples in Pattern-2 support both multimodal and text-only approaches:

**Multimodal Examples (Recommended)**:
- Include both `imagePath` and text descriptions in prompts
- Provide visual context alongside text explanations
- Help models understand document layout and formatting
- Most effective for complex document types

**Text-Only Examples**:
- Include sample document text (OCR output) within `classPrompt` or `attributesPrompt`
- Useful when images are not available or for privacy-sensitive scenarios
- Can demonstrate text patterns and content structure
- Still provide significant accuracy improvements over no examples

**Example with OCR Text Content**:
```yaml
examples:
  - classPrompt: |
      This is an example of the class 'invoice'. 
      
      Example document text:
      INVOICE
      Invoice #: INV-2024-001
      Date: January 15, 2024
      Bill To: ACME Corp
      Total Amount: $1,250.00
      Due Date: February 15, 2024
    name: "Invoice1"
    attributesPrompt: |
      For the above invoice text, expected attributes are:
          "invoice_number": "INV-2024-001",
          "invoice_date": "January 15, 2024",
          "vendor_name": "Your Company Name",
          "customer_name": "ACME Corp", 
          "total_amount": "$1,250.00",
          "due_date": "February 15, 2024"
    # imagePath is optional - can be omitted for text-only examples
    imagePath: "config_library/pattern-2/your_config/example-images/invoice1.pdf"
```

## How Few-Shot Examples Work in Pattern-2

Pattern-2 uses few-shot examples differently for classification and extraction tasks:

### Classification Process

When classifying documents:
- **Example Scope**: Uses examples from ALL document classes
- **Purpose**: Help the model distinguish between different document types
- **Content**: Uses `classPrompt` field from examples (with optional images)
- **Benefit**: Model sees visual and/or textual examples of each class to make better classification decisions
- **Filtering**: Only examples with non-empty `classPrompt` fields are included

### Extraction Process

When extracting attributes from documents:
- **Example Scope**: Uses examples ONLY from the specific document class being processed
- **Purpose**: Show the expected attribute extraction format and values
- **Content**: Uses `attributesPrompt` field from examples (with optional images)
- **Benefit**: Model sees concrete examples of what the extraction output should look like
- **Filtering**: Only examples with non-empty `attributesPrompt` fields are included

| Aspect | Classification | Extraction |
|--------|---------------|------------|
| **Example Scope** | ALL classes | Specific class only |
| **Prompt Field** | `classPrompt` | `attributesPrompt` |
| **Purpose** | Distinguish document types | Show extraction format |
| **Content** | Document type descriptions + optional OCR text | Expected JSON attribute values + optional OCR text |
| **Images** | Optional but recommended | Optional but recommended |
| **Filtering** | Requires non-empty `classPrompt` | Requires non-empty `attributesPrompt` |

## Setting Up Few-Shot Examples

### Step 1: Prepare Example Documents

1. **Select Representative Documents**: Choose 1-3 clear, representative examples for each document class
2. **Gather Content**: Collect both document images and/or sample OCR text output
3. **Cover Variations**: Include examples that demonstrate different formats or edge cases within each class

### Step 2: Create Example Images (Optional)

If using images, store your example document images in an accessible location:

```
config_library/pattern-2/your_config/example-images/
├── letter1.jpg
├── letter2.png
├── email1.jpg
└── invoice1.pdf
```

For multiple images per example, you can organize them in directories:

```
config_library/pattern-2/your_config/example-images/
├── letters/
│   ├── 001_formal_letter.jpg
│   ├── 002_informal_letter.png
│   └── 003_business_letter.jpg
├── invoices/
│   ├── invoice_simple.jpg
│   ├── invoice_complex.png
│   └── invoice_international.jpg
└── emails/
    ├── email_formal.jpg
    └── email_casual.png
```

### Step 3: Define Examples in Configuration

Add examples to each document class in your configuration file. You can use images, text, or both:

```yaml
classes:
  - name: invoice
    description: "A commercial document requesting payment..."
    attributes:
      - name: invoice_number
        description: "The unique invoice identifier..."
      - name: total_amount
        description: "The total amount due..."
    examples:
      # Example with both image and OCR text content
      - classPrompt: |
          This is an example of the class 'invoice'. 
          
          Sample invoice text content:
          ACME CORPORATION
          INVOICE #INV-2024-001
          Date: 01/15/2024
          Bill To: Tech Solutions Inc
          Amount Due: $1,250.00
        name: "Invoice1"
        attributesPrompt: |
          For an invoice like the above, expected attributes are:
              "invoice_number": "INV-2024-001",
              "invoice_date": "01/15/2024",
              "vendor_name": "ACME Corporation",
              "total_amount": "$1,250.00",
              "due_date": "02/15/2024"
        imagePath: "config_library/pattern-2/your_config/example-images/invoice1.pdf"
      
      # Example with multiple images from directory
      - classPrompt: "These are examples of the class 'invoice' showing different formats"
        name: "InvoiceVariations"
        attributesPrompt: |
          For invoices like these examples, expected attributes format:
              "invoice_number": "string",
              "invoice_date": "MM/DD/YYYY",
              "vendor_name": "string",
              "total_amount": "$X.XX",
              "due_date": "MM/DD/YYYY or null"
        imagePath: "config_library/pattern-2/your_config/example-images/invoices/"
      
      # Example with text only (no image)
      - classPrompt: |
          This is another example of the class 'invoice'.
          
          Text from a different invoice format:
          Invoice Number: 2024-0234
          Billing Date: March 10, 2024
          Customer: Small Business LLC
          Total: $875.50
        name: "Invoice2"
        attributesPrompt: |
          For this invoice format, expected attributes are:
              "invoice_number": "2024-0234",
              "invoice_date": "March 10, 2024",
              "vendor_name": "Service Provider Inc",
              "total_amount": "$875.50",
              "due_date": null
        # No imagePath - text-only example
```

### Step 4: Update Task Prompts with Cache Points

Ensure your classification and extraction task prompts include the `{FEW_SHOT_EXAMPLES}` placeholder and use `<<CACHEPOINT>>` for optimal performance. You can also use the `{DOCUMENT_IMAGE}` placeholder for precise image positioning:

**Standard Few-Shot Configuration:**
```yaml
classification:
  task_prompt: |
    Classify this document into exactly one of these categories:
    
    {CLASS_NAMES_AND_DESCRIPTIONS}
    
    <few_shot_examples>
    {FEW_SHOT_EXAMPLES}
    </few_shot_examples>
    
    <<CACHEPOINT>>
    
    <document_content>
    {DOCUMENT_TEXT}
    </document_content>

extraction:
  task_prompt: |
    Extract the following attributes from this {DOCUMENT_CLASS} document:
    
    {ATTRIBUTE_NAMES_AND_DESCRIPTIONS}
    
    <few_shot_examples>
    {FEW_SHOT_EXAMPLES}
    </few_shot_examples>
    
    <<CACHEPOINT>>
    
    Document content:
    {DOCUMENT_TEXT}
```

**Enhanced Configuration with Image Placement:**
```yaml
classification:
  task_prompt: |
    Classify this document into exactly one of these categories:
    
    {CLASS_NAMES_AND_DESCRIPTIONS}
    
    <few_shot_examples>
    {FEW_SHOT_EXAMPLES}
    </few_shot_examples>
    
    <<CACHEPOINT>>
    
    Now examine this new document:
    {DOCUMENT_IMAGE}
    
    Document text:
    {DOCUMENT_TEXT}
    
    Classification:

extraction:
  task_prompt: |
    Extract the following attributes from this {DOCUMENT_CLASS} document:
    
    {ATTRIBUTE_NAMES_AND_DESCRIPTIONS}
    
    <few_shot_examples>
    {FEW_SHOT_EXAMPLES}
    </few_shot_examples>
    
    <<CACHEPOINT>>
    
    Analyze this document:
    {DOCUMENT_IMAGE}
    
    Text content:
    {DOCUMENT_TEXT}
    
    Extract as JSON:
```

**Important**: The `<<CACHEPOINT>>` delimiter separates the static portion of your prompt (classes, few-shot examples) from the dynamic portion (document content). This enables Bedrock prompt caching, significantly reducing costs when processing multiple documents with the same configuration.

### Step 5: Configure Path Resolution (If Using Images)

If using images, set up environment variables for image path resolution:

**For Local Development:**
```bash
export ROOT_DIR=/path/to/your/project/root
```

**For S3 Deployment:**
```bash
export CONFIGURATION_BUCKET=your-config-bucket-name
```

## Prompt Caching with Few-Shot Examples

Using prompt caching with few-shot examples provides significant cost and performance benefits:

### How Prompt Caching Works

The `<<CACHEPOINT>>` delimiter splits your prompt into two parts:
- **Static portion** (before CACHEPOINT): Class definitions, few-shot examples, instructions
- **Dynamic portion** (after CACHEPOINT): The specific document being processed

The static portion is cached by Bedrock and reused across multiple document processing requests, while only the dynamic portion varies per document.

### Cost Benefits

With few-shot examples adding significant token count to prompts, caching becomes essential:

```yaml
# Example prompt structure for cost optimization
task_prompt: |
  You are a document classification expert.
  
  Classes: {CLASS_NAMES_AND_DESCRIPTIONS}
  
  Few-shot examples: {FEW_SHOT_EXAMPLES}
  [This section can be 1000+ tokens with multiple examples]
  
  <<CACHEPOINT>>
  
  Document to classify: {DOCUMENT_TEXT}
  [Only this section varies per document]
```

**Without caching**: Pay full token cost (static + dynamic) for every document
**With caching**: Pay full cost once, then only dynamic portion for subsequent documents

### Performance Benefits

- **Faster Processing**: Cached static content doesn't need to be reprocessed
- **Reduced Latency**: Less time spent on prompt parsing and understanding
- **Better Consistency**: Same cached context ensures consistent interpretation

### Cache Optimization Tips

1. **Group similar documents**: Process documents of the same class together to maximize cache hits
2. **Stable configurations**: Avoid changing class definitions or examples frequently during processing batches
3. **Strategic placement**: Put all static content (examples, instructions) before the CACHEPOINT
4. **Monitor cache effectiveness**: Track cost reductions to verify caching is working

## Best Practices

### Creating Quality Examples

1. **Use Clear, Representative Documents**
   - Choose documents that clearly represent each class
   - Include realistic OCR text samples that show typical content
   - For images: Ensure text is legible and images are high quality
   - Include typical variations within each document type

2. **Include Required Prompt Fields**
   ```yaml
   # Good - includes both classPrompt and attributesPrompt for full functionality
   - classPrompt: "This is an example of the class 'invoice'"
     attributesPrompt: |
       expected attributes are:
           "invoice_number": "INV-001",
           "total_amount": "$1,250.00"
     imagePath: "invoice1.jpg"
   
   # Limited - only works for classification (extraction will skip this example)
   - classPrompt: "This is an example of the class 'invoice'"
     # Missing attributesPrompt - skipped during extraction
     imagePath: "invoice2.jpg"
   ```

3. **Provide Complete Attribute Sets**
   ```yaml
   # Good - shows all attributes with realistic values
   attributesPrompt: |
     For the sample invoice text above, expected attributes are:
         "sender_name": "John Smith",
         "sender_address": "123 Main St, City, State 12345",
         "recipient_name": "Jane Doe",
         "date": "03/15/2024",
         "subject": "Business Proposal",
         "cc": null,
         "attachments": null
   
   # Avoid - incomplete attribute sets
   attributesPrompt: |
     expected attributes are:
         "sender_name": "John Smith"
         # Missing other important attributes
   ```

4. **Handle Null Values Explicitly**
   ```yaml
   attributesPrompt: |
     expected attributes are:
         "invoice_number": "INV-2024-001",
         "po_number": null,  # Explicitly show when fields are not present
         "discount": null,
         "tax_amount": "$125.00"
   ```

5. **Maintain Consistent Formatting**
   - Use consistent JSON structure across all examples
   - Follow the same date formats, currency formats, etc.
   - Ensure field names match your attribute definitions exactly

6. **Organize Multiple Images Effectively**
   When using directories or S3 prefixes with multiple images:

   ```yaml
   # Good: Use descriptive, ordered filenames
   imagePath: "examples/letters/"
   # Contents: 001_formal_letter.jpg, 002_informal_letter.png, 003_business_letter.jpg

   # Good: Group related examples together
   imagePath: "s3://config-bucket/examples/invoices/"
   # Contents: invoice_simple.jpg, invoice_complex.png, invoice_international.jpg
   ```

### Optimal Example Quantities

- **1-3 examples per class**: More examples aren't always better; focus on quality
- **Diverse coverage**: Include examples that cover different variations within each class
- **Balanced representation**: Provide examples for your most important document classes
- **Multiple images per example**: When using directories, 3-5 images per example typically provides good coverage

### Image vs Text-Only Considerations

**When to Use Images**:
- Complex layouts where visual structure matters
- Documents with tables, forms, or specific formatting
- When you have high-quality, clear document images available
- Privacy and security allow image sharing

**When to Use Text-Only**:
- Privacy-sensitive environments where images cannot be shared
- When working primarily with text content
- Simple document layouts where visual structure is less important
- When image quality is poor or unavailable

### Image Management (If Using Images)

- **File formats**: JPG, PNG, and PDF are supported
- **Resolution**: Use high-resolution images (300 DPI or higher recommended)
- **File size**: Balance quality with reasonable file sizes for processing efficiency
- **Naming**: Use descriptive names that make examples easy to identify
- **Organization**: Use directories to group related images for multi-image examples

### Cache-Friendly Prompt Design

- **Static content first**: Place all class definitions, examples, and instructions before CACHEPOINT
- **Dynamic content last**: Only document-specific content should come after CACHEPOINT
- **Consistent structure**: Keep the same prompt structure across processing sessions
- **Avoid frequent changes**: Don't modify examples or instructions during active processing

## Testing Your Configuration

Use the provided test notebooks to validate your few-shot configuration:

### Classification Testing
```python
# Test classification few-shot examples
from idp_common.classification.service import ClassificationService
import yaml

# Load your configuration
with open('path/to/your/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize service
service = ClassificationService(config=config, backend="bedrock")

# Test building examples for all classes
examples = service._build_few_shot_examples_content()
print(f"Loaded {len(examples)} example items for classification")
```

### Extraction Testing
```python
# Test extraction few-shot examples for specific class
from idp_common.extraction.service import ExtractionService

service = ExtractionService(config=config)

# Test building examples for specific class (e.g., "letter")
examples = service._build_few_shot_examples_content('letter')
print(f"Loaded {len(examples)} example items for 'letter' class extraction")
```

## Performance Considerations

### Benefits
- **Higher Accuracy**: Well-crafted examples typically improve accuracy by 10-30%
- **Reduced Prompt Engineering**: Less time spent fine-tuning text descriptions
- **Consistent Outputs**: Examples establish clear formatting standards
- **Better Edge Case Handling**: Visual and textual examples help with ambiguous documents
- **Cost Efficiency with Caching**: Prompt caching can reduce costs by 50-90% for repeated processing

### Trade-offs
- **Increased Initial Token Usage**: Examples add to prompt length, increasing initial processing costs
- **Processing Time**: Loading and including example images takes additional time (text-only examples are faster)
- **Storage Requirements**: Example images need to be stored and accessible (not applicable for text-only)
- **Configuration Complexity**: More configuration setup required

### Cost Optimization Strategies

1. **Use prompt caching**: Always include `<<CACHEPOINT>>` in prompts when using few-shot examples
2. **Strategic example selection**: Focus on document classes where accuracy improvements justify the cost
3. **Consider text-only examples**: When images aren't essential, text-only examples reduce processing time
4. **Optimize image sizes**: If using images, use the smallest size that maintains clarity
5. **Batch processing**: Process similar documents together to maximize cache hits
6. **Monitor costs**: Track token usage and cache effectiveness to optimize ROI
7. **A/B test**: Compare accuracy and costs with and without examples

### Cache Performance Monitoring

Monitor these metrics to ensure optimal cache usage:
- **Cache hit rate**: Percentage of requests using cached content
- **Cost reduction**: Compare costs with and without caching
- **Processing latency**: Time savings from cached static content
- **Token usage patterns**: Distribution of static vs. dynamic tokens

## Troubleshooting

### Common Issues

**Examples Not Loading**
- Verify `{FEW_SHOT_EXAMPLES}` placeholder exists in task prompts
- Check that examples are defined for the document classes being processed
- Ensure examples have the required prompt fields (`classPrompt` for classification, `attributesPrompt` for extraction)
- For image examples: Ensure image paths are correct and files exist

**Examples Being Skipped**
- Verify that examples have non-empty `classPrompt` field for classification tasks
- Verify that examples have non-empty `attributesPrompt` field for extraction tasks
- Check that the prompt field contains actual content, not just whitespace
- Review the example processing rules described in this documentation

**Images Not Found (If Using Images)**
- Set `ROOT_DIR` environment variable for local development
- Set `CONFIGURATION_BUCKET` for S3 deployment scenarios
- Verify image file paths in configuration match actual file locations
- For directories: Ensure the directory contains image files with supported extensions
- For S3 prefixes: Verify S3 bucket and prefix paths are correct
- Consider using text-only examples if image access is problematic

**Caching Not Working**
- Ensure `<<CACHEPOINT>>` is properly placed in task prompts
- Verify static content is before CACHEPOINT and dynamic content is after
- Check that you're using supported Bedrock models with caching enabled

**High Costs Despite Caching**
- Verify cache hit rates are high (>80% for batch processing)
- Ensure you're not changing static content frequently
- Check that CACHEPOINT placement is optimal

**Inconsistent Results**
- Review example quality and ensure they're representative
- Check that `attributesPrompt` format matches expected output exactly
- Ensure examples cover the range of variations in your documents
- For text examples: Verify OCR text samples are realistic and accurate

**Poor Performance**
- Add more diverse examples for problematic document classes
- Improve example quality and accuracy
- Ensure examples demonstrate proper null value handling
- Consider mixing text and image examples for better coverage

## Example Configurations

### Complete Working Example with Caching

See `config_library/pattern-2/few_shot_example/` for a complete working configuration that demonstrates:
- Letter classification and extraction with 2 examples
- Email classification and extraction with 1 example
- Proper image path configuration
- Task prompts with few-shot placeholder integration and optimal CACHEPOINT placement

### Multi-Image Example Configuration

For using multiple images per example:

```yaml
classes:
  - name: letter
    description: "A formal written correspondence"
    attributes:
      - name: sender_name
        description: "The name of the person who wrote the letter"
      - name: recipient_name
        description: "The name of the person receiving the letter"
    examples:
      # Single image example
      - classPrompt: "This is an example of the class 'letter'"
        name: "Letter1"
        attributesPrompt: |
          expected attributes are:
              "sender_name": "John Smith",
              "recipient_name": "Jane Doe"
        imagePath: "config_library/pattern-2/your_config/example-images/letter1.jpg"
      
      # Multiple images from directory
      - classPrompt: "These are various examples of the class 'letter'"
        name: "LetterVariations"
        attributesPrompt: |
          For letters like these examples, the expected format is:
              "sender_name": "string",
              "recipient_name": "string"
        imagePath: "config_library/pattern-2/your_config/example-images/letters/"
      
      # Multiple images from S3 prefix
      - classPrompt: "Additional letter examples from S3"
        name: "LetterS3Examples"
        attributesPrompt: |
          For these letter types, extract:
              "sender_name": "actual sender name",
              "recipient_name": "actual recipient name"
        imagePath: "s3://my-config-bucket/examples/letters/"
```

### Text-Only Example Configuration

For environments where images cannot be used:

```yaml
classes:
  - name: invoice
    description: "A commercial document requesting payment"
    attributes:
      - name: invoice_number
        description: "The unique invoice identifier"
      - name: total_amount
        description: "The total amount due"
    examples:
      - classPrompt: |
          This is an example of the class 'invoice'.
          
          Example invoice text:
          INVOICE
          Invoice No: INV-2024-001
          Date: January 15, 2024
          Bill To: Customer Name
          Amount: $1,250.00
        name: "Invoice1"
        attributesPrompt: |
          For the above invoice text, expected attributes are:
              "invoice_number": "INV-2024-001",
              "invoice_date": "January 15, 2024",
              "vendor_name": "Your Company",
              "total_amount": "$1,250.00"
        # No imagePath - text-only example

classification:
  task_prompt: |
    Classify this document: {CLASS_NAMES_AND_DESCRIPTIONS}
    Examples: {FEW_SHOT_EXAMPLES}
    <<CACHEPOINT>>
    Document: {DOCUMENT_TEXT}

extraction:
  task_prompt: |
    Extract: {ATTRIBUTE_NAMES_AND_DESCRIPTIONS}
    Examples: {FEW_SHOT_EXAMPLES}
    <<CACHEPOINT>>
    Document: {DOCUMENT_TEXT}
```

### Production-Ready Configuration

For production use with optimal caching:

```yaml
classification:
  task_prompt: |
    You are a document classification expert. Classify the document into exactly one category.
    
    Available Categories:
    {CLASS_NAMES_AND_DESCRIPTIONS}
    
    Study these examples of each category:
    {FEW_SHOT_EXAMPLES}
    
    Instructions:
    - Analyze the document layout, content, and formatting
    - Return only the category name, no explanation
    - Consider both visual structure and text content shown in examples
    
    <<CACHEPOINT>>
    
    Document to classify:
    {DOCUMENT_TEXT}

extraction:
  task_prompt: |
    You are a document extraction expert. Extract specific attributes from this {DOCUMENT_CLASS} document.
    
    Required Attributes:
    {ATTRIBUTE_NAMES_AND_DESCRIPTIONS}
    
    Follow these examples for the expected format:
    {FEW_SHOT_EXAMPLES}
    
    Rules:
    - Return valid JSON only
    - Use null for missing values
    - Match the exact format shown in examples
    - Extract from the document text, don't invent values
    
    <<CACHEPOINT>>
    
    Document content:
    {DOCUMENT_TEXT}
```

## Future Capabilities

The few-shot examples feature continues to evolve with planned enhancements:

- **Dynamic Example Selection**: Automatically choose the most relevant examples based on document similarity
- **Quality Assessment**: Automated evaluation of example quality and recommendations for improvement
- **Confidence Integration**: Use few-shot examples to improve confidence scoring
- **Additional Formats**: Support for more example formats and metadata
- **Enhanced Caching**: More sophisticated caching strategies for different use cases
- **Hybrid Examples**: Better integration of text and image content within examples
- **Enhanced Multi-Image Support**: Advanced algorithms for optimal image selection from directories

Few-shot examples with prompt caching represent a significant step forward in making Pattern-2 more accurate, cost-effective, and easier to configure for diverse document processing scenarios. The flexibility to use images, text, or both, combined with support for multiple images per example, provides comprehensive options for different security, privacy, and performance requirements.
