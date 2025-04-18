# Bedrock Utilities

This module provides utility functions for interacting with Amazon Bedrock's LLM services.

## Key Functions

### invoke_model

```python
def invoke_model(
    model_id: str, 
    system_prompt: Union[str, List[Dict[str, str]]], 
    content: List[Dict[str, Any]], 
    temperature: Union[float, str] = 0.0, 
    top_k: Optional[Union[float, str]] = None, 
    max_retries: int = MAX_RETRIES
) -> Dict[str, Any]
```

Invokes a Bedrock model with built-in retry logic for throttling and service exceptions.

**Parameters:**
- `model_id`: The Bedrock model ID (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')
- `system_prompt`: The system prompt as string or list of content objects
- `content`: The content for the user message (can include text and images)
- `temperature`: Model temperature parameter (float or string convertible to float)
- `top_k`: Optional top_k parameter for Anthropic models
- `max_retries`: Maximum number of retry attempts

**Returns:**
- Dictionary with the response and metering data

### extract_text_from_response

```python
def extract_text_from_response(response: Dict[str, Any]) -> str
```

Extracts the text content from a Bedrock response.

**Parameters:**
- `response`: Bedrock response object

**Returns:**
- Extracted text content as a string

### format_prompt

```python
def format_prompt(prompt_template: str, substitutions: Dict[str, str], required_placeholders: List[str] = None) -> str
```

Prepares a prompt from a template by safely replacing placeholders with values.

**Parameters:**
- `prompt_template`: The prompt template with placeholders in {PLACEHOLDER} format
- `substitutions`: Dictionary of placeholder values
- `required_placeholders`: Optional list of placeholder names that must be present in the template

**Returns:**
- String with placeholders replaced by values

**Raises:**
- ValueError: If a required placeholder is missing from the template

## Examples

### Invoking a Bedrock Model

```python
import bedrock

response = bedrock.invoke_model(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    system_prompt="You are a helpful assistant with expertise in document analysis.",
    content=[{"text": "Extract the key information from this invoice."}],
    temperature=0.0
)

# Extract the model's response text
result_text = bedrock.extract_text_from_response(response)
```

### Using the Prompt Template Formatter

```python
import bedrock

# Define a prompt template with placeholders
template = """
Extract the following information from this {DOCUMENT_TYPE} document:

Fields to extract:
{FIELDS_LIST}

Document content:
{DOCUMENT_TEXT}
"""

# Define substitution values
substitutions = {
    "DOCUMENT_TYPE": "invoice",
    "FIELDS_LIST": "- Invoice Number\n- Date\n- Total Amount",
    "DOCUMENT_TEXT": "INVOICE #1234\nDate: 2023-05-15\nTotal: $1,250.00"
}

# Define required placeholders
required = ["DOCUMENT_TYPE", "FIELDS_LIST", "DOCUMENT_TEXT"]

# Format the prompt
formatted_prompt = bedrock.format_prompt(template, substitutions, required)
```