"""
Bedrock client module for interacting with Amazon Bedrock models.

This module provides a class-based interface for invoking Bedrock models
with built-in retry logic, metrics tracking, and configuration options.
"""

import boto3
import json
import os
import time
import logging
import copy
import random
from typing import Dict, Any, List, Optional, Union, Tuple
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Default retry settings
DEFAULT_MAX_RETRIES = 8
DEFAULT_INITIAL_BACKOFF = 2  # seconds
DEFAULT_MAX_BACKOFF = 300    # 5 minutes


class BedrockClient:
    """Client for interacting with Amazon Bedrock models."""
    
    def __init__(
        self, 
        region: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
        max_backoff: float = DEFAULT_MAX_BACKOFF,
        metrics_enabled: bool = True
    ):
        """
        Initialize a Bedrock client.
        
        Args:
            region: AWS region (defaults to AWS_REGION env var or us-west-2)
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
            metrics_enabled: Whether to publish metrics
        """
        self.region = region or os.environ.get('AWS_REGION', 'us-west-2')
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.metrics_enabled = metrics_enabled
        self._client = None
        
    @property
    def client(self):
        """Lazy-loaded Bedrock client."""
        if self._client is None:
            self._client = boto3.client('bedrock-runtime', region_name=self.region)
        return self._client
    
    def __call__(
        self,
        model_id: str,
        system_prompt: Union[str, List[Dict[str, str]]],
        content: List[Dict[str, Any]],
        temperature: Union[float, str] = 0.0,
        top_k: Optional[Union[float, str]] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Make the instance callable with the same signature as the original function.
        
        This allows instances to be used as drop-in replacements for the function.
        
        Args:
            model_id: The Bedrock model ID (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')
            system_prompt: The system prompt as string or list of content objects
            content: The content for the user message (can include text and images)
            temperature: The temperature parameter for model inference (float or string)
            top_k: Optional top_k parameter for Anthropic models (float or string)
            max_retries: Optional override for the instance's max_retries setting
            
        Returns:
            Bedrock response object with metering information
        """
        # Use instance max_retries if not overridden
        effective_max_retries = max_retries if max_retries is not None else self.max_retries
            
        return self.invoke_model(
            model_id=model_id,
            system_prompt=system_prompt,
            content=content,
            temperature=temperature,
            top_k=top_k,
            max_retries=effective_max_retries
        )
    
    def invoke_model(
        self,
        model_id: str,
        system_prompt: Union[str, List[Dict[str, str]]],
        content: List[Dict[str, Any]],
        temperature: Union[float, str] = 0.0,
        top_k: Optional[Union[float, str]] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model with retry logic.
        
        Args:
            model_id: The Bedrock model ID (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')
            system_prompt: The system prompt as string or list of content objects
            content: The content for the user message (can include text and images)
            temperature: The temperature parameter for model inference (float or string)
            top_k: Optional top_k parameter for Anthropic models (float or string)
            max_retries: Optional override for the instance's max_retries setting
            
        Returns:
            Bedrock response object with metering information
        """
        # Track total requests
        self._put_metric('BedrockRequestsTotal', 1)
        
        # Use instance max_retries if not overridden
        effective_max_retries = max_retries if max_retries is not None else self.max_retries
        
        # Format system prompt if needed
        if isinstance(system_prompt, str):
            formatted_system_prompt = [{"text": system_prompt}]
        else:
            formatted_system_prompt = system_prompt
        
        # Build message
        message = {
            "role": "user",
            "content": content
        }
        messages = [message]
        
        # Convert temperature to float if it's a string
        if isinstance(temperature, str):
            try:
                temperature = float(temperature)
            except ValueError:
                logger.warning(f"Failed to convert temperature value '{temperature}' to float. Using default 0.0")
                temperature = 0.0
        
        inference_config = {"temperature": temperature}
        
        # Add additional model fields if needed
        additional_model_fields = None
        if "anthropic" in model_id.lower() and top_k is not None:
            # Convert top_k to float if it's a string
            if isinstance(top_k, str):
                try:
                    top_k = float(top_k)
                except ValueError:
                    logger.warning(f"Failed to convert top_k value '{top_k}' to float. Not using top_k.")
                    # Skip adding top_k if conversion fails
                else:
                    additional_model_fields = {"top_k": top_k}
            else:
                additional_model_fields = {"top_k": top_k}
        
        # Get guardrail configuration if available
        guardrail_config = self.get_guardrail_config()
        
        # Build converse parameters
        converse_params = {
            "modelId": model_id,
            "messages": messages,
            "system": formatted_system_prompt,
            "inferenceConfig": inference_config,
            "additionalModelRequestFields": additional_model_fields
        }
        
        # Add guardrail config if available
        if guardrail_config:
            converse_params["guardrailConfig"] = guardrail_config
        
        # Start timing the entire request
        request_start_time = time.time()
        
        # Call the recursive retry function
        result = self._invoke_with_retry(
            converse_params=converse_params,
            retry_count=0,
            max_retries=effective_max_retries,
            request_start_time=request_start_time
        )
        
        return result
    
    def _invoke_with_retry(
        self,
        converse_params: Dict[str, Any],
        retry_count: int,
        max_retries: int,
        request_start_time: float,
        last_exception: Exception = None
    ) -> Dict[str, Any]:
        """
        Recursive helper method to handle retries for Bedrock invocation.
        
        Args:
            converse_params: Parameters for the Bedrock converse API call
            retry_count: Current retry attempt (0-based)
            max_retries: Maximum number of retry attempts
            request_start_time: Time when the original request started
            last_exception: The last exception encountered (for final error reporting)
            
        Returns:
            Bedrock response object with metering information
            
        Raises:
            Exception: The last exception encountered if max retries are exceeded
        """
        try:
            # Create a copy of the messages to sanitize for logging
            sanitized_params = copy.deepcopy(converse_params)
            if "messages" in sanitized_params:
                sanitized_params["messages"] = self._sanitize_messages_for_logging(sanitized_params["messages"])
            
            # Log detailed request parameters
            logger.info(f"Bedrock request attempt {retry_count + 1}/{max_retries}:")
            logger.debug(f"  - model: {converse_params['modelId']}")
            logger.debug(f"  - inferenceConfig: {converse_params['inferenceConfig']}")
            logger.debug(f"  - system: {converse_params['system']}")
            logger.debug(f"  - messages: {sanitized_params['messages']}")
            logger.debug(f"  - additionalModelRequestFields: {converse_params['additionalModelRequestFields']}")
            
            # Log guardrail usage if configured
            if "guardrailConfig" in converse_params:
                logger.debug(f"  - guardrailConfig: {converse_params['guardrailConfig']}")
            
            # Start timing this attempt
            attempt_start_time = time.time()
            
            # Make the API call
            response = self.client.converse(**converse_params)
            
            # Calculate duration
            duration = time.time() - attempt_start_time
            
            # Log response details, but sanitize large content
            sanitized_response = self._sanitize_response_for_logging(response)
            logger.debug(f"Bedrock request successful after {retry_count + 1} attempts. Duration: {duration:.2f}s")
            logger.info(f"Response: {sanitized_response}")
            
            # Track successful requests and latency
            self._put_metric('BedrockRequestsSucceeded', 1)
            self._put_metric('BedrockRequestLatency', duration * 1000, 'Milliseconds')
            if retry_count > 0:
                self._put_metric('BedrockRetrySuccess', 1)
            
            # Track token usage
            if 'usage' in response:
                input_tokens = response['usage'].get('inputTokens', 0)
                output_tokens = response['usage'].get('outputTokens', 0)
                total_tokens = response['usage'].get('totalTokens', 0)
                self._put_metric('InputTokens', input_tokens)
                self._put_metric('OutputTokens', output_tokens)
                self._put_metric('TotalTokens', total_tokens)
            
            # Calculate total duration
            total_duration = time.time() - request_start_time
            self._put_metric('BedrockTotalLatency', total_duration * 1000, 'Milliseconds')
            
            # Create metering data
            usage = response.get('usage', {})
            response_with_metering = {
                "response": response,
                "metering": {
                    f"bedrock/{converse_params['modelId']}": {
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
                'ServiceUnavailableException',
                'ModelErrorException'
            ]
            
            if error_code in retryable_errors:
                self._put_metric('BedrockThrottles', 1)
                
                # Check if we've reached max retries
                if retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded. Last error: {error_message}")
                    self._put_metric('BedrockRequestsFailed', 1)
                    self._put_metric('BedrockMaxRetriesExceeded', 1)
                    raise
                
                # Calculate backoff time
                backoff = self._calculate_backoff(retry_count)
                logger.warning(f"Bedrock throttling occurred (attempt {retry_count + 1}/{max_retries}). "
                             f"Error: {error_message}. "
                             f"Backing off for {backoff:.2f}s")
                
                # Sleep for backoff period
                time.sleep(backoff)
                
                # Recursive call with incremented retry count
                return self._invoke_with_retry(
                    converse_params=converse_params,
                    retry_count=retry_count + 1,
                    max_retries=max_retries,
                    request_start_time=request_start_time,
                    last_exception=e
                )
            else:
                logger.error(f"Non-retryable Bedrock error: {error_code} - {error_message}")
                self._put_metric('BedrockRequestsFailed', 1)
                self._put_metric('BedrockNonRetryableErrors', 1)
                raise
        
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {str(e)}", exc_info=True)
            self._put_metric('BedrockRequestsFailed', 1)
            self._put_metric('BedrockUnexpectedErrors', 1)
            raise
    
    def get_guardrail_config(self) -> Optional[Dict[str, str]]:
        """
        Get guardrail configuration from environment if available.
        
        Returns:
            Optional guardrail configuration dict with id and version
        """
        guardrail_env = os.environ.get("GUARDRAIL_ID_AND_VERSION", "")
        if not guardrail_env:
            return None
            
        try:
            guardrail_id, guardrail_version = guardrail_env.split(":")
            if guardrail_id and guardrail_version:
                logger.debug(f"Using Bedrock Guardrail ID: {guardrail_id}, Version: {guardrail_version}")
                return {
                    "guardrailIdentifier": guardrail_id,
                    "guardrailVersion": guardrail_version,
                    "trace": "enabled"  # Enable tracing for guardrail violations
                }
        except ValueError:
            logger.warning(f"Invalid GUARDRAIL_ID_AND_VERSION format: {guardrail_env}. Expected format: 'id:version'")
            
        return None
    
    def generate_embedding(
        self, 
        text: str, 
        model_id: str = "amazon.titan-embed-text-v1",
        max_retries: Optional[int] = None
    ) -> List[float]:
        """
        Generate an embedding vector for the given text using Amazon Bedrock.
        
        Args:
            text: The text to generate embeddings for
            model_id: The embedding model ID to use (default: amazon.titan-embed-text-v1)
            max_retries: Optional override for the instance's max_retries setting
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not isinstance(text, str):
            # Return an empty vector for empty input
            return []
        
        # Use instance max_retries if not overridden
        effective_max_retries = max_retries if max_retries is not None else self.max_retries
            
        # Track total embedding requests
        self._put_metric('BedrockEmbeddingRequestsTotal', 1)
        
        # Normalize whitespace and prepare the input text
        normalized_text = " ".join(text.split())
        
        # Prepare the request body based on the model
        if "amazon.titan-embed" in model_id:
            request_body = json.dumps({
                "inputText": normalized_text
            })
        else:
            # Default format for other models
            request_body = json.dumps({
                "text": normalized_text
            })
        
        # Call the recursive embedding function
        return self._generate_embedding_with_retry(
            model_id=model_id,
            request_body=request_body,
            normalized_text=normalized_text,
            retry_count=0,
            max_retries=effective_max_retries
        )
    
    def _generate_embedding_with_retry(
        self,
        model_id: str,
        request_body: str,
        normalized_text: str,
        retry_count: int,
        max_retries: int,
        last_exception: Exception = None
    ) -> List[float]:
        """
        Recursive helper method to handle retries for embedding generation.
        
        Args:
            model_id: The embedding model ID
            request_body: JSON request body for the API call
            normalized_text: Normalized input text (for logging)
            retry_count: Current retry attempt (0-based)
            max_retries: Maximum number of retry attempts
            last_exception: The last exception encountered (for final error reporting)
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            Exception: The last exception encountered if max retries are exceeded
        """
        try:
            logger.info(f"Bedrock embedding request attempt {retry_count + 1}/{max_retries}:")
            logger.debug(f"  - model: {model_id}")
            logger.debug(f"  - input text length: {len(normalized_text)} characters")
            
            attempt_start_time = time.time()
            response = self.client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=request_body
            )
            duration = time.time() - attempt_start_time
            
            # Extract the embedding vector from response
            response_body = json.loads(response["body"].read())
            
            # Handle different response formats based on the model
            if "amazon.titan-embed" in model_id:
                embedding = response_body.get("embedding", [])
            else:
                # Default extraction format
                embedding = response_body.get("embedding", [])
            
            # Track successful requests and latency
            self._put_metric('BedrockEmbeddingRequestsSucceeded', 1)
            self._put_metric('BedrockEmbeddingRequestLatency', duration * 1000, 'Milliseconds')
            
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
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
                self._put_metric('BedrockEmbeddingThrottles', 1)
                
                # Check if we've reached max retries
                if retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for embedding. Last error: {error_message}")
                    self._put_metric('BedrockEmbeddingRequestsFailed', 1)
                    self._put_metric('BedrockEmbeddingMaxRetriesExceeded', 1)
                    raise
                
                # Calculate backoff time
                backoff = self._calculate_backoff(retry_count)
                logger.warning(f"Bedrock throttling occurred (attempt {retry_count + 1}/{max_retries}). "
                            f"Error: {error_message}. "
                            f"Backing off for {backoff:.2f}s")
                
                # Sleep for backoff period
                time.sleep(backoff)
                
                # Recursive call with incremented retry count
                return self._generate_embedding_with_retry(
                    model_id=model_id,
                    request_body=request_body,
                    normalized_text=normalized_text,
                    retry_count=retry_count + 1,
                    max_retries=max_retries,
                    last_exception=e
                )
            else:
                logger.error(f"Non-retryable Bedrock error for embedding: {error_code} - {error_message}")
                self._put_metric('BedrockEmbeddingRequestsFailed', 1)
                self._put_metric('BedrockEmbeddingNonRetryableErrors', 1)
                raise
        
        except Exception as e:
            logger.error(f"Unexpected error generating embedding: {str(e)}", exc_info=True)
            self._put_metric('BedrockEmbeddingRequestsFailed', 1)
            self._put_metric('BedrockEmbeddingUnexpectedErrors', 1)
            raise
    
    def extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        Extract text from a Bedrock response.
        
        Args:
            response: Bedrock response object
            
        Returns:
            Extracted text content
        """
        response_obj = response.get("response", response)
        return response_obj['output']['message']['content'][0].get("text", "")
    
    def format_prompt(
        self, 
        prompt_template: str, 
        substitutions: Dict[str, str], 
        required_placeholders: List[str] = None
    ) -> str:
        """
        Prepare prompt from template by replacing placeholders with values.
        
        Args:
            prompt_template: The prompt template with placeholders in {PLACEHOLDER} format
            substitutions: Dictionary of placeholder values
            required_placeholders: List of placeholder names that must be present in the template
            
        Returns:
            String with placeholders replaced by values
            
        Raises:
            ValueError: If a required placeholder is missing from the template
        """
        # Validate required placeholders if specified
        if required_placeholders:
            missing_placeholders = [p for p in required_placeholders if f"{{{p}}}" not in prompt_template]
            if missing_placeholders:
                raise ValueError(f"Prompt template must contain the following placeholders: {', '.join([f'{{{p}}}' for p in missing_placeholders])}")
        
        # Check if template uses {PLACEHOLDER} format and convert to %(PLACEHOLDER)s for secure replacement
        if any(f"{{{key}}}" in prompt_template for key in substitutions):
            for key in substitutions:
                placeholder = f"{{{key}}}"
                if placeholder in prompt_template:
                    prompt_template = prompt_template.replace(placeholder, f"%({key})s")
                    
        # Apply substitutions using % operator which is safer than .format()
        return prompt_template % substitutions
    
    def _calculate_backoff(self, retry_count: int) -> float:
        """
        Calculate exponential backoff time with jitter.
        
        Args:
            retry_count: Current retry attempt (0-based)
            
        Returns:
            Backoff time in seconds
        """
        # Exponential backoff with base of 2
        backoff_seconds = min(
            self.max_backoff,
            self.initial_backoff * (2 ** retry_count)
        )
        
        # Add jitter (random value between 0 and 1 second)
        jitter = random.random()
        
        return backoff_seconds + jitter
    
    def _put_metric(self, metric_name: str, value: Union[int, float], unit: str = 'Count'):
        """
        Publish a metric if metrics are enabled.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (default: Count)
        """
        if self.metrics_enabled:
            try:
                from ..metrics import put_metric
                put_metric(metric_name, value, unit)
            except Exception as e:
                logger.warning(f"Failed to publish metric {metric_name}: {str(e)}")
    
    def _sanitize_messages_for_logging(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create a copy of messages with image content replaced for logging.
        
        Args:
            messages: List of message objects for Bedrock API
            
        Returns:
            Sanitized message objects suitable for logging
        """
        sanitized = copy.deepcopy(messages)
        
        for message in sanitized:
            if 'content' in message and isinstance(message['content'], list):
                for content_item in message['content']:
                    # Check for image type content
                    if isinstance(content_item, dict) and content_item.get('type') == 'image':
                        # Replace actual image data with placeholder
                        if 'source' in content_item:
                            content_item['source'] = {'data': '[image_data]'}
                    elif isinstance(content_item, dict) and 'image' in content_item:
                        # Handle different image format used by some models
                        content_item['image'] = '[image_data]'
                    elif isinstance(content_item, dict) and 'bytes' in content_item:
                        # Handle raw binary format
                        content_item['bytes'] = '[binary_data]'
        
        return sanitized
    
    def _sanitize_response_for_logging(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a sanitized copy of the response suitable for logging.
        
        Args:
            response: Response from Bedrock API
            
        Returns:
            Sanitized response suitable for logging
        """
        # Create a deep copy to avoid modifying the original
        sanitized = copy.deepcopy(response)
        
        # For very large responses, limit the content for logging
        if 'output' in sanitized and 'message' in sanitized['output']:
            message = sanitized['output']['message']
            if 'content' in message:
                content = message['content']
                
                # Handle list of content items (multimodal responses)
                if isinstance(content, list):
                    for i, item in enumerate(content):
                        if isinstance(item, dict):
                            # Truncate text content if too long
                            if 'text' in item and isinstance(item['text'], str) and len(item['text']) > 500:
                                item['text'] = item['text'][:500] + '... [truncated]'
                            # Replace image data with placeholder
                            if 'image' in item:
                                item['image'] = '[image_data]'
                # Handle string content
                elif isinstance(content, str) and len(content) > 500:
                    message['content'] = content[:500] + '... [truncated]'
        
        return sanitized


# Create a default client instance
default_client = BedrockClient()

# Export the default client as invoke_model for backward compatibility
invoke_model = default_client