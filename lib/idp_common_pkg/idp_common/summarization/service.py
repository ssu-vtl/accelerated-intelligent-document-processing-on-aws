"""
Summarization service for documents using LLMs.

This module provides a service for summarizing documents using various backends:
1. Bedrock LLMs with text support
"""

import json
import logging
import os
import time
import boto3
from typing import List, Dict, Any, Optional, Union, Tuple

from idp_common import bedrock, s3, utils
from idp_common.summarization.models import DocumentSummary, DocumentSummarizationResult
from idp_common.models import Document, Status

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for summarizing documents using various backends."""
    
    def __init__(
        self,
        region: str = None,
        config: Dict[str, Any] = None,
        backend: str = "bedrock"
    ):
        """
        Initialize the summarization service.
        
        Args:
            region: AWS region for backend services
            config: Configuration dictionary
            backend: Summarization backend to use ('bedrock')
        """
        self.config = config or {}
        self.region = region or self.config.get("region") or os.environ.get("AWS_REGION")
        self.backend = backend.lower()
        
        # Validate backend choice
        if self.backend != "bedrock":
            logger.warning(f"Invalid backend '{backend}', falling back to 'bedrock'")
            self.backend = "bedrock"
        
        # Initialize backend-specific clients
        if self.backend == "bedrock":
            # Get model_id from config for logging
            model_id = self.config.get("model_id") or self.config.get("summarization", {}).get("model")
            if not model_id:
                raise ValueError("No model ID specified in configuration for Bedrock")
            self.bedrock_model = model_id
            logger.info(f"Initialized summarization service with Bedrock backend using model {model_id}")
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def _get_summarization_config(self) -> Dict[str, Any]:
        """
        Get and validate the summarization configuration.
                    
        Returns:
            Dict with validated summarization configuration parameters
            
        Raises:
            ValueError: If required configuration values are missing
        """
        summarization_config = self.config.get("summarization", {})
        config = {
            "model_id": self.bedrock_model,
            "temperature": float(summarization_config.get("temperature", 0)),
            "top_k": float(summarization_config.get("top_k", 0.5)),
        }
        
        # Validate system prompt
        system_prompt = summarization_config.get("system_prompt")
        if not system_prompt:
            raise ValueError("No system_prompt found in summarization configuration")
        
        config["system_prompt"] = system_prompt
        
        # Validate task prompt
        task_prompt = summarization_config.get("task_prompt")
        if not task_prompt:
            raise ValueError("No task_prompt found in summarization configuration")
        
        config["task_prompt"] = task_prompt
        
        return config

    def _extract_json(self, text: str) -> str:
        """Extract JSON string from text."""
        # Check for code block format
        if "```json" in text:
            start_idx = text.find("```json") + len("```json")
            end_idx = text.find("```", start_idx)
            if end_idx > start_idx:
                return text[start_idx:end_idx].strip()
        
        # Check for simple JSON
        if "{" in text and "}" in text:
            start_idx = text.find("{")
            # Find matching closing brace
            open_braces = 0
            for i in range(start_idx, len(text)):
                if text[i] == "{":
                    open_braces += 1
                elif text[i] == "}":
                    open_braces -= 1
                    if open_braces == 0:
                        return text[start_idx:i+1].strip()
        
        # If we can't find JSON, return the text as-is
        return text

    def _invoke_bedrock_model(
        self,
        content: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model with standard parameters.
        
        Args:
            content: Content to send to the model
            config: Configuration with model parameters
            
        Returns:
            Dictionary with response and metering data
        """
        return bedrock.invoke_model(
            model_id=config["model_id"],
            system_prompt=config["system_prompt"],
            content=content,
            temperature=config["temperature"],
            top_k=config["top_k"]
        )

    def _create_error_summary(self, error_message: str) -> DocumentSummary:
        """
        Create a standard error summary with error information.
        
        Args:
            error_message: Error message to include in metadata
            
        Returns:
            DocumentSummary with error result
        """
        return DocumentSummary(
            content={"error": "Error generating summary"},
            metadata={"error": error_message}
        )

    def process_text(self, text: str) -> DocumentSummary:
        """
        Summarize text content using the configured backend.
        
        Args:
            text: Text content to summarize
            
        Returns:
            DocumentSummary: Summary of the text content with flexible structure
        """
        if not text:
            logger.warning("Empty text provided for summarization")
            return self._create_error_summary("Empty text provided")
        
        # Get summarization configuration
        config = self._get_summarization_config()
        
        # Use common function to prepare prompt with required placeholder validation
        task_prompt = bedrock.format_prompt(
            config["task_prompt"], 
            {
                "DOCUMENT_TEXT": text
            },
            required_placeholders=["DOCUMENT_TEXT"]
        )
        
        content = [{"text": task_prompt}]
        
        logger.info("Summarizing text with Bedrock")
        
        # Invoke Bedrock model
        try:
            response_with_metering = self._invoke_bedrock_model(
                content=content,
                config=config
            )
            
            response = response_with_metering["response"]
            metering = response_with_metering["metering"]
            
            # Extract summarization result
            summary_text = response['output']['message']['content'][0].get("text", "")
            
            # Try to extract JSON from the response
            try:
                summary_json = self._extract_json(summary_text)
                summary_data = json.loads(summary_json)
                
                # Create summary with whatever fields were returned
                return DocumentSummary(
                    content=summary_data,
                    metadata={"metering": metering}
                )
                
            except Exception as e:
                logger.warning(f"Failed to parse JSON from response: {e}")
                # Fallback to using the raw text as a single content field
                error_content = {
                    "error": "Summary parsing failed",
                    "content": summary_text[:1000] + ("..." if len(summary_text) > 1000 else "")
                }
                
                return DocumentSummary(
                    content=error_content,
                    metadata={"error": str(e), "metering": metering}
                )
                
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return self._create_error_summary(str(e))

    def process_document(self, document: Document, store_results: bool = True) -> Document:
        """
        Summarize a document and update the Document object with the summary.
        
        Args:
            document: Document object to summarize
            store_results: Whether to store results in S3 (default: True)
            
        Returns:
            Document: Updated Document object with summary and summarization_result
        """
        if not document.pages:
            logger.warning("Document has no pages to summarize")
            return self._update_document_status(
                document, 
                success=False, 
                error_message="Document has no pages to summarize"
            )
        
        try:
            # Start timing
            start_time = time.time()
            
            # Combine text from all pages
            all_text = ""
            for page_id, page in sorted(document.pages.items()):
                if page.parsed_text_uri:
                    try:
                        page_text = s3.get_text_content(page.parsed_text_uri)
                        all_text += f"<page-number>{page_id}</page-number>\n{page_text}\n\n"
                    except Exception as e:
                        logger.warning(f"Failed to load text content from {page.parsed_text_uri}: {e}")
                        # Continue with other pages
            
            if not all_text:
                logger.warning("No text content found in document pages")
                return self._update_document_status(
                    document, 
                    success=False, 
                    error_message="No text content found in document pages"
                )
            
            # Generate summary
            summary = self.process_text(all_text)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create summarization result object
            summarization_result = DocumentSummarizationResult(
                document_id=document.id,
                summary=summary,
                execution_time=execution_time
            )
            
            # Attach summarization result to document for immediate use
            document.summarization_result = summarization_result
            
            # Store results if requested
            if store_results:
                # Generate markdown report
                markdown_report = summarization_result.to_markdown()
                
                # Store report in S3
                output_bucket = document.output_bucket
                report_key = f"{document.input_key}/summary/summary.md"
                
                s3.write_content(
                    content=markdown_report,
                    bucket=output_bucket,
                    key=report_key,
                    content_type="text/markdown"
                )
                
                # Update document and summarization result with summary report URI
                document.summary_report_uri = f"s3://{output_bucket}/{report_key}"
                summarization_result.output_uri = document.summary_report_uri
            
            # Update document metering
            if "metering" in summary.metadata:
                document.metering = utils.merge_metering_data(document.metering, summary.metadata["metering"])
            
            # Update document status
            document = self._update_document_status(document)
            
            if store_results:
                logger.info(f"Document summarized successfully. Summary report stored at: {document.summary_report_uri}")
            else:
                logger.info(f"Document summarized successfully. No summary report stored.")
            
        except Exception as e:
            error_msg = f"Error summarizing document: {str(e)}"
            logger.error(error_msg)
            document = self._update_document_status(document, success=False, error_message=error_msg)
        
        return document
    
    def _update_document_status(self, document: Document, success: bool = True, error_message: Optional[str] = None) -> Document:
        """
        Update document status based on processing results.
        
        Args:
            document: Document to update
            success: Whether processing was successful
            error_message: Optional error message to add
            
        Returns:
            Updated document with appropriate status
        """
        if error_message and error_message not in document.errors:
            document.errors.append(error_message)
            
        if not success:
            document.status = Status.FAILED
            if error_message:
                logger.error(error_message)
        else:
            # Set status to SUMMARIZED even with non-fatal errors
            document.status = Status.SUMMARIZED
            if document.errors:
                logger.warning(f"Document summarized with {len(document.errors)} errors")
                
        return document