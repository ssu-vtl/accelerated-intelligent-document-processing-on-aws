"""
Summarization service for documents using LLMs.

This module provides a service for summarizing documents using various backends:
1. Bedrock LLMs with text support
"""

import json
import logging
import os
import boto3
from typing import List, Dict, Any, Optional, Union

from idp_common import bedrock, s3, utils
from idp_common.summarization.models import DocumentSummary
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

    def _get_summarization_config(self, style: str = None) -> Dict[str, Any]:
        """
        Get and validate the summarization configuration.
        
        Args:
            style: Optional summarization style to use
            
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
        
        # Get default style if none specified
        if not style:
            style = summarization_config.get("default_style", "default")
        
        # Get style configuration
        styles = summarization_config.get("summarization_styles", {})
        if style not in styles:
            logger.warning(f"Summarization style '{style}' not found, using 'default' instead")
            style = "default"
            
        style_config = styles.get(style, {})
        
        # Get style parameters
        max_length = style_config.get("max_length", 1000)
        style_instructions = style_config.get("style_instructions", "")
        
        # Validate system prompt
        system_prompt = summarization_config.get("system_prompt")
        if not system_prompt:
            raise ValueError("No system_prompt found in summarization configuration")
        
        # Replace placeholders in system prompt
        system_prompt = system_prompt.replace("{STYLE_INSTRUCTIONS}", style_instructions)
        config["system_prompt"] = system_prompt
        
        # Validate task prompt
        task_prompt = summarization_config.get("task_prompt")
        if not task_prompt:
            raise ValueError("No task_prompt found in summarization configuration")
        
        # Replace max_length placeholder in task prompt
        task_prompt = task_prompt.replace("{MAX_LENGTH}", str(max_length))
        config["task_prompt"] = task_prompt
        
        # Add style to config for metadata
        config["style"] = style
        
        return config

    def _prepare_prompt_from_template(self, prompt_template: str, substitutions: Dict[str, str], required_placeholders: List[str] = None) -> str:
        """
        Prepare prompt from template by replacing placeholders with values.
        
        Args:
            prompt_template: The prompt template with placeholders
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
        
        # Check if template uses {PLACEHOLDER} format and convert to %(PLACEHOLDER)s if needed
        if any(f"{{{key}}}" in prompt_template for key in substitutions):
            for key in substitutions:
                placeholder = f"{{{key}}}"
                if placeholder in prompt_template:
                    prompt_template = prompt_template.replace(placeholder, f"%({key})s")
                    
        # Apply substitutions using % operator
        return prompt_template % substitutions

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

    def summarize_text(self, text: str, style: str = None) -> DocumentSummary:
        """
        Summarize text content using the configured backend.
        
        Args:
            text: Text content to summarize
            style: Optional summarization style to use (default, concise, detailed, executive, technical)
            
        Returns:
            DocumentSummary: Summary of the text content
        """
        if not text:
            logger.warning("Empty text provided for summarization")
            return DocumentSummary(
                brief_summary="No content to summarize",
                detailed_summary="",
                metadata={"error": "Empty text provided"}
            )
        
        # Get summarization configuration with optional style
        config = self._get_summarization_config(style)
        
        # Use common function to prepare prompt with required placeholder validation
        task_prompt = self._prepare_prompt_from_template(
            config["task_prompt"], 
            {
                "DOCUMENT_TEXT": text
            },
            required_placeholders=["DOCUMENT_TEXT"]
        )
        
        content = [{"text": task_prompt}]
        
        logger.info(f"Summarizing text with Bedrock using style: {config['style']}")
        
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
                
                # Create and return summary result
                summary = DocumentSummary(
                    brief_summary=summary_data.get("brief_summary", ""),
                    detailed_summary=summary_data.get("detailed_summary", "")
                )
                summary.metadata = {"metering": metering, "style": config['style']}
                return summary
            except Exception as e:
                logger.warning(f"Failed to parse JSON from response: {e}")
                # Fallback to using the raw text
                summary = DocumentSummary(
                    brief_summary="Summary parsing failed",
                    detailed_summary=summary_text[:1000] + ("..." if len(summary_text) > 1000 else "")
                )
                summary.metadata = {"error": str(e), "metering": metering}
                return summary
                
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            # Return error result
            summary = DocumentSummary(
                brief_summary="Error generating summary",
                detailed_summary=""
            )
            summary.metadata = {"error": str(e)}
            return summary

    def summarize_document(self, document: Document, style: str = None) -> Document:
        """
        Summarize a document and update the Document object with the summary.
        
        Args:
            document: Document object to summarize
            style: Optional summarization style to use (default, concise, detailed, executive, technical)
            
        Returns:
            Document: Updated Document object with summary
        """
        if not document.pages:
            logger.warning("Document has no pages to summarize")
            document.summary = "Document has no pages to summarize"
            return document
        
        try:
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
                document.summary = "No text content found in document pages"
                return document
            
            # Generate summary with specified style
            summary = self.summarize_text(all_text, style)
            
            # Update document with summary
            document.summary = summary.brief_summary
            document.detailed_summary = summary.detailed_summary
            
            # Store style in metadata if available
            if hasattr(document, 'metadata') and isinstance(document.metadata, dict):
                document.metadata["summarization_style"] = summary.metadata.get("style", "default")
            
            # Update document metering
            if "metering" in summary.metadata:
                document.metering = utils.merge_metering_data(document.metering, summary.metadata["metering"])
            
            logger.info(f"Document summarized successfully using style: {summary.metadata.get('style', 'default')}")
            
        except Exception as e:
            error_msg = f"Error summarizing document: {str(e)}"
            logger.error(error_msg)
            document.errors.append(error_msg)
            document.summary = "Error generating summary"
        
        return document
        
    def get_available_styles(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available summarization styles from configuration.
        
        Returns:
            Dict of available summarization styles with their descriptions
        """
        summarization_config = self.config.get("summarization", {})
        styles = summarization_config.get("summarization_styles", {})
        
        # Create a simplified version with just the descriptions and max_length
        result = {}
        for style_name, style_config in styles.items():
            result[style_name] = {
                "description": style_config.get("description", ""),
                "max_length": style_config.get("max_length", 0)
            }
            
        return result
