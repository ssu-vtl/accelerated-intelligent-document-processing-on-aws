"""
Extraction service for documents using LLMs.

This module provides a service for extracting fields and values from documents
using LLMs, with support for text and image content.
"""

import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple, Union

from idp_common import bedrock, s3, image, utils
from idp_common.extraction.models import ExtractedAttribute, ExtractionResult, PageInfo

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting fields from documents using LLMs."""

    def __init__(
        self,
        region: str = None,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the extraction service.
        
        Args:
            region: AWS region for Bedrock
            config: Configuration dictionary
        """
        self.config = config or {}
        self.region = region or self.config.get("region") or os.environ.get("AWS_REGION")
        
        # Get model_id from config for logging
        model_id = self.config.get("model_id") or self.config.get("extraction", {}).get("model")
        logger.info(f"Initialized extraction service with model {model_id}")

    def _get_class_attributes(self, class_label: str) -> List[Dict[str, Any]]:
        """
        Get attributes for a specific document class from configuration.
        
        Args:
            class_label: The document class name
            
        Returns:
            List of attribute configurations
        """
        classes_config = self.config.get("classes", [])
        class_config = next(
            (class_obj for class_obj in classes_config 
             if class_obj.get('name', '').lower() == class_label.lower()), 
            None
        )
        return class_config.get('attributes', []) if class_config else []

    def _format_attribute_descriptions(self, attributes: List[Dict[str, Any]]) -> str:
        """
        Format attribute descriptions for the prompt.
        
        Args:
            attributes: List of attribute configurations
            
        Returns:
            Formatted attribute descriptions as a string
        """
        return '\n'.join([
            f"{attr.get('name', '')}  \t[ {attr.get('description', '')} ]" 
            for attr in attributes
        ])

    def extract_from_text_and_images(
        self,
        document_text: str,
        page_images: List[bytes],
        class_label: str,
        section_id: str = "1",
        output_bucket: Optional[str] = None,
        output_prefix: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extract fields from document text and images.
        
        Args:
            document_text: The document text content
            page_images: List of page images as bytes
            class_label: The document class label
            section_id: ID for the document section
            output_bucket: Optional S3 bucket to store results
            output_prefix: Optional S3 prefix for storing results
            
        Returns:
            ExtractionResult containing the extracted fields
        """
        # Get extraction configuration
        extraction_config = self.config.get("extraction", {})
        model_id = self.config.get("model_id") or extraction_config.get("model")
        temperature = float(extraction_config.get("temperature", 0))
        top_k = float(extraction_config.get("top_k", 0.5))
        system_prompt = extraction_config.get("system_prompt", "")
        
        # Get attributes for this document class
        attributes = self._get_class_attributes(class_label)
        attribute_descriptions = self._format_attribute_descriptions(attributes)
        
        # Prepare prompt
        prompt_template = extraction_config.get("task_prompt", "")
        if "{DOCUMENT_TEXT}" in prompt_template and "{ATTRIBUTE_NAMES_AND_DESCRIPTIONS}" in prompt_template and "{DOCUMENT_CLASS}" in prompt_template:
            prompt_template = (
                prompt_template
                .replace("{DOCUMENT_TEXT}", "%(DOCUMENT_TEXT)s")
                .replace("{DOCUMENT_CLASS}", "%(DOCUMENT_CLASS)s")
                .replace("{ATTRIBUTE_NAMES_AND_DESCRIPTIONS}", "%(ATTRIBUTE_NAMES_AND_DESCRIPTIONS)s")
            )
            task_prompt = prompt_template % {
                "DOCUMENT_TEXT": document_text,
                "DOCUMENT_CLASS": class_label,
                "ATTRIBUTE_NAMES_AND_DESCRIPTIONS": attribute_descriptions
            }
        else:
            # Default prompt if template not found
            task_prompt = f"""
            Extract the following fields from this {class_label} document:
            
            {attribute_descriptions}
            
            Document text:
            {document_text}
            
            Respond with a JSON object containing each field name and its extracted value.
            """
        
        content = [{"text": task_prompt}]
        
        # Add image attachments to the content (limit to 20 images as per Bedrock constraints)
        if page_images:
            logger.info(f"Attaching images to prompt, for {len(page_images)} pages.")
            # Limit to 20 images as per Bedrock constraints
            for img in page_images[:20]:
                content.append(image.prepare_bedrock_image_attachment(img))
        
        logger.info(f"Extracting fields for {class_label} document, section {section_id}")
        
        # Time the model invocation
        request_start_time = time.time()
        
        # Invoke Bedrock with the common library
        response_with_metering = bedrock.invoke_model(
            model_id=model_id,
            system_prompt=system_prompt,
            content=content,
            temperature=temperature,
            top_k=top_k
        )
        
        total_duration = time.time() - request_start_time
        logger.info(f"Time taken for extraction: {total_duration:.2f} seconds")
        
        # Extract text from response
        extracted_text = bedrock.extract_text_from_response(response_with_metering)
        metering = response_with_metering.get("metering", {})
        
        # Parse response into JSON
        extracted_fields = {}
        output_uri = None
        output_key = None
        parsing_succeeded = True  # Flag to track if parsing was successful
        
        # Define output key if we have bucket and prefix
        if output_bucket and output_prefix:
            output_key = f"{output_prefix}/sections/{section_id}/result.json"
            
        try:
            # Try to parse the extracted text as JSON
            extracted_fields = json.loads(self._extract_json(extracted_text))
        except Exception as e:
            # Handle parsing error
            logger.error(f"Error parsing LLM output - invalid JSON?: {extracted_text} - {e}")
            logger.info(f"Using unparsed LLM output.")
            extracted_fields = {"raw_output": extracted_text}
            parsing_succeeded = False  # Mark that parsing failed
        
        # Write to S3 regardless of whether JSON parsing succeeded or failed
        if output_bucket and output_prefix and output_key:
            output = {
                "document_class": {
                    "type": class_label
                },
                "inference_result": extracted_fields
            }
            s3.write_content(output, output_bucket, output_key, content_type='application/json')
            output_uri = f"s3://{output_bucket}/{output_key}"
        
        # Create extraction attributes from the parsed fields
        attributes_list = []
        for name, value in extracted_fields.items():
            # Use confidence 0.0 for results from failed parsing, 1.0 for successful parsing
            confidence = 1.0 if parsing_succeeded else 0.0
            attributes_list.append(ExtractedAttribute(
                name=name,
                value=value,
                confidence=confidence
            ))
        
        # Create and return result
        metadata = {
            "parsing_succeeded": parsing_succeeded,
            "extraction_time_seconds": total_duration
        }
        
        return ExtractionResult(
            section_id=section_id,
            document_class=class_label,
            attributes=attributes_list,
            raw_response=extracted_text,
            metering=metering,
            output_uri=output_uri,
            metadata=metadata
        )

    def extract_from_section(
        self,
        section: Dict[str, Any],
        metadata: Dict[str, Any],
        output_bucket: str
    ) -> ExtractionResult:
        """
        Extract fields from a document section (using information from classification).
        
        Args:
            section: Dictionary containing section information
            metadata: Document metadata
            output_bucket: S3 bucket to store results
            
        Returns:
            ExtractionResult: The extraction result
        """
        section_id = section.get("id", "1")
        class_label = section.get("class", "")
        pages = section.get("pages", [])
        object_key = metadata.get("object_key", "")
        output_prefix = object_key
        
        # Sort pages by page number
        sorted_page_ids = sorted([page['page_id'] for page in pages], key=int)
        start_page = int(sorted_page_ids[0])
        end_page = int(sorted_page_ids[-1])
        logger.info(f"Processing {len(sorted_page_ids)} pages from {object_key}, class {class_label}: {start_page}-{end_page}")
        
        # Read document text from all pages in order
        t0 = time.time()
        document_texts = []
        for page in sorted(pages, key=lambda x: int(x['page_id'])):
            text_path = page['parsedTextUri']
            page_text = s3.get_text_content(text_path)
            document_texts.append(page_text)
        
        document_text = '\n'.join(document_texts)
        t1 = time.time()
        logger.info(f"Time taken to read text content: {t1-t0:.2f} seconds")
        
        # Read page images
        page_images = []
        for page in sorted(pages, key=lambda x: int(x['page_id'])):
            image_uri = page['imageUri']
            image_content = image.prepare_image(image_uri)
            page_images.append(image_content)
        
        t2 = time.time()
        logger.info(f"Time taken to read images: {t2-t1:.2f} seconds")
        
        # Extract fields
        result = self.extract_from_text_and_images(
            document_text=document_text,
            page_images=page_images,
            class_label=class_label,
            section_id=section_id,
            output_bucket=output_bucket,
            output_prefix=output_prefix
        )
        
        t3 = time.time()
        logger.info(f"Time taken for extraction: {t3-t2:.2f} seconds")
        
        return result

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON string from text response.
        
        Args:
            text: The text response from the model
            
        Returns:
            Extracted JSON string
        """
        # Check for code block format
        if "```json" in text:
            start_idx = text.find("```json") + len("```json")
            end_idx = text.find("```", start_idx)
            if end_idx > start_idx:
                return text[start_idx:end_idx].strip()
        elif "```" in text:
            start_idx = text.find("```") + len("```")
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