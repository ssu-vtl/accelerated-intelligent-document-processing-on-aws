"""
Classification service for documents using LLMs.

This module provides a service for classifying documents using LLMs,
with support for text and image content.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from idp_common import bedrock, s3, utils
from idp_common.classification.models import (
    DocumentClassification,
    DocumentType,
    PageClassification,
    DocumentSection,
    ClassificationResult
)

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for classifying documents using LLMs."""

    def __init__(
        self,
        region: str = None,
        max_workers: int = 20,
        config: Dict[str, Any] = None
    ):
        """
        Initialize the classification service.
        
        Args:
            region: AWS region for Bedrock
            max_workers: Maximum number of concurrent workers
            config: Configuration dictionary
        """
        self.config = config or {}
        self.region = region or self.config.get("region") or os.environ.get("AWS_REGION")
        self.max_workers = max_workers
        self.document_types = self._load_document_types()
        
        # Get model_id from config for logging
        model_id = self.config.get("model_id") or self.config.get("classification", {}).get("model")
        logger.info(f"Initialized classification service with model {model_id}")

    def _load_document_types(self) -> List[DocumentType]:
        """Load document types from configuration."""
        doc_types = []
        
        # Get document types from config
        classes = self.config.get("classes", [])
        for class_obj in classes:
            doc_types.append(DocumentType(
                type_name=class_obj.get("name", ""),
                description=class_obj.get("description", "")
            ))
        
        if not doc_types:
            # Add a default type if none are defined
            doc_types.append(DocumentType(
                type_name="unclassified",
                description="A document that does not match any known type."
            ))
        
        return doc_types

    def _format_document_types(self) -> str:
        """Format document types for the prompt."""
        return "\n".join([
            f"{doc_type.type_name}  \t[ {doc_type.description} ]" 
            for doc_type in self.document_types
        ])

    def classify_page(
        self,
        page_id: str,
        text_content: str = None,
        image_content: Optional[bytes] = None,
        text_uri: Optional[str] = None,
        image_uri: Optional[str] = None,
        raw_text_uri: Optional[str] = None
    ) -> PageClassification:
        """
        Classify a single page based on its text and/or image content.
        
        Args:
            page_id: ID of the page
            text_content: Text content of the page
            image_content: Image content as bytes
            text_uri: URI of the text content
            image_uri: URI of the image content
            raw_text_uri: URI of the raw text content
            
        Returns:
            PageClassification: Classification result for the page
        """
        # Load text content from URI if not provided
        if text_content is None and text_uri:
            text_content = s3.get_text_content(text_uri)
        
        # Load image content from URI if not provided
        if image_content is None and image_uri:
            image_content = s3.get_binary_content(image_uri)
        
        # Get classification configuration
        classification_config = self.config.get("classification", {})
        model_id = self.config.get("model_id") or classification_config.get("model")
        temperature = float(classification_config.get("temperature", 0))
        top_k = float(classification_config.get("top_k", 0.5))
        system_prompt = classification_config.get("system_prompt", "")
        
        # Prepare prompt
        prompt_template = classification_config.get("task_prompt", "")
        if "{DOCUMENT_TEXT}" in prompt_template and "{CLASS_NAMES_AND_DESCRIPTIONS}" in prompt_template:
            prompt_template = prompt_template.replace("{DOCUMENT_TEXT}", "%(DOCUMENT_TEXT)s").replace("{CLASS_NAMES_AND_DESCRIPTIONS}", "%(CLASS_NAMES_AND_DESCRIPTIONS)s")
            task_prompt = prompt_template % {
                "CLASS_NAMES_AND_DESCRIPTIONS": self._format_document_types(),
                "DOCUMENT_TEXT": text_content or ""
            }
        else:
            # Default prompt if template not found
            task_prompt = f"""
            Classify the following document into one of these types:
            
            {self._format_document_types()}
            
            Document text:
            {text_content or ""}
            
            Respond with a JSON object with a single field "class" containing the document type.
            """
        
        content = [{"text": task_prompt}]
        
        # Add image if available
        if image_content:
            from idp_common import image
            content.append(image.prepare_bedrock_image_attachment(image_content))
        
        logger.info(f"Classifying page {page_id}")
        
        t0 = time.time()
        
        # Invoke Bedrock with the common library
        response_with_metering = bedrock.invoke_model(
            model_id=model_id,
            system_prompt=system_prompt,
            content=content,
            temperature=temperature,
            top_k=top_k
        )
        
        t1 = time.time()
        logger.info(f"Time taken for classification of page {page_id}: {t1-t0:.2f} seconds")
        
        response = response_with_metering["response"]
        metering = response_with_metering["metering"]
        
        # Extract classification result
        classification_text = response['output']['message']['content'][0].get("text", "")
        
        # Try to extract JSON from the response
        try:
            classification_json = self._extract_json(classification_text)
            classification_data = json.loads(classification_json)
            doc_type = classification_data.get("class", "")
        except Exception as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
            # Try to extract classification directly from text
            doc_type = self._extract_class_from_text(classification_text)
        
        if not doc_type:
            doc_type = "unclassified"
        
        logger.info(f"Page {page_id} classified as {doc_type}")
        
        # Create and return classification result
        return PageClassification(
            page_id=page_id,
            classification=DocumentClassification(
                doc_type=doc_type,
                confidence=1.0,  # Default confidence
                metadata={"metering": metering}
            ),
            image_uri=image_uri,
            text_uri=text_uri,
            raw_text_uri=raw_text_uri
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

    def _extract_class_from_text(self, text: str) -> str:
        """Extract class name from text if JSON parsing fails."""
        # Check for common patterns
        patterns = [
            "class: ", 
            "document type: ", 
            "document class: ", 
            "classification: ",
            "type: "
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            if pattern in text_lower:
                start_idx = text_lower.find(pattern) + len(pattern)
                end_idx = text_lower.find("\n", start_idx)
                if end_idx == -1:
                    end_idx = len(text_lower)
                
                return text[start_idx:end_idx].strip().strip('"\'')
        
        return ""

    def classify_pages(self, pages: Dict[str, Dict[str, Any]]) -> ClassificationResult:
        """
        Classify multiple pages concurrently.
        
        Args:
            pages: Dictionary of pages with their data
            
        Returns:
            ClassificationResult: Result with classified pages grouped into sections
        """
        all_results = []
        futures = []
        metering = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for page_num, page_data in pages.items():
                future = executor.submit(
                    self.classify_page,
                    page_id=page_num,
                    text_uri=page_data.get('parsedTextUri'),
                    image_uri=page_data.get('imageUri'),
                    raw_text_uri=page_data.get('rawTextUri')
                )
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    page_result = future.result()
                    page_metering = page_result.classification.metadata.get("metering", {})
                    all_results.append(page_result)
                    
                    # Merge metering data
                    metering = utils.merge_metering_data(metering, page_metering)
                except Exception as e:
                    logger.error(f"Error in concurrent classification: {str(e)}")
                    raise
        
        # Group pages into sections
        sections = self._group_consecutive_pages(all_results)
        
        # Create and return classification result
        return ClassificationResult(
            metadata={"metering": metering},
            sections=sections
        )

    def _group_consecutive_pages(self, results: List[PageClassification]) -> List[DocumentSection]:
        """
        Group consecutive pages with the same classification into sections.
        
        Args:
            results: List of page classification results
            
        Returns:
            List of document sections
        """
        sorted_results = sorted(results, key=lambda x: int(x.page_id))
        sections = []
        
        if not sorted_results:
            return sections
        
        current_group = 1
        current_type = sorted_results[0].classification.doc_type
        current_pages = [sorted_results[0]]
        
        for result in sorted_results[1:]:
            if result.classification.doc_type == current_type:
                current_pages.append(result)
            else:
                sections.append(DocumentSection(
                    section_id=str(current_group),
                    classification=DocumentClassification(
                        doc_type=current_type,
                        confidence=1.0  # Default confidence
                    ),
                    pages=current_pages
                ))
                current_group += 1
                current_type = result.classification.doc_type
                current_pages = [result]
        
        # Add the last section
        sections.append(DocumentSection(
            section_id=str(current_group),
            classification=DocumentClassification(
                doc_type=current_type,
                confidence=1.0  # Default confidence
            ),
            pages=current_pages
        ))
        
        return sections