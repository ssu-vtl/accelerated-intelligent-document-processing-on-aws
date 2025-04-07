import boto3
import json
import os
import time
import logging
from typing import Dict, Any, List, Optional, Union
from botocore.exceptions import ClientError
from ..utils import calculate_backoff
from ..metrics import put_metric

logger = logging.getLogger(__name__)

# Default retry settings
MAX_RETRIES = 8
INITIAL_BACKOFF = 2  # seconds
MAX_BACKOFF = 300    # 5 minutes

# Add version info
__version__ = "0.1.0"

# Initialize clients
_bedrock_client = None

def get_bedrock_client():
    """
    Get or initialize the Bedrock client
    
    Returns:
        boto3 Bedrock client
    """
    global _bedrock_client
    if _bedrock_client is None:
        region = os.environ.get('AWS_REGION')
        _bedrock_client = boto3.client('bedrock-runtime', region_name=region)
    return _bedrock_client

def invoke_model(
    model_id: str,
    system_prompt: Union[str, List[Dict[str, str]]],
    content: List[Dict[str, Any]],
    temperature: float = 0.0,
    top_k: Optional[float] = None,
    max_retries: int = MAX_RETRIES
) -> Dict[str, Any]:
    """
    Invoke a Bedrock model with retry logic
    
    Args:
        model_id: The Bedrock model ID (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')
        system_prompt: The system prompt as string or list of content objects
        content: The content for the user message (can include text and images)
        temperature: The temperature parameter for model inference
        top_k: Optional top_k parameter for Anthropic models
        max_retries: Maximum number of retry attempts
        
    Returns:
        Bedrock response object
    """
    bedrock_client = get_bedrock_client()
    retry_count = 0
    last_exception = None
    request_start_time = time.time()
    
    # Track total requests
    put_metric('BedrockRequestsTotal', 1)
    
    # Format system prompt if needed
    if isinstance(system_prompt, str):
        formatted_system_prompt = [{"text": system_prompt}]
    else:
        formatted_system_prompt = system_prompt
    
    # Build message and inference config
    message = {
        "role": "user",
        "content": content
    }
    messages = [message]
    
    inference_config = {"temperature": temperature}
    
    # Add additional model fields if needed
    if "anthropic" in model_id.lower() and top_k is not None:
        additional_model_fields = {"top_k": top_k}
    else:
        additional_model_fields = None
    
    while retry_count < max_retries:
        try:
            logger.info(f"Bedrock request attempt {retry_count + 1}/{max_retries} - "
                      f"model: {model_id}, "
                      f"inferenceConfig: {inference_config}")
            
            attempt_start_time = time.time()
            response = bedrock_client.converse(
                modelId=model_id,
                messages=messages,
                system=formatted_system_prompt,
                inferenceConfig=inference_config,
                additionalModelRequestFields=additional_model_fields
            )
            duration = time.time() - attempt_start_time
            
            logger.info(f"Bedrock request successful after {retry_count + 1} attempts. "
                      f"Duration: {duration:.2f}s")
            
            # Track successful requests and latency
            put_metric('BedrockRequestsSucceeded', 1)
            put_metric('BedrockRequestLatency', duration * 1000, 'Milliseconds')
            if retry_count > 0:
                put_metric('BedrockRetrySuccess', 1)
            
            # Track token usage
            if 'usage' in response:
                input_tokens = response['usage'].get('inputTokens', 0)
                output_tokens = response['usage'].get('outputTokens', 0)
                total_tokens = response['usage'].get('totalTokens', 0)
                put_metric('InputTokens', input_tokens)
                put_metric('OutputTokens', output_tokens)
                put_metric('TotalTokens', total_tokens)
            
            total_duration = time.time() - request_start_time
            put_metric('BedrockTotalLatency', total_duration * 1000, 'Milliseconds')
            
            # Create metering data
            usage = response.get('usage', {})
            response_with_metering = {
                "response": response,
                "metering": {
                    f"bedrock/{model_id}": {
                        **usage
                    }
                }
            }
            
            return response_with_metering
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            retryable_errors = [
                'ThrottlingException', 
                'ServiceQuotaExceededException', 
                'RequestLimitExceeded', 
                'TooManyRequestsException', 
                'ServiceUnavailableException'
            ]
            
            if error_code in retryable_errors:
                retry_count += 1
                put_metric('BedrockThrottles', 1)
                
                if retry_count == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded. Last error: {error_message}")
                    put_metric('BedrockRequestsFailed', 1)
                    put_metric('BedrockMaxRetriesExceeded', 1)
                    raise
                
                backoff = calculate_backoff(retry_count)
                logger.warning(f"Bedrock throttling occurred (attempt {retry_count}/{max_retries}). "
                             f"Error: {error_message}. "
                             f"Backing off for {backoff:.2f}s")
                
                time.sleep(backoff)
                last_exception = e
            else:
                logger.error(f"Non-retryable Bedrock error: {error_code} - {error_message}")
                put_metric('BedrockRequestsFailed', 1)
                put_metric('BedrockNonRetryableErrors', 1)
                raise
        
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {str(e)}", exc_info=True)
            put_metric('BedrockRequestsFailed', 1)
            put_metric('BedrockUnexpectedErrors', 1)
            raise
    
    if last_exception:
        raise last_exception

def extract_text_from_response(response: Dict[str, Any]) -> str:
    """
    Extract text from a Bedrock response
    
    Args:
        response: Bedrock response object
        
    Returns:
        Extracted text content
    """
    response_obj = response.get("response", response)
    return response_obj['output']['message']['content'][0].get("text", "")